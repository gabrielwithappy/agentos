from pathlib import Path
import typer
from rich.console import Console

from agentos.terminal.paths import StateError, initialize_state
from agentos.terminal.skills import install_bundled_skills

app = typer.Typer(help="Initialize AgentOS environment")
console = Console()

@app.callback(invoke_without_command=True)
def main(
    home: str | None = typer.Option(None, "--home", help="Override AGENTOS_HOME."),
    refresh_bundled_skills: bool = typer.Option(False, "--refresh-bundled-skills", help="Replace preserved bundled skill names."),
):
    """Run the setup process for AgentOS."""
    console.print("[bold blue]Setting up AgentOS...[/bold blue]")
    try:
        dest = initialize_state(Path(home) if home else None)
        summary = install_bundled_skills(dest, refresh=refresh_bundled_skills)
        console.print(
            "기본 카탈로그 스킬: "
            f"설치 {summary.installed}, 최신 {summary.already_current}, 갱신 {summary.bundled_updated}, "
            f"보존 {summary.custom_preserved}, 갱신 가능 {summary.bundled_update_available}, 실패 {summary.failed}"
        )
        if summary.failed:
            raise StateError("Default skill installation failed. Next: agentos setup")
            
        # Call the unified hook installation script
        import subprocess
        hook_script = Path(__file__).parent.parent.parent / "scripts" / "install-hooks.sh"
        if hook_script.exists():
            console.print("[bold blue]Installing Unified Hooks for all CLIs...[/bold blue]")
            subprocess.run(["bash", str(hook_script)], check=False)
            
        console.print("[bold green]Verification successful![/bold green] CLI state is ready.")
        console.print(f"[bold green]PASS[/bold green] agentos-setup destination={dest} selection=catalog-default-skills")
    except (StateError, OSError, ValueError) as e:
        console.print(f"[bold red]Setup failed: {e}[/bold red]")
        raise typer.Exit(code=1)
