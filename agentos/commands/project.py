from __future__ import annotations

import json
import os
import shutil
import tempfile
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from agentos.terminal.paths import StateError, agentos_home, atomic_write_json
from agentos.terminal.skills import global_skills_dir, skill_digest
from agentos.terminal import base_resources
from agentos.terminal.catalog import load_available_optional_skills, validate_selection, parse_skills_input

app = typer.Typer(help="Reflect AgentOS global resources into a project", add_completion=False)
skills_app = typer.Typer(help="Manage project skills", add_completion=False)
app.add_typer(skills_app, name="skills")

PROJECT_SCHEMA = "agentos.project/v1"
MANAGED = "agentos-project"
PROJECT_DOCUMENT_FILES = (
    "00-project-index.md",
    "01-project-charter.md",
    "02-product-scope-and-requirements.md",
    "03-system-contract.md",
    "04-safety-risk-verification.md",
    "05-agent-operating-contract.md",
    "06-decisions-progress-change-log.md",
    "reference/README.md",
    "reference/implementation/README.md",
    "reference/decisions/README.md",
    "reference/operations/README.md",
)


def _source_checkout_root() -> Path | None:
    return base_resources._source_checkout_root()


def _packaged_harness_root() -> Path | None:
    return base_resources._packaged_harness_root()


def _harness_sources() -> tuple[Path, Path] | None:
    root = _source_checkout_root()
    if root is not None:
        candidates = (root / ".agents" / "agents" / "harness", root / ".agents" / "skills" / "harness")
    else:
        packaged = _packaged_harness_root()
        if packaged is None:
            return None
        candidates = (packaged / "agents" / "harness", packaged / "skills" / "harness")
    if not all(path.is_dir() for path in candidates):
        return None
    return candidates


def _project_template_root() -> Path | None:
    root = _source_checkout_root()
    if root is not None:
        candidate = root / "docs" / "project" / "template"
    else:
        packaged = _packaged_harness_root()
        candidate = None
        if packaged is not None:
            candidates = (packaged / "_project_docs" / "template", packaged.parent / "_project_docs" / "template")
            candidate = next((item for item in candidates if item.is_dir()), None)
    return candidate if candidate is not None and candidate.is_dir() else None


def _project_documents_payload(root: Path) -> dict:
    target = root / ".agentos" / "project"
    if not target.exists():
        return {"state": "not_initialized", "missing": list(PROJECT_DOCUMENT_FILES)}
    if target.is_symlink() or not target.is_dir():
        return {"state": "invalid", "missing": list(PROJECT_DOCUMENT_FILES)}
    missing = [name for name in PROJECT_DOCUMENT_FILES if not (target / name).is_file()]
    return {"state": "current" if not missing else "partial", "missing": missing}


def _root(path: str | None) -> Path:
    candidate = Path(path).expanduser() if path else Path.cwd()
    if not candidate.exists() or not candidate.is_dir() or candidate.is_symlink():
        raise StateError("Project path must be an existing regular directory. Next: choose a project directory.")
    return candidate.resolve()


def _managed(root: Path) -> Path:
    meta = root / ".agentos"
    if meta.exists() and meta.is_symlink():
        raise StateError("Project .agentos directory must not be a symlink.")
    return meta / MANAGED


def _settings_digest() -> str:
    import hashlib
    path = agentos_home() / "config.toml"
    if not path.is_file() or path.is_symlink():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload(root: Path) -> dict:
    documents = _project_documents_payload(root)
    managed = _managed(root)
    manifest = managed / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        return {"state": "not_initialized", "project_documents": documents}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"state": "invalid", "project_documents": documents}
    if data.get("schema_version") != PROJECT_SCHEMA or not isinstance(data.get("skills"), dict) or not isinstance(data.get("agents", {}), dict):
        return {"state": "invalid", "project_documents": documents}
    skills_root = managed / "skills"
    agents_root = managed / "agents"
    current = True
    for name, expected in data["skills"].items():
        try:
            if skill_digest(skills_root / name) != expected:
                return {"state": "invalid"}
            global_skill = global_skills_dir() / name
            if global_skill.is_dir() and skill_digest(global_skill) != expected:
                current = False
        except StateError:
            return {"state": "invalid"}
    for name, expected in data.get("agents", {}).items():
        try:
            if skill_digest(agents_root / name) != expected:
                return {"state": "invalid"}
        except StateError:
            return {"state": "invalid"}
    state = "current" if current and data.get("settings_reference", {}).get("digest") == _settings_digest() else "stale_global_skills" if not current else "stale_global_settings"
    return {
        "state": state,
        "skills": sorted(data["skills"]),
        "agents": sorted(data.get("agents", {})),
        "optional_skills": data.get("optional_skills", []),
        "settings_activation": "project-local",
        "project_documents": documents,
    }


