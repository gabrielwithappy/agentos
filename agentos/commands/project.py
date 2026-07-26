from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import typer

from agentos.terminal.paths import StateError, agentos_home, atomic_write_json
from agentos.terminal.skills import global_skills_dir, skill_digest

app = typer.Typer(help="Reflect AgentOS global resources into a project", add_completion=False)
PROJECT_SCHEMA = "agentos.project/v1"
MANAGED = "agentos-project"


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
    managed = _managed(root)
    manifest = managed / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        return {"state": "not_initialized"}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"state": "invalid"}
    if data.get("schema_version") != PROJECT_SCHEMA or not isinstance(data.get("skills"), dict):
        return {"state": "invalid"}
    skills_root = managed / "skills"
    current = True
    for name, expected in data["skills"].items():
        try:
            if skill_digest(skills_root / name) != expected:
                return {"state": "invalid"}
            if skill_digest(global_skills_dir() / name) != expected:
                current = False
        except StateError:
            return {"state": "invalid"}
    state = "current" if current and data.get("settings_reference", {}).get("digest") == _settings_digest() else "stale_global_skills" if not current else "stale_global_settings"
    return {"state": state, "skills": sorted(data["skills"]), "settings_activation": "global-only"}


@app.command()
def init(path: str | None = typer.Option(None, "--path"), json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        root = _root(path)
        skills = [entry for entry in global_skills_dir().iterdir() if entry.is_dir() and not entry.is_symlink() and (entry / "SKILL.md").is_file()]
        if not skills:
            raise StateError("No skills installed. Next: agentos skill install <SKILL_DIRECTORY>")
        managed = _managed(root)
        managed.parent.mkdir(exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{MANAGED}.stage-", dir=managed.parent))
        backup = managed.parent / f".{MANAGED}.backup"
        try:
            target_skills = stage / "skills"
            target_skills.mkdir()
            records = {}
            for source in skills:
                digest = skill_digest(source)
                shutil.copytree(source, target_skills / source.name)
                if skill_digest(target_skills / source.name) != digest:
                    raise StateError("Project skill staging validation failed.")
                records[source.name] = digest
            atomic_write_json(stage / "manifest.json", {"schema_version": PROJECT_SCHEMA, "skills": records, "settings_reference": {"digest": _settings_digest(), "activation": "global-only"}})
            if backup.exists():
                shutil.rmtree(backup)
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
        payload = _payload(root)
    except (StateError, OSError) as exc:
        typer.echo(json.dumps({"state": "invalid", "message": str(exc)}) if json_output else str(exc), err=True)
        raise typer.Exit(2)
    typer.echo(json.dumps(payload, sort_keys=True) if json_output else "Project resources initialized. Next: agentos project status")


@app.command()
def status(path: str | None = typer.Option(None, "--path"), json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        payload = _payload(_root(path))
    except StateError as exc:
        payload = {"state": "invalid", "message": str(exc)}
    typer.echo(json.dumps(payload, sort_keys=True) if json_output else f"Project status: {payload['state']}")
