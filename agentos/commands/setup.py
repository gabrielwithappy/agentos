import json
import subprocess
from pathlib import Path
import typer
from rich.console import Console

from agentos.terminal.paths import StateError, initialize_state
from agentos.terminal.skills import install_bundled_skills
from agentos.terminal.base_resources import install_harness_base
from agentos.commands.project import _root
from agentos.terminal.paths import atomic_write_text

app = typer.Typer(help="Initialize AgentOS environment")
console = Console()


CODEX_CONFIG = {
    "hooks": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "agentos hook bridge codex pre-bash"}]},
            {"matcher": "write_to_file|replace_file_content|multi_replace_file_content", "hooks": [{"type": "command", "command": "agentos hook bridge codex pre-write"}]},
        ],
    }
}
CLAUDE_CONFIG = {
    "hooks": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "agentos hook bridge claude-code pre-bash"}]},
            {"matcher": "Replace|Edit|Write.*", "hooks": [{"type": "command", "command": "agentos hook bridge claude-code pre-write"}]},
        ],
    }
}
AGENTS_TEMPLATE = "# AGENTS.md\n\nThis project is initialized for AgentOS. Run `agentos --help` for commands.\n"


def _source_checkout_root() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    if (root / "pyproject.toml").is_file() and not (root / "pyproject.toml").is_symlink() and (root / "scripts" / "install-hooks.sh").is_file() and not (root / "scripts" / "install-hooks.sh").is_symlink():
        return root
    return None


def _is_self_host_target(target: Path) -> bool:
    source = _source_checkout_root()
    return source is not None and target.resolve() == source.resolve()


def _regular_parent(root: Path, name: str) -> Path:
    path = root / name
    if path.exists():
        if path.is_symlink():
            raise StateError(f"unsupported symlink path={path}")
        if not path.is_dir():
            raise StateError(f"unsupported non-directory path={path}")
    return path


def _write_or_skip(path: Path, content: str, vendor: str | None, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        if path.is_symlink():
            raise StateError(f"unsupported symlink path={path}")
        if not path.is_file():
            raise StateError(f"unsupported non-regular-file path={path}")
        if vendor:
            console.print(f"SKIP existing file={path} vendor={vendor} reason=existing-config")
            skipped.append(vendor)
        else:
            console.print(f"SKIP existing file={path} reason=existing-agents-md")
        return
    atomic_write_text(path, content)
    if vendor:
        console.print(f"CREATED file={path} vendor={vendor}")
        created.append(vendor)
    else:
        console.print(f"CREATED file={path} purpose=agents-md")


def _validate_destination(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink():
        raise StateError(f"unsupported symlink path={path}")
    if not path.is_file():
        raise StateError(f"unsupported non-regular-file path={path}")


def _bootstrap_project(target: Path) -> None:
    _regular_parent(target, ".codex")
    _regular_parent(target, ".claude")
    for destination in (target / "AGENTS.md", target / ".codex" / "hooks.json", target / ".claude" / "settings.json"):
        _validate_destination(destination)
    created: list[str] = []
    skipped: list[str] = []
    agents_created = not (target / "AGENTS.md").exists()
    _write_or_skip(target / "AGENTS.md", AGENTS_TEMPLATE, None, created, skipped)
    _write_or_skip(target / ".codex" / "hooks.json", json.dumps(CODEX_CONFIG, indent=2) + "\n", "codex", created, skipped)
    _write_or_skip(target / ".claude" / "settings.json", json.dumps(CLAUDE_CONFIG, indent=2) + "\n", "claude-code", created, skipped)
    enabled = ",".join(created) or "none"
    preserved = ",".join(skipped) or "none"
    console.print(
        f"PASS agentos-setup destination={target} written={len(created) + int(agents_created)} "
        f"skipped={len(skipped)} enabled={enabled} skipped_vendors={preserved} deferred=gemini rerun_safe=true"
    )

@app.callback(invoke_without_command=True)
def main(
    home: str | None = typer.Option(None, "--home", help="Override AGENTOS_HOME."),
    path: str | None = typer.Option(None, "--path", help="Project directory to initialize; defaults to cwd."),
    refresh_bundled_skills: bool = typer.Option(False, "--refresh-bundled-skills", help="Replace preserved bundled skill names."),
):
    """Run the setup process for AgentOS."""
    console.print("[bold blue]Setting up AgentOS...[/bold blue]")
    try:
        dest = initialize_state(Path(home) if home else None)
        summary = install_bundled_skills(dest, refresh=refresh_bundled_skills)
        console.print(
            "기본 카탈로그 스킬: "
            f"설치 {summary.installed}, 최신 {summary.already_current}, 갱신 {summary.bundled_updated}, "
            f"보존 {summary.custom_preserved}, 갱신 가능 {summary.bundled_update_available}, 실패 {summary.failed}"
        )
        if summary.failed:
            raise StateError("Default skill installation failed. Next: agentos setup")
        base_manifest = install_harness_base(dest)
        console.print(
            f"공통 하네스 base: agents={len(base_manifest['agents'])}, skills={len(base_manifest['skills'])}, "
            f"schema={base_manifest['schema_version']}"
        )
            
        target = _root(path)
        if _is_self_host_target(target):
            hook_script = _source_checkout_root() / "scripts" / "install-hooks.sh"  # type: ignore[operator]
            console.print("[bold blue]Installing Unified Hooks for all CLIs...[/bold blue]")
            subprocess.run(["bash", str(hook_script)], cwd=target, check=False)
        else:
            _bootstrap_project(target)
        console.print("[bold green]Verification successful![/bold green] CLI state is ready.")
        if _is_self_host_target(target):
            console.print(f"[bold green]PASS[/bold green] agentos-setup destination={dest} selection=catalog-default-skills")
    except (StateError, OSError, ValueError) as e:
        message = str(e)
        if message.startswith("unsupported symlink path="):
            path_value = message.removeprefix("unsupported symlink path=")
            message = (
                f"{message}. No existing files were changed. Next: inspect with ls -ld {path_value}, "
                "replace it with a regular file or directory you own, then rerun agentos setup."
            )
        console.print(f"[bold red]Setup failed: {message}[/bold red]")
        raise typer.Exit(code=1)