def _run_tty_selector(available: list, current_selection: list[str]) -> list[str]:
    console = Console()
    selection = set(current_selection)
    
    while True:
        console.print("\n[bold]AgentOS Optional Skills[/bold]")
        groups = {}
        for s in available:
            groups.setdefault(s.group_kr, []).append(s)
            
        idx = 1
        idx_to_skill = {}
        for group, items in groups.items():
            console.print(f"\n[cyan]{group}[/cyan]")
            for s in items:
                mark = "\\[x]" if s.name in selection else "\\[ ]"
                console.print(f"  {idx}. {mark} {s.name} - {s.summary}")
                idx_to_skill[str(idx)] = s.name
                idx += 1
                
        console.print("\nType a number to toggle, 'c' to confirm, or 'q' to cancel.")
        choice = Prompt.ask("Action").strip().lower()
        if choice == 'c':
            return list(selection)
        elif choice == 'q':
            console.print("Cancelled.")
            raise typer.Exit(2)
        elif choice in idx_to_skill:
            name = idx_to_skill[choice]
            if name in selection:
                selection.remove(name)
            else:
                selection.add(name)
        else:
            console.print("[red]Invalid choice[/red]")


def _sync_project_skills(root: Path, selected_optional: list[str]) -> None:
    managed = _managed(root)
    managed.parent.mkdir(exist_ok=True)
    
    manifest_path = managed / "manifest.json"
    prior_manifest = {}
    prior_optional = []
    if manifest_path.is_file() and not manifest_path.is_symlink():
        try:
            prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "optional_skills" in prior_manifest:
                prior_optional = prior_manifest["optional_skills"]
            else:
                # If no optional_skills field, assume all managed skills except harness are optional
                prior_optional = [k for k in prior_manifest.get("skills", {}) if k != "harness"]
        except Exception:
            pass

    project_agents = root / ".agents" / "agents"
    project_skills = root / ".agents" / "skills"
    
    for destination in (root / ".agents", project_agents, project_skills):
        if destination.exists() and (destination.is_symlink() or not destination.is_dir()):
            raise StateError(f"Managed project path is invalid: {destination}")

    stage = Path(tempfile.mkdtemp(prefix=f".{MANAGED}.stage-", dir=managed.parent))
    backup = managed.parent / f".{MANAGED}.backup"
    
    try:
        target_skills = stage / "skills"
        target_skills.mkdir()
        target_agents = stage / "agents"
        target_agents.mkdir()
        
        records = {}
        agent_records = {}

        # 1. Copy unmanaged existing things
        if project_agents.is_dir():
            for item in project_agents.iterdir():
                if item.name == "harness":
                    continue
                shutil.copytree(item, target_agents / item.name)
        
        if project_skills.is_dir():
            for item in project_skills.iterdir():
                if item.name == "harness" or item.name in prior_optional or item.name in selected_optional:
                    continue
                shutil.copytree(item, target_skills / item.name)

        # 2. Copy harness
        harness = _harness_sources()
        if harness is not None:
            source_agents, source_skills = harness
            shutil.copytree(source_agents, target_agents / "harness")
            shutil.copytree(source_skills, target_skills / "harness")
            agent_records["harness"] = skill_digest(target_agents / "harness")
            records["harness"] = skill_digest(target_skills / "harness")
            
        # 3. Copy selected optional skills
        for name in selected_optional:
            source = global_skills_dir() / name
            if not source.is_dir():
                raise StateError(f"Selected skill '{name}' is not installed globally.")
            dest = target_skills / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
            digest = skill_digest(source)
            if skill_digest(dest) != digest:
                raise StateError("Project skill staging validation failed.")
            records[name] = digest

        atomic_write_json(stage / "manifest.json", {
            "schema_version": PROJECT_SCHEMA,
            "skills": records,
            "agents": agent_records,
            "optional_skills": selected_optional,
            "settings_reference": {"digest": _settings_digest(), "activation": "project-local"}
        })

        if backup.exists():
            shutil.rmtree(backup)
            
        for source_dir, destination in ((target_skills, project_skills), (target_agents, project_agents)):
            backup_runtime = destination.parent / f".{destination.name}.agentos-backup"
            runtime_stage = destination.parent / f".{destination.name}.agentos-stage"
            
            if backup_runtime.exists():
                shutil.rmtree(backup_runtime)
            if runtime_stage.exists():
                shutil.rmtree(runtime_stage)
            if destination.exists():
                os.replace(destination, backup_runtime)
            try:
                shutil.copytree(source_dir, runtime_stage)
                os.replace(runtime_stage, destination)
            except OSError:
                if backup_runtime.exists() and not destination.exists():
                    os.replace(backup_runtime, destination)
                raise
            finally:
                if runtime_stage.exists():
                    shutil.rmtree(runtime_stage)
            if backup_runtime.exists():
                shutil.rmtree(backup_runtime)
                
        if managed.exists():
            if managed.is_symlink() or not (managed / "manifest.json").is_file():
                raise StateError("Managed project state is invalid. Next: remove only .agentos/agentos-project after inspection.")
            os.replace(managed, backup)
        try:
            os.replace(stage, managed)
        except OSError:
            if backup.exists() and not managed.exists():
                os.replace(backup, managed)
            raise
        if backup.exists():
            shutil.rmtree(backup)
            
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _bootstrap_docs(root: Path) -> None:
    documents_target = root / ".agentos" / "project"
    documents_template = _project_template_root()
    if not documents_target.exists() and documents_template is None:
        raise StateError("Project document template is unavailable. Next: reinstall AgentOS")
        
    if documents_template is not None:
        if not documents_target.exists():
            documents_stage = Path(tempfile.mkdtemp(prefix=".project-documents.stage-", dir=documents_target.parent))
            try:
                shutil.copytree(documents_template, documents_stage / "project")
                os.replace(documents_stage / "project", documents_target)
            finally:
                if documents_stage.exists():
                    shutil.rmtree(documents_stage)
        else:
            # no-overwrite partial copy
            for name in PROJECT_DOCUMENT_FILES:
                src = documents_template / name
                dst = documents_target / name
                if src.is_file() and not dst.is_file():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)


