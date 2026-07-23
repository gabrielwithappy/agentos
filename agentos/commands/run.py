import json
import sys

import typer
from rich.console import Console

from agentos.llm.redaction import sanitize
from agentos.llm.session import UnsupportedProviderError, stream_once, unsupported_provider_event
from agentos.terminal.hooks import HookError, apply_input_hooks
from agentos.terminal.paths import read_preferred_provider
from agentos.terminal.tui import run_tui

app = typer.Typer(help="Start the main agent session")
console = Console()

@app.callback(invoke_without_command=True)
def main(
    prompt: str | None = typer.Argument(None),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSONL events"),
    once: bool = typer.Option(False, "--once", help="Run one LLM turn and exit"),
    provider: str | None = typer.Option(None, "--provider", help="LLM provider name"),
):
    """Start the interactive agent chat session."""
    selected_provider = provider or read_preferred_provider() or "mock"
    if json_output and not once:
        typer.echo("--json requires --once.", err=True)
        raise typer.Exit(2)
    if once:
        if prompt is None or not prompt.strip():
            typer.echo("A prompt is required. Next: agentos run --once \"<prompt>\".", err=True)
            raise typer.Exit(2)
        try:
            prompt = apply_input_hooks(prompt)
        except HookError as exc:
            if json_output:
                typer.echo(json.dumps(sanitize({
                    "type": "error",
                    "provider": selected_provider,
                    "mode": "hook",
                    "error": {"code": "hook_failed", "message": str(exc)},
                    "recovery": "Next: agentos hook config show",
                }), sort_keys=True))
            typer.echo(f"Hook {exc.hook} failed. Next: agentos hook config show", err=True)
            raise typer.Exit(1 if exc.critical else 0)
        try:
            saw_error = False
            for event in stream_once(prompt, provider=selected_provider):
                event_payload = event.to_dict()
                event_payload.setdefault("metadata", {})
                event_payload["metadata"].setdefault("cli", {"schema_version": "agentos.cli-event/v1"})
                if event_payload["type"] == "error":
                    saw_error = True
                if json_output:
                    typer.echo(json.dumps(sanitize(event_payload), sort_keys=True))
                else:
                    if event_payload["type"] == "message_delta" and event_payload.get("text"):
                        console.print(event_payload["text"])
            if saw_error:
                raise typer.Exit(1)
        except UnsupportedProviderError:
            if json_output:
                typer.echo(json.dumps(sanitize(unsupported_provider_event(selected_provider).to_dict()), sort_keys=True))
            else:
                typer.echo(unsupported_provider_event(selected_provider).error["message"], err=True)
            raise typer.Exit(1)
        return

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        typer.echo('Interactive mode requires a TTY. Next: agentos run --once "<prompt>".', err=True)
        raise typer.Exit(2)
    raise typer.Exit(run_tui(provider=selected_provider))
