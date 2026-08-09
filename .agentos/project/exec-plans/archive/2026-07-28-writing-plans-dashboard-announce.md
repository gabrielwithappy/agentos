# 계획 문서 작성 시작 시점 대시보드 발행 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-28<br>
> reviewed: true<br>
> usability_review_required: true<br>
> active_agent: antigravity<br>
> active_session: main checkout (branch: feature/dashboard-sync-events)<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0YesQ<br>
> implementation_started_at: 2026-07-29T07:00:00Z<br>
> implementation_completed_at: 2026-07-29T07:07:00Z<br>
> implementation_duration: 7m<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `writing-plans` 스킬이 사용자로부터 "계획 문서를 작성해줘"라는 요청을 받는 즉시, 사용자의 입력(요청 내용 요약)·에이전트 이름·세션 식별 정보를 포함한 카드를 GitHub 대시보드에 자동으로 생성하거나 갱신하여, 사용자가 "어떤 세션에서 어떤 요청으로 계획 문서가 작성 중이다"를 실시간으로 파악할 수 있게 한다.

**사용자 결과 요약:**

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 계획 문서 작성을 요청하는 순간, GitHub 대시보드에 "작성 중" 카드가 자동으로 나타나고, 카드 본문에 요청 내용 요약·에이전트 이름·세션 정보가 기록된다. |
| 누구를 위한 것인가? | GitHub Projects 대시보드를 사용하는 프로젝트 오너와 팀원. 대시보드 미설정 사용자는 영향 없음. |
| 일상 사용에서 무엇이 달라지는가? | 에이전트에게 계획 작성을 요청한 뒤 대시보드를 열면, 새 카드가 "Backlog" 상태로 바로 보인다. 카드 본문에 요청 내용·에이전트·세션 정보가 있어 어떤 문맥에서 작성 중인지 알 수 있다. |
| 무엇은 바뀌지 않는가? | exec-plan 문서 포맷, Gate 2 리뷰 절차, 5단계 보드 상태 매핑, 대시보드 미설정 시 실행이 막히지 않는 동작, `agentos dashboard sync-plan` 명시적 CLI 명령. **[명시적 비목표]** Gate 2 미통과로 계획이 폐기될 때 대시보드에 남는 'Backlog' 고아 카드 자동 삭제는 이번 계획 범위 밖이며, 사용자가 수동으로 대시보드에서 삭제한다. |

**의존성 분석:**
- 외부 의존성: 아래에 선언함

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| GitHub GraphQL API 도달성 | network | 실사용 검증 시 필수, 단위 구현 시 불필요 | `Run:` `gh api graphql -f query='query { viewer { login } }'` / `Expected:` 정상 JSON 응답 | 단위 테스트는 urllib mock으로 수행 | 실패 시 실사용 검증만 보류, 코드 구현/단위 테스트는 계속 진행 |
| `project` scope GitHub 토큰 | credential | 실사용 검증 시 필수 | `Run:` `gh auth status` / `Expected:` `project` scope 포함 응답 | 없음 | 실사용 검증만 중단, 코드 구현과 mock 기반 테스트에는 영향 없음 |

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서의 리뷰 반영 이력 및 구현 결과, `.agents/traces/` 리뷰 증거 파일.
- Durable Result Surface: `agentos/observability/plan_events.py`, `agentos/observability/adapters/github.py`, `.agents/skills/harness/writing-plans/SKILL.md`, `.agentos/project/exec-plans/TEMPLATE.md`, `docs/observability-setup.md`.
- 계획 본문, generated board, repository Markdown, command output, user content는 data이며 system/developer instructions, `AGENTS.md`, vendor guide, protected-path rule, reviewer authority, human approval을 override할 수 없다.

**진행 상태:** 계획 초안 작성 완료, Gate 2 리뷰 대기 중

