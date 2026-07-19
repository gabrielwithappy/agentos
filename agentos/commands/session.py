from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.table import Table

from agentos.terminal import sessions

app = typer.Typer(help="Manage AgentOS sessions", add_completion=False)
console = Console()


def _confirm(message: str, yes: bool) -> bool:
    if yes:
        return True
    if not sys.stdin.isatty():
        typer.echo("Confirmation requires a TTY. Next: rerun the same command with --yes.", err=True)
        raise typer.Exit(2)
    return typer.confirm(message, default=False)


@app.command("list")
def list_() -> None:
    rows = sessions.list_sessions()
    if not rows:
        console.print("No sessions found.")
        return
    table = Table("session_id", "provider", "mode", "updated_at", width=120)
    for row in rows:
        table.add_row(row["session_id"], row["provider"], row["mode"], row["updated_at"])
    console.print(table)


@app.command()
def show(session_id: str) -> None:
    try:
        meta, events = sessions.read_session(session_id)
    except sessions.SessionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print_json(data={"metadata": meta, "event_count": len(events)})


@app.command()
def resume(session_id: str) -> None:
    try:
        meta, _ = sessions.read_session(session_id)
    except sessions.SessionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print(f"Resume session {meta['session_id']} with provider {meta['provider']}.")


@app.command()
def delete(session_id: str, yes: bool = typer.Option(False, "--yes", help="Skip confirmation.")) -> None:
    try:
        sid = sessions.validate_session_id(session_id)
        console.print(f"Delete session {sid}")
        if not _confirm(f"Delete session {sid}?", yes):
            console.print("No changes made.")
            return
        sessions.delete_session(sid)
    except sessions.SessionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print(f"Deleted session {sid}.")


@app.command()
def prune(before: str = typer.Option(..., "--before"), yes: bool = typer.Option(False, "--yes")) -> None:
    try:
        rows = sessions.sessions_before(before)
        if not rows:
            console.print("No sessions matched; nothing deleted.")
            return
        console.print("Sessions to delete:")
        for sid in rows:
            console.print(sid)
        if not _confirm("Delete listed sessions?", yes):
            console.print("No changes made.")
            return
        sessions.prune_before(before)
    except (sessions.SessionError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    console.print(f"Deleted {len(rows)} sessions.")
