# GitHub 대시보드 Status 되읽기(양방향 동기화 1단계) 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-08-01<br>
> reviewed: false<br>
> usability_review_required: true<br>
> user_request: 현재 GitHub 대시보드 연동은 AgentOS → GitHub 단방향 push만 지원한다. 대시보드 기능 확장을 위해, 사람이 GitHub Projects 보드에서 바꾼 카드 Status를 다시 AgentOS로 읽어오는 양방향 흐름을 계획 문서로 작성해 달라는 요청.<br>
> active_agent: Claude Code<br>
> active_session: f145077e-dbba-4d91-8e7c-412b076b55b9<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg039us<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** AgentOS → GitHub 단방향으로만 흐르던 대시보드 동기화에, GitHub Projects v2 보드에서 사람이 카드 Status를 바꾸면 그 값을 다시 로컬 계획 문서로 읽어오는 되읽기(pull) 경로를 추가한다.

**사용자 결과:** `agentos dashboard pull-plan <계획 파일>`을 실행하면 보드에서 사람이 바꾼 카드 Status가 계획 문서에 기록되고, 로컬 계획이 기대하는 상태와 일치하는지 여부가 터미널에 바로 표시된다.

**진행 상태:** 계획 초안 작성, 리뷰 대기 중 (Gate 2 서브에이전트 리뷰 미착수)

**아키텍처:** 기존 push 전용 `DashboardAdapter`/`DashboardNotifier` 레지스트리 구조는 그대로 두고, `GithubDashboardAdapter`에 읽기 전용 `fetch_remote_status(item_id)` 메서드를 추가한다. 새 CLI 서브커맨드 `agentos dashboard pull-plan`이 이를 호출해 로컬 계획 파일의 관찰용 메타 필드(`remote_board_status`, `remote_board_synced_at`)만 갱신한다. 계획의 공식 판단 필드인 `> **상태:**`/`reviewed`는 건드리지 않아, 보드 드래그 한 번으로 Gate 2 승인 권한이 우회되는 것을 막는다.

**기술 스택:** Python 3.11+, typer, GitHub GraphQL API(Projects v2) — 기존 `sync-plan`이 이미 쓰는 `gh` CLI 토큰 자격 증명을 그대로 재사용.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 초안 |
| 완료됨 | 현재 아키텍처 조사(단방향 push 확인), 양방향 범위 확정(보드 Status 되읽기만), 계획 초안 작성 |
| 현재 위치 | Gate 0/Gate 1 자기 검토 완료, Gate 2 서브에이전트 리뷰(`request_review.py`) 대기 |
| 다음 단계 | Gate 2 리뷰 통과 → `reviewed: true` 반영 → Task 1부터 구현 실행 |
| 완료 신호 | `pytest tests/test_dashboard_pull.py` 전체 통과 + `agentos dashboard pull-plan --help`에 새 커맨드 노출 확인 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | GitHub Projects 보드에서 사람이 카드 Status를 바꾸면, `agentos dashboard pull-plan`으로 그 값을 로컬 계획 문서에 다시 반영하고 로컬/원격 상태 불일치를 즉시 확인할 수 있다. |
| 누구를 위한 것인가? | exec-plan을 GitHub 보드로 운영하는 리뷰어/운영자, 그리고 다음 세션에서 계획을 이어받는 에이전트. |
| 일상 사용에서 무엇이 달라지는가? | 지금까지는 보드 카드를 옮겨도 로컬 계획 파일에는 아무 흔적이 남지 않았다. 이제 `pull-plan`을 실행하면 원격 Status와 동기화 시각이 계획 파일에 기록되고, 기대 상태와 다르면 노란색 경고로 드러난다. |
| 무엇은 바뀌지 않는가? | 계획의 공식 `> **상태:**`/`reviewed` 필드, Gate 2 승인 절차, 그리고 기존 `sync-plan` push 동작은 변경하지 않는다. 보드에서 카드를 옮기는 것만으로 계획이 자동 승인되지 않는다. 댓글/라벨 읽기, 웹훅 수신 서버는 이번 범위에서 제외한다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 원격 Status 조회 API 추가 | (내부 준비 단계, 사용자 직접 노출 없음) | `agentos/observability/adapters/github.py` | `Run:` `python3 -c "from agentos.observability.adapters.github import GithubDashboardAdapter; print(hasattr(GithubDashboardAdapter, 'fetch_remote_status'))"` / `Expected:` `True` |
| 2. `pull-plan` CLI 명령 추가 | `agentos dashboard pull-plan <plan>` 실행 시 보드 Status가 계획 파일에 기록되고 일치/불일치가 색상으로 표시됨 | `agentos/commands/dashboard.py` | `Run:` `agentos dashboard pull-plan --help` / `Expected:` 출력에 `pull-plan`, `--all`, `--owner`, `--project-number`, `--config` 옵션이 보임 |
| 3. 동작 검증 (단위 테스트) | 일치/불일치/미설정/미동기화 4가지 경로가 자동 검증됨 | `tests/test_dashboard_pull.py` | `Run:` `python3 -m pytest tests/test_dashboard_pull.py -v` / `Expected:` 전부 `PASSED`, 실패 0건 |
| 4. 사용법 문서화 | `docs/observability-setup.md`에서 `pull-plan` 사용법과 새 메타 필드 의미를 바로 찾을 수 있음 | `docs/observability-setup.md` | `Run:` `grep -n "pull-plan" docs/observability-setup.md` / `Expected:` 1줄 이상 매치 |