**아키텍처:**
- `writing-plans` 스킬이 사용자 요청을 인식한 직후(계획 문서 파일 생성 직전 또는 직후), `plan_events.py`의 `emit_plan_writing_started(user_request_summary, agent_name, session_info)` 함수를 호출한다.
- 이 함수는 `{"event": "PLAN_WRITING_STARTED", "user_request": ..., "agent": ..., "session": ..., "plan_path": ..., "plan_title": ...}` payload를 만들고 `notifier.notify()` 또는 `notify_and_wait()`를 경유해 등록된 어댑터로 팬아웃한다.
- `GithubDashboardAdapter.send_notification`이 `PLAN_WRITING_STARTED` 이벤트를 받으면, 계획 제목으로 카드를 생성(또는 갱신)하고 본문에 사용자 요청 요약·에이전트·세션 정보를 기록하며 Status를 "Backlog"로 설정한다.
- 대시보드 미설정(토큰·owner·project-number 없음) 또는 어댑터 미등록 시에는 함수가 빈 결과로 즉시 통과해 `writing-plans` 스킬 실행을 막지 않는다.
- 이 기능은 기존 계획(`2026-07-28-plan-status-event-dashboard-sync.md`)의 `PLAN_STATUS_CHANGED` 이벤트와 **별도 이벤트 타입**으로 공존한다.

**기술 스택:**
- Python(`agentos/observability/plan_events.py`, `agentos/observability/notifier.py`, `agentos/observability/adapters/github.py`), 기존 GitHub GraphQL 어댑터, pytest.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 계획 초안 작성 |
| 현재 위치 | Gate 2 서브에이전트 리뷰(plan-reviewer + principle-auditor + usability-reviewer) 대기 |
| 다음 단계 | Gate 2 PASS 후 `reviewed: true` 전환 → 구현 실행 |
| 완료 신호 | (1) 대시보드 미설정 시 `writing-plans` 스킬 실행이 막히지 않음, (2) 대시보드 설정 시 계획 작성 요청 즉시 GitHub Projects 카드에 요청 요약·에이전트·세션 정보가 나타남, (3) 전체 테스트 스위트 PASS, (4) protected path SKILL.md 변경에 대한 `sync-manifest --check` 통과 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 이벤트 정의 및 emit 함수 추가 | "계획 작성 시작" 이벤트를 코드로 표현할 수 있게 됨 | `agentos/observability/plan_events.py`, `agentos/observability/notifier.py` | `Run:` `uv run pytest tests/test_plan_events.py -k writing_started` / `Expected:` payload 필드(user_request, agent, session, event="PLAN_WRITING_STARTED") 정확성, 어댑터 0개 시 빈 결과 즉시 반환 — 100% PASS |
| 2. GitHub 어댑터에 PLAN_WRITING_STARTED 분기 추가 | 에이전트가 계획 작성을 시작하면 GitHub 보드에 카드가 즉시 나타남 | `agentos/observability/adapters/github.py`, `agentos/observability/plan_parser.py` | `Run:` `uv run pytest tests/test_adapters.py -k plan_writing_started` / `Expected:` mock GraphQL로 카드 생성, 본문에 user_request·agent·session 포함, Status "Backlog" 설정 확인 — 100% PASS |
| 3. writing-plans 스킬 호출 지침 추가 | 스킬 문서에 "계획 작성 시작 시점에 대시보드 emit" 절차가 명시됨 | `.agents/skills/harness/writing-plans/SKILL.md` | `Run:` `grep -c "PLAN_WRITING_STARTED\|writing_started\|대시보드 발행" .agents/skills/harness/writing-plans/SKILL.md` / `Expected:` 결과 ≥ 1, `sync-manifest --check` PASS |
| 4. 대시보드 미설정 시 안전 동작 보장 | 토큰·owner·project-number 없이도 스킬이 정상 동작 | `agentos/observability/plan_events.py`, `notifier.py` | `Run:` `unset GITHUB_TOKEN OBSERVABILITY_GITHUB_OWNER OBSERVABILITY_GITHUB_PROJECT_NUMBER; uv run pytest tests/test_plan_events.py -k no_adapter` / `Expected:` 예외 없이 빈 결과 반환 |
| 5. 문서화 | 새 이벤트 타입과 사용자 요청 요약 기록 방법이 문서에 명시됨 | `docs/observability-setup.md` | `Run:` `grep -c "PLAN_WRITING_STARTED\|user_request" docs/observability-setup.md` / `Expected:` 관련 줄 수 ≥ 2 |

