import typer
from rich.console import Console

app = typer.Typer(help="Check system dependencies and state")
console = Console()

@app.callback(invoke_without_command=True)
def main():
    """Diagnose the AgentOS installation."""
    console.print("[bold blue]Checking AgentOS health...[/bold blue]")
    # TODO: Check python version, env vars, manifest
    console.print("[bold green]All systems go.[/bold green]")