## 장기 적용 표면

- traceability surface: 이 active plan 문서, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`(lifecycle board)
- durable result surface: `docs/observability-setup.md`(사용자가 실제로 참조하는 사용법 문서), `agentos/commands/dashboard.py` + `agentos/observability/adapters/github.py`(실제 동작하는 코드)
- documentation-only exception: 없음 — 코드 변경을 동반하는 계획이며 durable result는 코드와 문서 양쪽에 남는다.

---

## File Structure

- 수정: `agentos/observability/adapters/github.py` — `GithubDashboardAdapter`에 읽기 전용 `fetch_remote_status(item_id)` 추가.
- 수정: `agentos/commands/dashboard.py` — 어댑터 설정 로직을 `_resolve_configured_adapters()`로 추출(기존 `sync-plan`이 쓰던 로직 재사용)하고, 새 `pull-plan` 서브커맨드 추가.
- 생성: `tests/test_dashboard_pull.py` — `pull-plan` 명령과 `fetch_remote_status`의 일치/불일치/미설정/미동기화 경로 단위 테스트. (기존 `tests/test_dashboard_command.py`는 `sync-plan` 전용이므로 커맨드 단위로 파일을 분리한다.)
- 수정: `docs/observability-setup.md` — `pull-plan` 사용법, `remote_board_status`/`remote_board_synced_at` 메타 필드 설명 추가.

---

## Task 상세 구현 계획

### Task 1: GithubDashboardAdapter에 원격 Status 조회 메서드 추가

**파일:**
- 수정: `agentos/observability/adapters/github.py`

**사용자에게 보이는 마일스톤:** (내부 준비 단계, Task 2에서 사용자 노출)

- [ ] **Step 1: `fetch_remote_status` 메서드 추가**

`GithubDashboardAdapter` 클래스에 아래 메서드를 추가한다. 기존 push 경로가 쓰는 `_status_option_ids`(이름→ID) 매핑과 달리, 되읽기는 `fieldValueByName`으로 현재 선택된 옵션의 **이름**을 직접 받아온다.

```python
def fetch_remote_status(self, item_id: str) -> str | None:
    """Read back the board card's current Status option name (read-only).

    Used by `agentos dashboard pull-plan` to detect Status changes a human
    made directly on the GitHub Projects v2 board (drag-and-drop), so they
    can flow back into the local exec-plan file without AgentOS silently
    overwriting the plan's authoritative `> **상태:**`/`reviewed` fields.
    """
    data = self._graphql(
        """
        query($itemId: ID!) {
          node(id: $itemId) {
            ... on ProjectV2Item {
              fieldValueByName(name: "Status") {
                ... on ProjectV2ItemFieldSingleSelectValue { name }
              }
            }
          }
        }
        """,
        {"itemId": item_id},
    )
    node = data.get("node")
    if not node:
        return None
    field_value = node.get("fieldValueByName")
    return field_value.get("name") if field_value else None