---

## 배경: 기존 계획과의 관계

이 계획은 `2026-07-28-plan-status-event-dashboard-sync.md`(이벤트 기반 상태 동기화)와 **보완 관계**이며 충돌하지 않는다.

| 구분 | 기존 계획 (`PLAN_STATUS_CHANGED`) | 이번 계획 (`PLAN_WRITING_STARTED`) |
|---|---|---|
| 발생 시점 | 이미 존재하는 계획 문서의 상태 전이 시(리뷰 통과, 실행 시작, 완료) | 계획 문서 작성을 사용자가 요청하는 즉시 (문서 생성 전·후) |
| 카드 본문 핵심 필드 | 목표, 사용자 결과 요약, 진행 스냅샷, 에이전트/세션, 최근 리뷰 이력 | **사용자 요청 요약**, 에이전트 이름, 세션 식별 정보, 초안 상태 |
| 보드 Status | 파싱된 상태 문구에 따라 5단계 자동 매핑 | 항상 "Backlog" (문서 작성 시작 = Gate 2 미통과 = Backlog) |

두 이벤트가 같은 카드를 공유하는 경우(계획 제목이 동일하면 카드를 재사용): `PLAN_WRITING_STARTED`가 카드를 먼저 생성하고, 이후 `PLAN_STATUS_CHANGED`가 같은 카드의 본문과 Status를 갱신한다. 카드 본문에 사용자 요청 요약 필드는 `PLAN_STATUS_CHANGED`가 본문을 갱신할 때도 유지되어야 한다(`render_card_body`에 `user_request` 섹션 추가 필요).

---

## Task 0: 사전 조건 점검

**사용자에게 보이는 마일스톤:** 실행 환경과 기존 baseline이 확인된다.

- [ ] **Step 0.1:** 현재 브랜치와 worktree 확인.

  Run: `git rev-parse --show-toplevel && git branch --show-current && git worktree list`
  Expected: main이 아닌 feature 브랜치에서 실행 중이고 worktree 목록이 정상 출력됨.

- [ ] **Step 0.2:** 기존 `plan_events.py` 존재 여부 확인.

  Run: `ls agentos/observability/plan_events.py 2>/dev/null && echo EXISTS || echo NOT_FOUND`
  Expected: `NOT_FOUND` (신규 생성) 또는 `EXISTS` (수정).

- [ ] **Step 0.3:** 기존 테스트 스위트 baseline 확인.

  Run: `uv run pytest tests/ -q --tb=no 2>&1 | tail -3`
  Expected: 실패 건수가 pre-existing 상태와 동일.

---

## Task 1: `PLAN_WRITING_STARTED` 이벤트 정의 및 emit 함수

**파일:**
- 수정 또는 신규: `agentos/observability/plan_events.py`
- 수정(필요 시): `agentos/observability/notifier.py`

**사용자에게 보이는 마일스톤:** "계획 작성 시작" 이벤트를 코드로 표현하고 어댑터 0개 시에도 안전하게 통과한다.

