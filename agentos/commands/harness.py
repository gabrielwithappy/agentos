import os
import sys
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(
    help="Run the core harness loop",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
console = Console()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    project_root: str | None = typer.Option(None, "--project-root", help="AgentOS project root containing .agents."),
):
    """Execute the harness loop."""
    console.print("[bold blue]Starting Python harness engine...[/bold blue]")
    if not project_root:
        typer.echo("Missing --project-root. Next: pass the AgentOS project with --project-root.", err=True)
        raise typer.Exit(code=2)
    root_dir = Path(project_root).expanduser().resolve(strict=False)
    python_engine = root_dir / ".agents" / "skills" / "harness" / "core-engine" / "harness_loop.py"
    
    if not python_engine.is_file():
        typer.echo(f"Could not find harness engine at: {python_engine}", err=True)
        typer.echo("Next: run agentos setup for CLI state, then pass the AgentOS project with --project-root.", err=True)
        raise typer.Exit(code=2)
        
    # Pass all remaining arguments to the python engine
    args = ctx.args if ctx.args else []
    
    try:
        # We replace the current process with the python engine
        os.execv(sys.executable, [sys.executable, str(python_engine)] + args)
    except Exception as e:
        typer.echo(f"Failed to execute harness loop: {e}", err=True)
        raise typer.Exit(code=1)
