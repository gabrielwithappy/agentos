import os
import subprocess
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
    console.print("[bold blue]Running harness loop...[/bold blue]")
    
    root_dir = Path.cwd()
    canonical_script = root_dir / ".agents" / "skills" / "harness" / "harness-loop.sh"
    
    if not canonical_script.is_file():
        console.print(f"[bold red]❌ canonical harness loop script를 찾을 수 없습니다: {canonical_script}[/bold red]", err=True)
        raise typer.Exit(code=1)
        
    # Pass all remaining arguments to the script
    args = ctx.args if ctx.args else []
    
    try:
        # We replace the current process similar to `exec` in bash
        os.execv(str(canonical_script), [str(canonical_script)] + args)
    except Exception as e:
        console.print(f"[bold red]Failed to execute harness loop: {e}[/bold red]", err=True)
        raise typer.Exit(code=1)