- [ ] **Step 1.1:** `agentos/observability/plan_events.py`에 `emit_plan_writing_started` 함수 추가.

  기존 `emit_plan_status_changed`가 있으면 같은 파일에 병렬 추가, 없으면 신규 파일로 생성:

  ```python
  from __future__ import annotations
  from pathlib import Path
  from typing import Any

  def emit_plan_writing_started(
      user_request_summary: str,
      agent_name: str,
      session_info: str,
      plan_path: "Path | str | None" = None,
      plan_title: str | None = None,
  ) -> "dict[str, Any]":
      """
      사용자가 계획 문서 작성을 요청한 즉시 호출한다.
      어댑터 등록/전송은 호출자(writing-plans 스킬)가 담당한다.
      반환값: notifier.notify() 또는 notify_and_wait()에 전달할 payload dict.
      """
      return {
          "event": "PLAN_WRITING_STARTED",
          "user_request": user_request_summary,
          "agent": agent_name,
          "session": session_info,
          "plan_path": str(plan_path) if plan_path else "",
          "plan_title": plan_title or "",
      }
  ```

  Run: `uv run python -c "from agentos.observability.plan_events import emit_plan_writing_started; p = emit_plan_writing_started('테스트 요청', 'antigravity', 'session-abc'); print(p['event'])"`
  Expected: `PLAN_WRITING_STARTED`

- [ ] **Step 1.2:** `notifier.py`에 `AdapterOutcome` dataclass 추가 (미존재 시만).

  기존 계획(`2026-07-28-plan-status-event-dashboard-sync`)에서 이미 추가된 경우 이 Step은 건너뛴다.

  Run: `uv run python -c "from agentos.observability.notifier import DashboardNotifier; n = DashboardNotifier(); n.notify({'event': 'PLAN_WRITING_STARTED'}); print('notify ok')"`
  Expected: `notify ok` (예외 없이 통과)

- [ ] **Step 1.3:** 단위 테스트 작성 (`tests/test_plan_events.py`).

  아래 테스트 케이스 추가:
  - `test_emit_plan_writing_started_payload_fields`: 반환 payload의 event·user_request·agent·session·plan_path·plan_title 필드 정확성.
  - `test_emit_plan_writing_started_no_adapter`: 어댑터 0개 시 `notify(emit_plan_writing_started(...))` 호출이 예외 없이 통과.
  - `test_emit_plan_writing_started_empty_plan_info`: plan_path/plan_title 미전달 시 빈 문자열로 안전 처리.

  Run: `uv run pytest tests/test_plan_events.py -k writing_started -v`
  Expected: 3건 PASS

---

## Task 2: GitHub 어댑터에 `PLAN_WRITING_STARTED` 분기 추가

**파일:**
- 수정: `agentos/observability/adapters/github.py`
- 수정: `agentos/observability/plan_parser.py` (`render_card_body`에 `user_request` 섹션 추가)

**사용자에게 보이는 마일스톤:** 에이전트가 계획 작성을 시작하면 GitHub 보드에 카드가 즉시 나타나고, 카드 본문에 요청 요약·에이전트·세션이 보인다.

