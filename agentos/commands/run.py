import json

import typer
from rich.console import Console
from rich.prompt import Prompt

from agentos.llm.redaction import sanitize
from agentos.llm.session import UnsupportedProviderError, stream_once, unsupported_provider_event

app = typer.Typer(help="Start the main agent session")
console = Console()

@app.callback(invoke_without_command=True)
def main(
    prompt: str | None = typer.Argument(None),
    json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSONL events"),
    once: bool = typer.Option(False, "--once", help="Run one LLM turn and exit"),
    provider: str = typer.Option("mock", "--provider", help="LLM provider name"),
):
    """Start the interactive agent chat session."""
    if json_output or once:
        if not once:
            typer.echo("--json requires --once for the current runtime.", err=True)
            raise typer.Exit(1)
        if prompt is None or not prompt.strip():
            event = {
                "type": "error",
                "provider": provider,
                "mode": "mock",
                "error": {
                    "code": "missing_prompt",
                    "message": "A prompt is required for agentos run --json --once.",
                },
                "recovery": "Pass a prompt argument after --once.",
            }
            typer.echo(json.dumps(sanitize(event), sort_keys=True))
            raise typer.Exit(1)
        try:
            saw_error = False
            for event in stream_once(prompt, provider=provider):
                event_payload = event.to_dict()
                if event_payload["type"] == "error":
                    saw_error = True
                typer.echo(json.dumps(sanitize(event_payload), sort_keys=True))
            if saw_error:
                raise typer.Exit(1)
        except UnsupportedProviderError:
            typer.echo(
                json.dumps(sanitize(unsupported_provider_event(provider).to_dict()), sort_keys=True)
            )
            raise typer.Exit(1)
        return

    console.print("[bold blue]Starting AgentOS session... Type 'exit' or 'quit' to end.[/bold blue]")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            if user_input.strip().lower() in ["exit", "quit"]:
                console.print("[bold yellow]Exiting AgentOS session...[/bold yellow]")
                break
                
            if not user_input.strip():
                continue
                
            console.print(f"[bold cyan]AgentOS:[/bold cyan] Received '{user_input}' (Mock response)")
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Exiting AgentOS session...[/bold yellow]")
            break
