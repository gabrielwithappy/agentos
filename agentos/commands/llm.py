from __future__ import annotations

import json

import typer

from agentos.llm.redaction import sanitize
from agentos.llm.session import UnsupportedProviderError, get_provider, unsupported_provider_event

app = typer.Typer(help="Inspect LLM provider status")


def _emit_json(payload: dict) -> None:
    typer.echo(json.dumps(sanitize(payload), sort_keys=True))


def _unsupported_payload(provider: str) -> dict:
    return unsupported_provider_event(provider).to_dict()


def build_status_payload(provider: str) -> dict:
    try:
        return get_provider(provider).status().to_dict()
    except UnsupportedProviderError:
        return _unsupported_payload(provider)


def build_login_payload(provider: str) -> dict:
    try:
        payload = get_provider(provider).login().to_dict()
    except UnsupportedProviderError:
        return _unsupported_payload(provider)
    payload["action"] = "login"
    return payload


def iter_login_updates(provider: str):
    try:
        provider_impl = get_provider(provider)
    except UnsupportedProviderError:
        yield {"type": "result", "payload": _unsupported_payload(provider)}
        return

    login_updates = getattr(provider_impl, "login_updates", None)
    if callable(login_updates):
        yield from login_updates()
        return

    yield {"type": "result", "payload": build_login_payload(provider)}


def build_logout_payload(provider: str) -> dict:
    try:
        payload = get_provider(provider).logout().to_dict()
    except UnsupportedProviderError:
        return _unsupported_payload(provider)
    payload["action"] = "logout"
    return payload


def _emit_payload(payload: dict, json_output: bool) -> None:
    if payload.get("error"):
        if json_output:
            _emit_json(payload)
        else:
            error = payload["error"]
            typer.echo(f"{error['message']} {payload.get('recovery', '')}".strip(), err=True)
        raise typer.Exit(1)
    if json_output:
        _emit_json(payload)
        return
    typer.echo(payload["message"])


@app.command()
def status(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Show provider status."""
    _emit_payload(build_status_payload(provider), json_output)


@app.command()
def login(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Run provider login."""
    _emit_payload(build_login_payload(provider), json_output)


@app.command()
def logout(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Run provider logout."""
    _emit_payload(build_logout_payload(provider), json_output)
