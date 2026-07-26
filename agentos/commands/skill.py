from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentos.terminal.paths import StateError
from agentos.terminal.skills import global_skills_dir, install_skill, statuses

app = typer.Typer(help="Manage agent skills")
console = Console()


def get_skills_dir() -> Path:
    return global_skills_dir()


@app.command()
def list() -> None:
    skills_dir = get_skills_dir()
    console.print(f"[bold blue]Installed Skills (in {skills_dir}):[/bold blue]")
    if not skills_dir.is_dir():
        console.print("[yellow]Skills directory not found. Run 'agentos setup' first.[/yellow]")
        return
    names = [item.name for item in sorted(skills_dir.iterdir()) if item.is_dir() and not item.is_symlink() and (item / "SKILL.md").is_file()]
    if not names:
        console.print("[yellow]No skills installed.[/yellow]")
        return
    for name in names:
        console.print(f"- [bold green]{name}[/bold green]")


@app.command()
def install(path: str) -> None:
    try:
        name = install_skill(path)
    except StateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print(f"[bold green]✔ Successfully installed skill '{name}'[/bold green]")


@app.command()
def status(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        rows = statuses()
    except StateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    payload = [{"name": row.name, "state": row.state, "digest": row.digest, "source_digest": row.source_digest} for row in rows]
    if json_output:
        import json
        typer.echo(json.dumps(payload, sort_keys=True))
        return
    if not payload:
        typer.echo("No skills installed. Next: agentos skill install <SKILL_DIRECTORY>")
        return
    for row in payload:
        typer.echo(f"{row['name']}: {row['state']}")


@app.command(hidden=True)
def add(path: str) -> None:
    install(path)
