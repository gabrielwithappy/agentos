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
def main(ctx: typer.Context):
    """Execute the harness loop."""
    console.print("[bold blue]Starting Python harness engine...[/bold blue]")
    
    root_dir = Path.cwd()
    python_engine = root_dir / ".agents" / "skills" / "harness" / "core-engine" / "harness_loop.py"
    
    if not python_engine.is_file():
        console.print(f"[bold red]❌ 하네스 엔진을 찾을 수 없습니다: {python_engine}[/bold red]", err=True)
        raise typer.Exit(code=1)
        
    # Pass all remaining arguments to the python engine
    args = ctx.args if ctx.args else []
    
    try:
        # We replace the current process with the python engine
        os.execv(sys.executable, [sys.executable, str(python_engine)] + args)
    except Exception as e:
        console.print(f"[bold red]Failed to execute harness loop: {e}[/bold red]", err=True)
        raise typer.Exit(code=1)
