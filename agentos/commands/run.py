import typer
from rich.console import Console

app = typer.Typer(help="Start the main agent session")
console = Console()

@app.callback(invoke_without_command=True)
def main():
    """Start the interactive agent chat session."""
    console.print("[bold blue]Starting AgentOS session...[/bold blue]")
    # TODO: Implement chat loop
    console.print("[bold yellow]Not implemented yet.[/bold yellow]")
