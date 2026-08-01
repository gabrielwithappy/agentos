from __future__ import annotations

import json
from typing import Optional

import typer

from agentos.gateway.service import GatewayService
from agentos.gateway.types import GatewayError
from agentos.gateway.worker import SingleWorker
from agentos.runtime.protocol import RecordPolicy

app = typer.Typer(help="Manage local Gateway Core runs", add_completion=False)


def _emit(payload, *, json_output: bool = True) -> None:
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
    else:
        typer.echo(payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True))


def _handle_error(exc: GatewayError, *, json_output: bool) -> None:
    payload = {"type": "error", "error": {"code": exc.code, "message": str(exc)}, "recovery": "Run agentos gateway doctor."}
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
    else:
        typer.echo(str(exc), err=True)
    raise typer.Exit(exc.exit_code)


@app.command()
def doctor(provider: Optional[str] = typer.Option(None, "--provider"), json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        _emit(GatewayService().doctor(provider=provider), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def submit(
    prompt: str = typer.Argument(...),
    provider: Optional[str] = typer.Option(None, "--provider"),
    cwd: Optional[str] = typer.Option(None, "--cwd"),
    record_policy: RecordPolicy = typer.Option("metadata", "--record-policy"),
    idempotency_key: Optional[str] = typer.Option(None, "--idempotency-key"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        run = GatewayService().submit(prompt, provider=provider, cwd=cwd, record_policy=record_policy, idempotency_key=idempotency_key)
        _emit(run.to_dict(include_prompt=False), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command("list")
def list_runs(status: Optional[str] = typer.Option(None, "--status"), json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        runs = [run.to_dict() for run in GatewayService().list_runs(status=status)]
        _emit({"runs": runs}, json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def status(run_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        _emit(GatewayService().status(run_id).to_dict(), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def events(run_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        events_payload = [event.to_dict() for event in GatewayService().events(run_id)]
        if json_output:
            for event in events_payload:
                typer.echo(json.dumps(event, sort_keys=True))
        else:
            _emit({"events": events_payload}, json_output=False)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def cancel(run_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        _emit(GatewayService().cancel(run_id).to_dict(), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def retry(
    run_id: str,
    prompt: Optional[str] = typer.Argument(None),
    yes: bool = typer.Option(False, "--yes"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        _emit(GatewayService().retry(run_id, prompt=prompt, yes=yes).to_dict(), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def prune(before: str = typer.Option(..., "--before"), yes: bool = typer.Option(False, "--yes"), json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        _emit(GatewayService().prune(before=before, yes=yes), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)


@app.command()
def worker(once: bool = typer.Option(False, "--once"), json_output: bool = typer.Option(False, "--json")) -> None:
    if not once:
        typer.echo("Gateway Core supports worker --once. Long-running daemon mode is out of scope.", err=True)
        raise typer.Exit(2)
    try:
        _emit(SingleWorker().run_once(), json_output=json_output)
    except GatewayError as exc:
        _handle_error(exc, json_output=json_output)
