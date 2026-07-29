from __future__ import annotations

import inspect
import json
import sys
from collections.abc import Callable

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


def iter_login_updates(provider: str, *, manual_code_input: Callable[[], str | None] | None = None):
    """`manual_code_input`, if given, is only actually passed to providers
    whose `login_updates()` declares it (currently just `claude`, which has
    no device-code fallback) — checked via signature inspection *before*
    calling, so providers that don't accept it (mock, codex, codex-cli) run
    their normal, automatic-only flow unaffected, and a real `TypeError`
    from inside an accepting provider's flow can't be mistaken for a
    signature mismatch and trigger a second, side-effect-duplicating call."""
    try:
        provider_impl = get_provider(provider)
    except UnsupportedProviderError:
        yield {"type": "result", "payload": _unsupported_payload(provider)}
        return

    login_updates = getattr(provider_impl, "login_updates", None)
    if callable(login_updates):
        if manual_code_input is not None and "manual_code_input" in inspect.signature(login_updates).parameters:
            yield from login_updates(manual_code_input=manual_code_input)
        else:
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


def _prompt_for_manual_login_code() -> str | None:
    """Fallback for when the browser's automatic redirect doesn't complete
    (it can't always reach a locally-bound callback server, or the
    provider's approval page simply never navigates away). Only offered
    when stdin is a real TTY, so a non-interactive invocation (CI, piped
    input) never blocks on it."""
    try:
        return input("Or paste the authorization code / redirect URL here: ")
    except EOFError:
        return None


@app.command()
def login(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Run provider login.

    Streams hints (e.g. the browser sign-in URL, or the device-code
    verification URL/code if browser auto-launch fails) to stderr as they
    become known — a one-shot CLI invocation has no other way to show the
    user where to sign in before the flow completes.
    """
    manual_code_input = _prompt_for_manual_login_code if sys.stdin.isatty() else None
    payload: dict | None = None
    for update in iter_login_updates(provider, manual_code_input=manual_code_input):
        if update.get("type") == "hint":
            typer.echo(str(update.get("text", "")), err=True)
            continue
        payload = dict(update.get("payload", {}))
    if payload is None:
        payload = build_login_payload(provider)
    payload.setdefault("action", "login")
    _emit_payload(payload, json_output)


@app.command()
def logout(
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON"),
) -> None:
    """Run provider logout."""
    _emit_payload(build_logout_payload(provider), json_output)