```

Run: `python3 -c "from agentos.observability.adapters.github import GithubDashboardAdapter; print(hasattr(GithubDashboardAdapter, 'fetch_remote_status'))"`
Expected: `True`

---

### Task 2: `agentos dashboard pull-plan` CLI 명령 추가

**파일:**
- 수정: `agentos/commands/dashboard.py`

**사용자에게 보이는 마일스톤:** `agentos dashboard pull-plan <plan>` 실행 시 보드 Status가 계획 파일에 기록되고 일치/불일치가 표시됨

- [ ] **Step 1: 어댑터 설정 로직을 공용 헬퍼로 추출**

`sync_plan`에 인라인으로 있던 owner/project-number/config 해석 + 어댑터 등록 로직을 아래처럼 분리해 `pull_plan`과 공유한다.

```python
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
```

`sync_plan`의 기존 동등 블록을 `if not _resolve_configured_adapters(owner, project_number, config): ... skip` 형태로 교체한다. 기존 동작(경고 메시지, `raise typer.Exit(0)`)은 그대로 유지한다.

Run: `python3 -m pytest tests/test_dashboard_command.py -v`
Expected: 기존 `sync-plan` 테스트 전부 `PASSED` (리팩터링으로 인한 회귀 없음)

- [ ] **Step 2: `pull-plan` 서브커맨드 추가**

```python
from datetime import datetime, timezone
from agentos.observability.plan_parser import parse_exec_plan, status_to_board_status, upsert_meta_field


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
        console.print(f"[red]{plan_path}: 보드에서 Status 값을 찾지 못했습니다.[/red]")
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
            f"[yellow]{plan_path}: 상태 불일치 — 로컬 계획 기준 예상={expected_status}, 원격 보드 실제={remote_status}[/yellow]"
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
```

Run: `agentos dashboard pull-plan --help`
Expected: 출력에 `pull-plan`, `--all`, `--owner`, `--project-number`, `--config` 옵션이 모두 보임

---

### Task 3: 단위 테스트 추가

**파일:**
- 생성: `tests/test_dashboard_pull.py`

**사용자에게 보이는 마일스톤:** 일치/불일치/미설정/미동기화 4가지 경로가 자동 검증됨

`tests/test_dashboard_command.py`의 `_mock_response`/`_run_graphql` 헬퍼와 GraphQL mock 패턴(`patch("agentos.observability.adapters.github.urllib.request.urlopen")`)을 그대로 재사용한다.

- [ ] **Step 1: 로컬/원격 상태 일치 케이스**

`reviewed: true`, 상태 문구에 "완료" 없음(→ 기대 `Ready`) 계획 파일에 대해 `fieldValueByName`이 `{"name": "Ready"}`를 반환하도록 mock하고, 콘솔 출력에 "일치"가 포함되는지, 계획 파일에 `remote_board_status: Ready`가 기록되는지 확인한다.

- [ ] **Step 2: 로컬/원격 상태 불일치 케이스**

동일 계획에 대해 원격 값이 `"In Progress"`인 것으로 mock하고, 콘솔에 경고(불일치, 예상/실제 값)가 출력되는지 확인한다.

- [ ] **Step 3: `dashboard_item_id` 없음 → skip**

메타 필드에 `dashboard_item_id`가 비어 있는 계획 파일을 입력하면 GraphQL 호출 없이 "먼저 sync-plan을 실행하세요" 경고만 출력되고 파일이 변경되지 않는지 확인한다.

- [ ] **Step 4: 대시보드 미설정 → graceful skip**

`owner`/`project_number`/`config`가 전부 비어 있을 때 `typer.Exit(0)`으로 안전 종료하고 "대시보드가 설정되어 있지 않아" 경고만 출력되는지 확인한다(기존 `sync-plan`의 미설정 동작과 동일 계약).

Run: `python3 -m pytest tests/test_dashboard_pull.py -v`
Expected: 4개 테스트 모두 `PASSED`

---

### Task 4: 사용법 문서화

**파일:**
- 수정: `docs/observability-setup.md`

**사용자에게 보이는 마일스톤:** `pull-plan` 사용법과 새 메타 필드 의미를 문서에서 바로 찾을 수 있음

- [ ] **Step 1: `agentos dashboard sync-plan` 섹션 아래에 되읽기 섹션 추가**

아래 내용을 포함해 `## agentos dashboard pull-plan — 보드 Status 되읽기` 섹션을 추가한다:
- 목적: 사람이 보드에서 드래그한 카드 Status를 로컬 계획 문서로 되읽는다(관찰용, 계획의 공식 상태를 자동으로 바꾸지 않음).
- 사용 예: `agentos dashboard pull-plan <exec-plan-file>`, `agentos dashboard pull-plan --all`
- 새 메타 필드 설명: `remote_board_status`(마지막으로 확인한 원격 Status 값), `remote_board_synced_at`(마지막 pull 시각, UTC).
- 명시적 비목표: 댓글/라벨 읽기, 웹훅 기반 실시간 반영, 자동 Gate 2 승인은 이 범위에 없다.

Run: `grep -n "pull-plan" docs/observability-setup.md`
Expected: 1줄 이상 매치

---

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption. 이 계획의 모든 `Run:` 검증(pytest 단위 테스트, `--help`, `grep`)은 GraphQL 호출을 mock으로 처리하며 라이브 네트워크에 의존하지 않는다. `fetch_remote_status`가 런타임에 실제로 쓰는 GitHub GraphQL API 자격 증명(`GITHUB_TOKEN`/`gh auth token`)은 기존 `sync-plan`이 이미 쓰는 것과 동일한 기존 의존성이며, 이번 계획이 새로 추가하는 의존성이 아니다.

## HISTORY Checkpoint Tagging Contract

- 구현/검증/closeout checkpoint 예시에는 `plan=.agentos/project/exec-plans/active/2026-08-01-dashboard-status-pullback.md`를 포함한다.

## 리뷰 반영 이력
- (Gate 2 리뷰 진행 후 기록)

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
