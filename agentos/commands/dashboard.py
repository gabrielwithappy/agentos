from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentos.observability.adapters.github import GithubDashboardAdapter
from agentos.observability.setup import get_gh_token
from agentos.observability.plan_events import emit_plan_status_changed
from agentos.observability.notifier import notifier
from datetime import datetime, timezone
from agentos.observability.plan_parser import parse_exec_plan, status_to_board_status, upsert_meta_field

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


def _resolve_configured_adapters(owner: str | None, project_number: str | None, config: str | None) -> bool:
    """Load configured dashboard adapters into the shared notifier registry.

    Shared by sync-plan and pull-plan so both commands honor the same
    --owner/--project-number/--config resolution order. Returns True if at
    least one adapter ended up registered.
    """
    notifier.clear_adapters()
    notifier.load_adapters_from_config()

    if owner and project_number:
        token = get_gh_token()
        if token:
            adapter = GithubDashboardAdapter(token=token, owner=owner, project_number=project_number)
            if not any(isinstance(a, GithubDashboardAdapter) for a in notifier._adapters):
                notifier.register_adapter(adapter)

    return bool(notifier._adapters)


@app.command("sync-plan")
def sync_plan(
    plan_path: str = typer.Argument(None, help="Path to an exec-plan markdown file"),
    all_active: bool = typer.Option(False, "--all", help="Sync every .md file under the active exec-plans directory"),
    owner: str = typer.Option(None, "--owner", envvar="OBSERVABILITY_GITHUB_OWNER"),
    project_number: str = typer.Option(None, "--project-number", envvar="OBSERVABILITY_GITHUB_PROJECT_NUMBER"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file or custom adapter configuration"),
) -> None:
    """Push exec-plan document(s) onto GitHub Projects v2 board card(s) or configured external dashboards."""
    if not plan_path and not all_active:
        console.print("[red]Provide a plan file path, or use --all to sync every active exec-plan.[/red]")
        raise typer.Exit(1)

    if plan_path and not all_active and not Path(plan_path).is_file():
        console.print(f"[red]Plan file not found: {plan_path}[/red]")
        raise typer.Exit(1)

    if not config and (not owner or not project_number):
        console.print("[yellow]대시보드가 설정되어 있지 않아 동기화를 건너뜁니다.[/yellow]")
        raise typer.Exit(0)

    if not _resolve_configured_adapters(owner, project_number, config):
        console.print("[yellow]대시보드가 설정되어 있지 않아 동기화를 건너뜁니다.[/yellow]")
        raise typer.Exit(0)

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


def _do_pull(plan_path: Path, adapter: GithubDashboardAdapter) -> None:
    text = plan_path.read_text(encoding="utf-8")
    summary = parse_exec_plan(text)
    if not summary.dashboard_item_id:
        console.print(f"[yellow]{plan_path}: dashboard_item_id가 없습니다 — 먼저 sync-plan을 실행하세요.[/yellow]")
        return

    try:
        remote_status = adapter.fetch_remote_status(summary.dashboard_item_id)
    except ValueError as exc:
        console.print(f"[red]{plan_path}: 원격 상태 조회 실패 - {exc}[/red]")
        return

    if remote_status is None:
        console.print(
            f"[red]{plan_path}: 보드에서 Status 값을 찾지 못했습니다 — "
            "카드가 삭제되었거나 Status 필드가 비어 있는지 보드에서 확인하세요.[/red]"
        )
        return

    expected_status = status_to_board_status(summary.status, summary.reviewed)
    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    updated = upsert_meta_field(text, "remote_board_status", remote_status)
    updated = upsert_meta_field(updated, "remote_board_synced_at", synced_at)
    plan_path.write_text(updated, encoding="utf-8")

    if remote_status == expected_status:
        console.print(f"[green]{plan_path}: 로컬과 원격 보드 상태 일치 ({remote_status})[/green]")
    else:
        console.print(
            f"[yellow]{plan_path}: 상태 불일치 — 로컬 계획 기준 예상={expected_status}, 원격 보드 실제={remote_status} "
            "(참고: 이 값은 참고용 기록이며 계획의 공식 상태/reviewed 필드는 자동으로 바뀌지 않습니다)[/yellow]"
        )


@app.command("pull-plan")
def pull_plan(
    plan_path: str = typer.Argument(None, help="Path to an exec-plan markdown file"),
    all_active: bool = typer.Option(False, "--all", help="Pull remote Status for every .md file under the active exec-plans directory"),
    owner: str = typer.Option(None, "--owner", envvar="OBSERVABILITY_GITHUB_OWNER"),
    project_number: str = typer.Option(None, "--project-number", envvar="OBSERVABILITY_GITHUB_PROJECT_NUMBER"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file or custom adapter configuration"),
) -> None:
    """Read the GitHub Projects v2 board card's current Status back into local exec-plan file(s).

    Observational only: never changes the plan's official 상태/reviewed fields.
    """
    if not plan_path and not all_active:
        console.print("[red]Provide a plan file path, or use --all to pull every active exec-plan.[/red]")
        raise typer.Exit(1)

    if not config and (not owner or not project_number):
        console.print("[yellow]대시보드가 설정되어 있지 않아 pull을 건너뜁니다.[/yellow]")
        raise typer.Exit(0)

    if not _resolve_configured_adapters(owner, project_number, config):
        console.print("[yellow]대시보드가 설정되어 있지 않아 pull을 건너뜁니다.[/yellow]")
        raise typer.Exit(0)

    github_adapters = [a for a in notifier._adapters if isinstance(a, GithubDashboardAdapter)]
    if not github_adapters:
        console.print("[yellow]pull-plan을 지원하는 어댑터가 없습니다 (현재 GitHub만 지원).[/yellow]")
        raise typer.Exit(0)
    adapter = github_adapters[0]

    paths = sorted(ACTIVE_PLANS_DIR.glob("*.md")) if all_active else [Path(plan_path)]
    for path in paths:
        if not path.is_file():
            console.print(f"[red]Plan file not found: {path}[/red]")
            continue
        _do_pull(path, adapter)
