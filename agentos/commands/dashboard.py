from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentos.observability.adapters.github import GithubDashboardAdapter
from agentos.observability.setup import get_gh_token
from agentos.observability.plan_events import emit_plan_status_changed
from agentos.observability.notifier import notifier

app = typer.Typer(help="Sync exec-plan documents to an external dashboard")
console = Console()

ACTIVE_PLANS_DIR = Path(".agentos/project/exec-plans/active")

def _do_sync(plan_path: Path) -> None:
    payload = emit_plan_status_changed(plan_path)
    outcomes = notifier.notify_and_wait(payload)
    for outcome in outcomes:
        if outcome.ok:
            console.print(f"[green]Successfully synced {plan_path} via {outcome.adapter_name}[/green]")
        else:
            console.print(f"[red]동기화 실패: {outcome.adapter_name} - {outcome.error}[/red]")


@app.command("sync-plan")
def sync_plan(
    plan_path: str = typer.Argument(None, help="Path to an exec-plan markdown file"),
    all_active: bool = typer.Option(False, "--all", help="Sync every .md file under the active exec-plans directory"),
    owner: str = typer.Option(None, "--owner", envvar="OBSERVABILITY_GITHUB_OWNER"),
    project_number: str = typer.Option(None, "--project-number", envvar="OBSERVABILITY_GITHUB_PROJECT_NUMBER"),
) -> None:
    """Push exec-plan document(s) onto GitHub Projects v2 board card(s)."""
    if not plan_path and not all_active:
        console.print("[red]Provide a plan file path, or use --all to sync every active exec-plan.[/red]")
        raise typer.Exit(1)

    if not owner or not project_number:
        console.print("[yellow]대시보드가 설정되어 있지 않아 동기화를 건너뜁니다.[/yellow]")
        raise typer.Exit(0)

    token = get_gh_token()
    if not token:
        console.print("[yellow]대시보드가 설정되어 있지 않아 동기화를 건너뜁니다.[/yellow]")
        raise typer.Exit(0)

    adapter = GithubDashboardAdapter(token=token, owner=owner, project_number=project_number)
    # Temporary registration just for this CLI run
    notifier.clear_adapters()
    notifier.register_adapter(adapter)

    if all_active:
        paths = sorted(ACTIVE_PLANS_DIR.glob("*.md"))
        if not paths:
            console.print(f"[yellow]No .md files found under {ACTIVE_PLANS_DIR}[/yellow]")
            raise typer.Exit(0)

        for path in paths:
            try:
                _do_sync(path)
            except Exception as exc:
                console.print(f"[red]Failed to sync {path}: {exc}[/red]")

        return

    path = Path(plan_path)
    if not path.is_file():
        console.print(f"[red]Plan file not found: {plan_path}[/red]")
        raise typer.Exit(1)

    try:
        _do_sync(path)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

