from pathlib import Path
import typer
from rich.console import Console

from agentos.terminal.paths import StateError, initialize_state

app = typer.Typer(help="Initialize AgentOS environment")
console = Console()

@app.callback(invoke_without_command=True)
def main(home: str | None = typer.Option(None, "--home", help="Override AGENTOS_HOME.")):
    """Run the setup process for AgentOS."""
    console.print("[bold blue]Setting up AgentOS...[/bold blue]")
    try:
        dest = initialize_state(Path(home) if home else None)
        console.print("[bold green]Verification successful![/bold green] CLI state is ready.")
        console.print(f"[bold green]PASS[/bold green] agentos-setup destination={dest} selection=cli-state-only")
    except (StateError, OSError, ValueError) as e:
        console.print(f"[bold red]Setup failed: {e}[/bold red]")
        raise typer.Exit(code=1)
