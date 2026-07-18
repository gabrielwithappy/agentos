import os
import shutil
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(help="Manage agents")
console = Console()

def get_agents_dir() -> Path:
    dest_path_str = os.environ.get("AGENTOS_HOME", str(Path.home() / ".agentos"))
    return Path(dest_path_str) / "core" / ".agents" / "agents"

@app.command()
def list():
    """List installed agents."""
    agents_dir = get_agents_dir()
    
    console.print(f"[bold blue]Installed Agents (in {agents_dir}):[/bold blue]")
    if not agents_dir.is_dir():
        console.print("[yellow]Agents directory not found. Run 'agentos setup' first.[/yellow]")
        return
        
    agents_found = False
    for item in sorted(agents_dir.iterdir()):
        if item.is_dir() and (item / "AGENT.md").is_file():
            console.print(f"- [bold green]{item.name}[/bold green]")
            agents_found = True
            
    if not agents_found:
        console.print("[yellow]No agents installed.[/yellow]")

@app.command()
def install(path: str):
    """Install a new agent from a path."""
    source_path = Path(path).resolve()
    
    if not source_path.is_dir():
        console.print(f"[bold red]❌ Agent source must be a directory: {source_path}[/bold red]")
        raise typer.Exit(code=1)
        
    if not (source_path / "AGENT.md").is_file():
        console.print(f"[bold red]❌ Not a valid agent: {source_path}/AGENT.md is missing[/bold red]")
        raise typer.Exit(code=1)
        
    agents_dir = get_agents_dir()
    if not agents_dir.is_dir():
        console.print("[bold red]❌ Agents directory not found. Run 'agentos setup' first.[/bold red]")
        raise typer.Exit(code=1)
        
    dest_path = agents_dir / source_path.name
    console.print(f"Installing agent from [blue]{source_path}[/blue] to [blue]{dest_path}[/blue]...")
    
    try:
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(source_path, dest_path)
        console.print(f"[bold green]✔ Successfully installed agent '{source_path.name}'[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to install agent: {e}[/bold red]")
        raise typer.Exit(code=1)

# Keep add as an alias for backward compatibility
@app.command(hidden=True)
def add(path: str):
    """Alias for install."""
    install(path)
