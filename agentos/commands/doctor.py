import sys
import json
import typer
from rich.console import Console

from agentos.terminal.paths import state_status

app = typer.Typer(help="Check system dependencies and state")
console = Console()

@app.callback(invoke_without_command=True)
def main(json_output: bool = typer.Option(False, "--json", help="Emit sanitized JSON status.")):
    """Diagnose the AgentOS installation."""
    status = state_status()
    if json_output:
        typer.echo(json.dumps(status, sort_keys=True))
        raise typer.Exit(0 if status["configured"] else 1)

    console.print("[bold blue]Checking AgentOS health...[/bold blue]")
    issues_found = False
    if sys.version_info < (3, 11):
        console.print("[bold red]Python version must be >= 3.11[/bold red]")
        issues_found = True
    else:
        console.print(f"[bold green]OK[/bold green] Python version: {sys.version_info.major}.{sys.version_info.minor}")
    if not status["configured"]:
        console.print(f"[bold red]AGENTOS_HOME not configured at: {status['home']}[/bold red]")
        console.print("[yellow]Hint: Run 'agentos setup' to initialize the environment.[/yellow]")
        issues_found = True
    else:
        console.print(f"[bold green]OK[/bold green] AGENTOS_HOME: {status['home']}")
        console.print(f"[bold green]OK[/bold green] state-manifest.json schema: {status.get('manifest_schema_version')}")
    if issues_found:
        console.print("[bold red]Diagnosis completed with errors.[/bold red]")
        raise typer.Exit(code=1)
    console.print("[bold green]All systems go.[/bold green]")
