from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from agentos.terminal import hooks
from agentos.llm.redaction import redact_text
from agentos.terminal.paths import StateError

app = typer.Typer(help="Manage declarative AgentOS hooks", add_completion=False)
config_app = typer.Typer(help="Inspect hook configuration", add_completion=False)
console = Console()


@app.command("list")
def list_() -> None:
    try:
        rows = hooks.effective_hooks()
    except StateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    table = Table("name", "phase", "order", "enabled", "critical", "timeout_ms")
    for spec in rows:
        table.add_row(spec.name, spec.phase, str(spec.order), str(spec.enabled), str(spec.critical), str(spec.timeout_ms))
    console.print(table)


@app.command()
def enable(name: str) -> None:
    try:
        hooks.set_hook_enabled(name, True)
    except StateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print(f"Enabled hook {name}.")


@app.command()
def disable(name: str) -> None:
    try:
        hooks.set_hook_enabled(name, False)
    except StateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print(f"Disabled hook {name}.")


@config_app.command("show")
def config_show() -> None:
    try:
        rows = hooks.effective_hooks()
    except StateError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    typer.echo('schema_version = "agentos.hooks/v1"')
    typer.echo("")
    typer.echo("[hooks]")
    for spec in rows:
        typer.echo("")
        typer.echo(f"[hooks.{spec.name}]")
        typer.echo(f"enabled = {str(spec.enabled).lower()}")
        typer.echo(f"order = {spec.order}")
        typer.echo(f"critical = {str(spec.critical).lower()}")
        typer.echo(f"timeout_ms = {spec.timeout_ms}")
        if spec.value not in (None, ""):
            typer.echo(f'value = "{redact_text(str(spec.value))}"')


app.add_typer(config_app, name="config")