def _do_init_or_select(path: str | None, skills_input: str | None, json_output: bool) -> dict:
    root = _root(path)
    available = load_available_optional_skills()
    
    managed = _managed(root)
    manifest_path = managed / "manifest.json"
    
    current_selection = []
    if manifest_path.is_file():
        try:
            prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "optional_skills" in prior_manifest:
                current_selection = prior_manifest["optional_skills"]
            else:
                current_selection = [k for k in prior_manifest.get("skills", {}) if k != "harness"]
        except Exception:
            pass
            
    parsed = parse_skills_input(skills_input)
    if parsed is not None:
        selected = validate_selection(parsed, available)
    else:
        if sys.stdout.isatty():
            selected = _run_tty_selector(available, current_selection)
        else:
            selected = current_selection

    _sync_project_skills(root, selected)
    _bootstrap_docs(root)
    
    return _payload(root)


@app.command()
def init(
    path: str | None = typer.Option(None, "--path"), 
    json_output: bool = typer.Option(False, "--json"),
    skills: str | None = typer.Option(None, "--skills", help="Comma-separated skill names, or 'none' to skip optional skills")
) -> None:
    try:
        payload = _do_init_or_select(path, skills, json_output)
    except (StateError, OSError) as exc:
        typer.echo(json.dumps({"state": "invalid", "message": str(exc)}) if json_output else str(exc), err=True)
        raise typer.Exit(2)
    typer.echo(json.dumps(payload, sort_keys=True) if json_output else "Project resources initialized. Next: agentos project status")


@skills_app.command("select")
def select(
    path: str | None = typer.Option(None, "--path"), 
    json_output: bool = typer.Option(False, "--json"),
    skills: str | None = typer.Option(None, "--skills", help="Comma-separated skill names, or 'none' to skip optional skills")
) -> None:
    try:
        payload = _do_init_or_select(path, skills, json_output)
    except (StateError, OSError) as exc:
        typer.echo(json.dumps({"state": "invalid", "message": str(exc)}) if json_output else str(exc), err=True)
        raise typer.Exit(2)
    typer.echo(json.dumps(payload, sort_keys=True) if json_output else "Project skills updated. Next: agentos project status")


@app.command()
def status(path: str | None = typer.Option(None, "--path"), json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        payload = _payload(_root(path))
    except StateError as exc:
        payload = {"state": "invalid", "message": str(exc)}
    typer.echo(json.dumps(payload, sort_keys=True) if json_output else f"Project status: {payload['state']}")
