from __future__ import annotations

import json

import typer

from agentos.llm.redaction import sanitize
from agentos.llm.session import UnsupportedProviderError, get_provider, unsupported_provider_event

app = typer.Typer(help="Inspect LLM provider status")


def _emit_json(payload: dict) -> None:
    typer.echo(json.dumps(sanitize(payload), sort_keys=True))


def _handle_unsupported(provider: str, as_json: bool) -> None:
    event = unsupported_provider_event(provider).to_dict()
    if as_json:
        _emit_json(event)
    else:
        error = event["error"]
        typer.echo(f"{error['message']} {event['recovery']}", err=True)
    raise typer.Exit(1)


def _status_payload(action: str, provider: str) -> dict:
    try:
        status = get_provider(provider).status()
    except UnsupportedProviderError:
        _handle_unsupported(provider, True)
    payload = status.to_dict()
    payload["action"] = action
    return payload


@app.command()
def status(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Show provider status."""
    try:
        payload = get_provider(provider).status().to_dict()
    except UnsupportedProviderError:
        _handle_unsupported(provider, json_output)
    if json_output:
        _emit_json(payload)
        return
    typer.echo(payload["message"])


@app.command()
def login(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Run provider login."""
    try:
        payload = get_provider(provider).login().to_dict()
    except UnsupportedProviderError:
        _handle_unsupported(provider, json_output)
    payload["action"] = "login"
    if json_output:
        _emit_json(payload)
        return
    typer.echo(payload["message"])


@app.command()
def logout(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Run provider logout."""
    try:
        payload = get_provider(provider).logout().to_dict()
    except UnsupportedProviderError:
        _handle_unsupported(provider, json_output)
    payload["action"] = "logout"
    if json_output:
        _emit_json(payload)
        return
    typer.echo(payload["message"])