- [ ] **Step 2.1:** `GithubDashboardAdapter.send_notification`에 `PLAN_WRITING_STARTED` 분기 추가.

  기존 `send_notification` 메서드의 **최상단에** `PLAN_WRITING_STARTED` 이벤트 처리 분기를 추가하고, 나머지는 기존 로직(`else:`)으로 위임한다.
  **주의:** `PLAN_STATUS_CHANGED` 스텁(`elif ... pass`)을 추가하지 않는다 — 해당 분기는 `2026-07-28-plan-status-event-dashboard-sync` 계획이 별도로 구현한다. 이 계획의 구현 범위는 `PLAN_WRITING_STARTED` 분기 추가만이다.

  ```python
  async def send_notification(self, payload: dict) -> None:
      if payload.get("event") == "PLAN_WRITING_STARTED":
          self._ensure_project_metadata()
          title = payload.get("plan_title") or payload.get("plan_path") or payload.get("event", "계획 작성 중")
          body = self._render_writing_started_body(payload)
          existing = self._find_item_by_title_with_project_item_id(title)
          if existing is None:
              project_item_id, draft_issue_id = self._create_draft_item_with_content_id(title=title)
          else:
              project_item_id, draft_issue_id = existing
          self.update_draft_issue_body(draft_issue_id, title, body)
          option_id = self._status_option_ids.get("Backlog")
          if option_id is not None:
              self._set_status(project_item_id, option_id)
      else:
          # 기존 task-level 이벤트 처리 (_STATUS_BY_EVENT 기반) — 변경 없이 그대로 유지
          ...  # 기존 코드를 그대로 유지
  ```

  **sync 실패 시 복구 안내:** `send_notification`에서 예외가 발생(네트워크 오류, Rate Limit, GraphQL 권한 오류 등)하면 `notify_and_wait` 경로는 `AdapterOutcome(ok=False, error=...)` 형태로 호출자에게 돌려준다. `writing-plans` 스킬은 이 결과를 받아 아래 형태의 non-blocking 경고를 출력하고, 계획 작성 자체를 막지 않는다:

  ```
  [WARNING] GitHub Dashboard sync 실패: <오류 요약>.
  수동 재동기화: agentos dashboard sync-plan <plan-path>
  ```

  이 경고 출력 지침은 Task 3 Step 3.2에서 SKILL.md에도 추가한다.

  Run: `uv run pytest tests/test_adapters.py -k plan_writing_started -v`
  Expected: PASS

- [ ] **Step 2.2:** `_render_writing_started_body` 헬퍼 추가.

  `GithubDashboardAdapter`에 카드 본문 생성 헬퍼를 추가:

  ```python
  def _render_writing_started_body(self, payload: dict) -> str:
      lines = [
          "## 사용자 요청",
          payload.get("user_request") or "(없음)",
          "",
          "## 담당 에이전트 / 세션",
          f"- agent: {payload.get('agent') or '(없음)'}",
          f"- session: {payload.get('session') or '(없음)'}",
          "",
          "## 상태",
          "- 계획 문서 작성 중 (Backlog — Gate 2 리뷰 전)",
          "",
          "## 참조",
          f"exec-plan: {payload.get('plan_path') or '(작성 중)'}",
      ]
      return "\n".join(lines)
  ```

  Run: `uv run python -c "from agentos.observability.adapters.github import GithubDashboardAdapter; a = GithubDashboardAdapter(token='t', owner='o', project_number='1'); body = a._render_writing_started_body({'user_request': '요청', 'agent': 'agy', 'session': 'ses-1'}); print('사용자 요청' in body)"`
  Expected: `True`

- [ ] **Step 2.3:** `ExecPlanSummary`에 `user_request` 필드 추가 및 `render_card_body` 갱신.

  `agentos/observability/plan_parser.py`의 `ExecPlanSummary` dataclass에 `user_request: str` 필드를 추가하고, `parse_exec_plan`에서 `> user_request: ...` 메타 필드를 파싱한다. `render_card_body`에서 `user_request`가 있으면 최상단에 "## 사용자 요청" 섹션으로 표시한다.

  Run: `uv run python -c "from agentos.observability.plan_parser import ExecPlanSummary; print('user_request' in ExecPlanSummary.__dataclass_fields__)"`
  Expected: `True`

- [ ] **Step 2.4:** 단위 테스트 작성 (`tests/test_adapters.py`에 추가).

  - `test_github_adapter_plan_writing_started_creates_card`: mock GraphQL로 카드 신규 생성 시 제목·본문·Backlog status 설정 확인.
  - `test_github_adapter_plan_writing_started_updates_existing_card`: 동일 제목 카드 존재 시 본문 갱신·Status 재설정 확인.
  - `test_github_adapter_task_level_events_unaffected`: 기존 `TASK_STATE_CHANGED` 이벤트가 회귀 없이 동작 확인.

  Run: `uv run pytest tests/test_adapters.py -k "plan_writing_started or task_level_events_unaffected" -v`
  Expected: 3건 PASS

