import os
import shutil
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(help="Manage agent skills")
console = Console()

def get_skills_dir() -> Path:
    dest_path_str = os.environ.get("AGENTOS_HOME", str(Path.home() / ".agentos"))
    return Path(dest_path_str) / "core" / ".agents" / "skills"

@app.command()
def list():
    """List installed skills."""
    skills_dir = get_skills_dir()
    
    console.print(f"[bold blue]Installed Skills (in {skills_dir}):[/bold blue]")
    if not skills_dir.is_dir():
        console.print("[yellow]Skills directory not found. Run 'agentos setup' first.[/yellow]")
        return
        
    skills_found = False
    for item in sorted(skills_dir.iterdir()):
        if item.is_dir() and (item / "SKILL.md").is_file():
            console.print(f"- [bold green]{item.name}[/bold green]")
            skills_found = True
            
    if not skills_found:
        console.print("[yellow]No skills installed.[/yellow]")

@app.command()
def add(path: str):
    """Add a new skill from a path."""
    source_path = Path(path).resolve()
    
    if not source_path.is_dir():
        console.print(f"[bold red]❌ Skill source must be a directory: {source_path}[/bold red]")
        raise typer.Exit(code=1)
        
    if not (source_path / "SKILL.md").is_file():
        console.print(f"[bold red]❌ Not a valid skill: {source_path}/SKILL.md is missing[/bold red]")
        raise typer.Exit(code=1)
        
    skills_dir = get_skills_dir()
    if not skills_dir.is_dir():
        console.print("[bold red]❌ Skills directory not found. Run 'agentos setup' first.[/bold red]")
        raise typer.Exit(code=1)
        
    dest_path = skills_dir / source_path.name
    console.print(f"Adding skill from [blue]{source_path}[/blue] to [blue]{dest_path}[/blue]...")
    
    try:
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(source_path, dest_path)
        console.print(f"[bold green]✔ Successfully added skill '{source_path.name}'[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to add skill: {e}[/bold red]")
        raise typer.Exit(code=1)
