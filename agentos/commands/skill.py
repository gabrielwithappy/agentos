import typer
from rich.console import Console

app = typer.Typer(help="Manage agent skills")
console = Console()

@app.command()
def list():
    """List installed skills."""
    console.print("[bold blue]Installed Skills:[/bold blue]")
    # TODO: List skills in .agents/skills
    console.print("- harness")

@app.command()
def add(path: str):
    """Add a new skill from a path."""
    console.print(f"Adding skill from {path}...")