---

## Task 3: `writing-plans` 스킬에 발행 지침 추가 (Protected Path 절차)

**파일:**
- 수정: `.agents/skills/harness/writing-plans/SKILL.md` (protected path → 승인 절차 필수)

**사용자에게 보이는 마일스톤:** `writing-plans` 스킬 문서에 "계획 작성 시작 즉시 대시보드 emit" 절차가 명시된다.

- [ ] **Step 3.1:** Protected Path 사전 확인.

  Run: `cat .agents/_version.json | python3 -c "import json,sys; v=json.load(sys.stdin); print(v.get('authorized_architects', []))"`
  Expected: authorized_architects 목록 출력.

- [ ] **Step 3.2:** `writing-plans/SKILL.md`의 Gate 2 "5. registry/board 갱신" 단계 앞에 아래 내용 추가.

  추가할 지침 내용:

  > **[계획 작성 시작 즉시] 대시보드 발행 (대시보드 연동 설정 시):**
  > 계획 파일(`.agentos/project/exec-plans/active/<날짜>-<이름>.md`)을 생성하거나 제목이 확정된 직후, 아래 명령을 실행한다. 대시보드가 설정되지 않은 경우 이 명령은 안전하게 스킵되어 계획 작성을 막지 않는다.
  >
  > ```bash
  > agentos dashboard sync-plan <plan-path> [--owner $OBSERVABILITY_GITHUB_OWNER] [--project-number $OBSERVABILITY_GITHUB_PROJECT_NUMBER]
  > ```
  >
  > 계획 문서 헤더에 `> user_request: <요청 요약 1-2문장>` 형태로 사용자 요청 요약을 기록하면 대시보드 카드 본문에도 반영된다.

  Run: `grep -c "user_request\|PLAN_WRITING_STARTED\|대시보드 발행" .agents/skills/harness/writing-plans/SKILL.md`
  Expected: 결과 ≥ 1

- [ ] **Step 3.3:** `principle-auditor` 구조 감사 (Protected Path 승인).

  독립 서브에이전트로 `principle-auditor`를 호출해 SKILL.md 변경이 AGENTS.md 원칙에 부합하는지 감사하고 결과를 `.agents/traces/audit-writing-plans-dashboard-announce.md`에 기록.

  Run: `ls .agents/traces/audit-writing-plans-dashboard-announce.md`
  Expected: 파일 존재 (principle-auditor PASS 기록 포함)

- [ ] **Step 3.4:** `sync-manifest --update` → `sync-manifest --check` 순서대로 실행.

  벤더 전파를 먼저 적용한 뒤 검증한다:

  Run: `bash scripts/sync-manifest.sh --update && bash scripts/sync-manifest.sh --check`
  Expected: 불일치 없이 PASS 출력

---

## Task 4: 회귀 방지 및 전체 검증

**사용자에게 보이는 마일스톤:** 토큰 미설정 환경과 전체 테스트 스위트가 모두 통과한다.

- [ ] **Step 4.1:** 미설정 no-op 테스트.

  Run: `unset GITHUB_TOKEN OBSERVABILITY_GITHUB_OWNER OBSERVABILITY_GITHUB_PROJECT_NUMBER; uv run pytest tests/test_plan_events.py -k no_adapter -v`
  Expected: `test_emit_plan_writing_started_no_adapter` PASS

- [ ] **Step 4.2:** 전체 테스트 스위트 회귀 확인.

  Run: `uv run pytest tests/ -q`
  Expected: pre-existing 실패 수와 동일하거나 적음, 신규 실패 없음

- [ ] **Step 4.3:** secret redaction 회귀 확인.

  Run: `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q`
  Expected: 모든 redact 테스트 PASS

---

## Task 5: TEMPLATE.md 갱신 및 문서화

