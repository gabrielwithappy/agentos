from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentos.observability.adapters.github import GithubDashboardAdapter
from agentos.observability.plan_parser import (
    parse_exec_plan,
    render_card_body,
    status_to_board_status,
    upsert_meta_field,
)
from agentos.observability.setup import get_gh_token

app = typer.Typer(help="Sync exec-plan documents to an external dashboard")
console = Console()

ACTIVE_PLANS_DIR = Path(".agentos/project/exec-plans/active")


def _sync_one(adapter: GithubDashboardAdapter, path: Path) -> None:
    """Sync a single exec-plan file to a board card. Raises on failure."""
    text = path.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)
    if not summary.title:
        raise ValueError(f"Could not find a title (H1) in {path}")

    body = render_card_body(summary, str(path))
    board_status = status_to_board_status(summary.status, summary.reviewed)

    existing = adapter._find_item_by_title_with_project_item_id(summary.title)
    if existing is None:
        project_item_id, draft_issue_id = adapter._create_draft_item_with_content_id(title=summary.title)
        console.print(f"[green]Created new card: {summary.title}[/green]")
    else:
        project_item_id, draft_issue_id = existing
        console.print(f"[green]Found existing card: {summary.title}[/green]")

    adapter.update_draft_issue_body(draft_issue_id, summary.title, body)

    option_id = adapter._status_option_ids.get(board_status)
    if option_id is not None:
        adapter._set_status(project_item_id, option_id)
        console.print(f"[green]Synced status: {board_status}[/green]")
    else:
        console.print(
            f"[yellow]Status option '{board_status}' not found on board — "
            "card created/updated but status not set. Run Milestone 3's board setup first.[/yellow]"
        )

    board_url = f"https://github.com/users/{adapter.owner}/projects/{adapter.project_number}"
    if summary.dashboard_item_id != project_item_id:
        updated_text = upsert_meta_field(text, "dashboard_item_id", project_item_id)
        path.write_text(updated_text, encoding="utf-8")
    console.print(f"[green]dashboard_item_id: {project_item_id}[/green]")
    console.print(f"[green]board: {board_url}[/green]")


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
        console.print(
            "[red]Missing owner/project number. "
            "Set --owner/--project-number or OBSERVABILITY_GITHUB_OWNER/OBSERVABILITY_GITHUB_PROJECT_NUMBER.[/red]"
        )
        raise typer.Exit(1)

    token = get_gh_token()
    if not token:
        console.print("[red]No GitHub token available. Run `gh auth login` first.[/red]")
        raise typer.Exit(1)

    adapter = GithubDashboardAdapter(token=token, owner=owner, project_number=project_number)
    adapter._ensure_project_metadata()

    if all_active:
        paths = sorted(ACTIVE_PLANS_DIR.glob("*.md"))
        if not paths:
            console.print(f"[yellow]No .md files found under {ACTIVE_PLANS_DIR}[/yellow]")
            raise typer.Exit(0)

        succeeded = 0
        failed = 0
        for path in paths:
            try:
                _sync_one(adapter, path)
                succeeded += 1
            except Exception as exc:
                failed += 1
                console.print(f"[red]Failed to sync {path}: {exc}[/red]")

        console.print(f"[bold]{succeeded} succeeded, {failed} failed[/bold]")
        if failed > 0:
            raise typer.Exit(1)
        return

    path = Path(plan_path)
    if not path.is_file():
        console.print(f"[red]Plan file not found: {plan_path}[/red]")
        raise typer.Exit(1)

    try:
        _sync_one(adapter, path)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
