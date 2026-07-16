import os
import sys
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(help="Check system dependencies and state")
console = Console()

@app.callback(invoke_without_command=True)
def main():
    """Diagnose the AgentOS installation."""
    console.print("[bold blue]Checking AgentOS health...[/bold blue]")
    
    issues_found = False
    
    # 1. Check Python version
    if sys.version_info < (3, 11):
        console.print("[bold red]❌ Python version must be >= 3.11[/bold red]")
        issues_found = True
    else:
        console.print(f"[bold green]✔[/bold green] Python version: {sys.version_info.major}.{sys.version_info.minor}")

    # 2. Check AGENTOS_HOME and core files
    dest_path_str = os.environ.get("AGENTOS_HOME", str(Path.home() / ".agentos"))
    dest = Path(dest_path_str)
    
    if not dest.is_dir():
        console.print(f"[bold red]❌ AGENTOS_HOME not found at: {dest}[/bold red]")
        console.print("[yellow]Hint: Run 'agentos setup' to initialize the environment.[/yellow]")
        issues_found = True
    else:
        console.print(f"[bold green]✔[/bold green] AGENTOS_HOME: {dest}")
        
        manifest_path = dest / "manifest.json"
        if not manifest_path.is_file():
            console.print(f"[bold red]❌ manifest.json not found at: {manifest_path}[/bold red]")
            issues_found = True
        else:
            console.print(f"[bold green]✔[/bold green] manifest.json found")
            
        agents_dir = dest / "core" / ".agents"
        if not agents_dir.is_dir():
            console.print(f"[bold red]❌ .agents core directory not found at: {agents_dir}[/bold red]")
            issues_found = True
        else:
            console.print(f"[bold green]✔[/bold green] Core plugins found")
            
    if issues_found:
        console.print("[bold red]Diagnosis completed with errors.[/bold red]")
        raise typer.Exit(code=1)
    else:
        console.print("[bold green]All systems go.[/bold green]")