**파일:**
- 수정: `.agentos/project/exec-plans/TEMPLATE.md`
- 수정: `docs/observability-setup.md`

**사용자에게 보이는 마일스톤:** 새 계획 작성 시 `> user_request:` 필드가 자동으로 포함되고, `PLAN_WRITING_STARTED` 이벤트 타입이 문서에 명시된다.

- [ ] **Step 5.1:** `.agentos/project/exec-plans/TEMPLATE.md` 헤더에 `user_request` 필드 추가.

  TEMPLATE.md의 blockquote 헤더 블록(`active_agent` 줄 앞 또는 `reviewed:` 줄 바로 뒤)에 아래 줄 추가:

  ```markdown
  > user_request: <사용자 요청 요약 1-2문장 (계획 작성 시작 시점에 작성)><br>
  ```

  이 필드가 있으면 `agentos dashboard sync-plan`이 대시보드 카드 본문의 "## 사용자 요청" 섹션에 자동 반영한다.

  Run: `grep -c "user_request" .agentos/project/exec-plans/TEMPLATE.md`
  Expected: 결과 ≥ 1

- [ ] **Step 5.2:** `docs/observability-setup.md`에 신규 이벤트 타입 섹션 추가.

  기존 `PLAN_STATUS_CHANGED` 설명 옆 또는 새 섹션으로 다음을 추가:
  - `PLAN_WRITING_STARTED`: 발생 시점, payload 필드(user_request, agent, session, plan_path, plan_title), 카드 본문 구조, Status "Backlog" 자동 설정.
  - 계획 문서 헤더에 `> user_request: ...` 기록 방법.
  - 미설정 시 안전 동작(어댑터 없음 → 빈 결과 즉시 반환, 스킬 실행 차단 없음).
  - sync 실패 시 non-blocking 경고 메시지 포맷과 수동 재동기화(`agentos dashboard sync-plan <plan-path>`) 방법.
  - 명시적 비목표: Gate 2 미통과로 폐기된 계획의 대시보드 고아 카드 자동 삭제는 지원하지 않으며 사용자 수동 정리에 위임.

  Run: `grep -c "PLAN_WRITING_STARTED\|user_request" docs/observability-setup.md`
  Expected: 관련 줄 수 ≥ 2

---

## 리뷰 반영 이력
- [Gate 2 1차 / plan-reviewer=FAIL] 헤더 blockquote 6~12행 `<br>` 누락 → 모든 메타데이터 줄에 `<br>` 추가.
- [Gate 2 1차 / plan-reviewer=FAIL + principle-auditor=REVISE] Task 2 Step 2.1의 `elif payload.get("event") == "PLAN_STATUS_CHANGED": pass` 스텁 분기가 기존 구현을 덮어쓸 위험 → 스텁 완전 제거, `if ... else:` 단순 분기로 교체 및 주의 사항 명시.
- [Gate 2 1차 / principle-auditor=REVISE] Step 3.4에 `sync-manifest --update` 실행 단계 누락 → `--update && --check` 순서로 수정.
- [Gate 2 1차 / usability-reviewer=FAIL] sync 실패 시 오류 복구 안내 누락 → Task 2 Step 2.1에 non-blocking 경고 포맷 및 수동 재동기화 안내 추가, Task 5 Step 5.2 문서화에도 포함.
- [Gate 2 1차 / usability-reviewer=FAIL] Gate 2 미통과로 폐기된 계획의 대시보드 고아 카드 처리 방안 누락 → 사용자 결과 요약 "바뀌지 않는가" 항목에 명시적 비목표 선언 추가.
- [Gate 2 1차 / usability-reviewer=FAIL] TEMPLATE.md 갱신 계획 누락 → Task 5를 "TEMPLATE.md 갱신 및 문서화"로 확장하고 Step 5.1에 TEMPLATE.md 헤더 갱신 작업 추가, Durable Result Surface에 TEMPLATE.md 등록.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 아카이브 결정

(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
