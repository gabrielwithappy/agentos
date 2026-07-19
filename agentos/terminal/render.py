from __future__ import annotations

import json
from typing import Any

import typer
from rich.console import Console

from agentos.llm.redaction import sanitize

console = Console()


def emit_jsonl(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(sanitize(payload), sort_keys=True))


def emit_error(message: str, *, exit_code: int, recovery: str | None = None) -> None:
    typer.echo(message, err=True)
    if recovery:
        typer.echo(recovery, err=True)
    raise typer.Exit(exit_code)


def render_llm_text(event: dict[str, Any]) -> None:
    if event.get("type") == "message_delta" and event.get("text"):
        console.print(event["text"])
    elif event.get("type") == "error":
        err = event.get("error") or {}
        typer.echo(err.get("message", "Provider error."), err=True)
        if event.get("recovery"):
            typer.echo(event["recovery"], err=True)
