import os
import shutil
import json
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(help="Initialize AgentOS environment")
console = Console()

@app.callback(invoke_without_command=True)
def main():
    """Run the setup process for AgentOS."""
    console.print("[bold blue]Setting up AgentOS...[/bold blue]")
    
    # Determine DEST
    dest_path_str = os.environ.get("AGENTOS_HOME", str(Path.home() / ".agentos"))
    dest = Path(dest_path_str)
    
    try:
        # 1. mkdir -p ~/.agentos/core
        core_dir = dest / "core"
        core_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. cp -R .agents ~/.agentos/core/.agents
        # ROOT is where this CLI runs from, or the package dir.
        # Assuming we are running from the source tree where .agents is adjacent.
        root_dir = Path.cwd()
        src_agents = root_dir / ".agents"
        dest_agents = core_dir / ".agents"
        
        if src_agents.exists():
            if dest_agents.exists():
                shutil.rmtree(dest_agents)
            shutil.copytree(src_agents, dest_agents)
            console.print(f"Copied .agents to {dest_agents}")
        else:
            console.print(f"[yellow]Warning: source {src_agents} not found. Skipping copy.[/yellow]")
            
        # 3. Create manifest.json
        manifest_path = dest / "manifest.json"
        manifest_data = {"managed_by": "agentOS", "selection": "agentcore-only"}
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
            
        # 4. Verify installation
        console.print("[bold blue]Verifying installation...[/bold blue]")
        if not dest_agents.exists() or not dest_agents.is_dir():
            raise RuntimeError(f"Verification failed: {dest_agents} is missing or not a directory.")
        if not manifest_path.exists() or not manifest_path.is_file():
            raise RuntimeError(f"Verification failed: {manifest_path} is missing or not a file.")
            
        console.print("[bold green]Verification successful![/bold green] All required files and directories are present.")
        console.print(f"[bold green]PASS[/bold green] agentos-setup destination={dest} selection=agentcore-only")
    except Exception as e:
        console.print(f"[bold red]Setup failed: {e}[/bold red]")
        raise typer.Exit(code=1)
