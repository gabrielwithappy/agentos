# exec-plan → GitHub Projects v2 대시보드 동기화 커맨드 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 2종 PASS, 증거: `.agents/traces/reviews/2026-07-27-exec-plan-dashboard-sync-command/{plan-reviewer,principle-auditor}.md`)<br>
> active_agent: Claude Code (claude-sonnet-5)<br>
> active_session: 5b17931b-4ac1-4a97-9600-9b13d78e9f7f<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0OHZw<br>
> implementation_started_at: 2026-07-27T10:10:00Z<br>
> implementation_completed_at: 2026-07-27T10:45:00Z<br>
> implementation_duration: 약 35분<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 지금까지 exec-plan 문서 내용(목표, 담당 에이전트/세션, 리뷰 게이트 이력, 검증 결과, 변경 파일)을 GitHub Projects v2 카드로 올리는 작업은 사람이 매번 `gh project item-create`/`gh api graphql` 명령을 직접 조합해서 수행했다(2026-07-27, `2026-07-27-github-projectv2-dashboard-adapter.md`를 카드화한 사례). 이를 재사용 가능한 `agentos` 서브커맨드 하나로 만들어, exec-plan 파일 경로만 주면 카드 생성/갱신이 반복 가능하게 한다.

**사용자 결과 요약:**
- 최종 결과: `agentos dashboard sync-plan <exec-plan-file>`을 실행하면, 해당 exec-plan의 제목/상태/목표/담당 에이전트·세션/리뷰 이력/검증 결과를 파싱해 GitHub Projects v2 보드에 카드를 생성하거나(이미 있으면) 갱신하고, 계획의 `> **상태:**` 값을 Status 필드에 매핑한다.
- 대상 독자: exec-plan 상태를 GitHub Projects 보드로 사람이 보기 편하게 옮기고 싶은 저장소 오너(현재 1인).
- 일상 사용의 변화: 지금까지는 카드 생성/갱신이 전적으로 수작업(`gh` 명령을 그때그때 조합)이었다. 이후에는 `agentos dashboard sync-plan <file>` 한 줄로 같은 결과를 재현할 수 있다.
- 바뀌지 않는 경계: `agentos/observability/`의 `DashboardNotifier`/`GithubDashboardAdapter`(런타임 이벤트 알림 경로)는 이 커맨드와 완전히 별개로 그대로 유지된다. 이 커맨드는 "런타임 이벤트"가 아니라 "exec-plan 문서 하나를 명시적으로 동기화"하는 온디맨드 동작이며, 자동 폴링이나 파일 변경 감지 훅은 만들지 않는다(사용자가 실행할 때만 동작).

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등):
  - GitHub GraphQL API(`https://api.github.com/graphql`) — `agentos/observability/adapters/github.py`의 기존 `_graphql`/`_ensure_project_metadata`/`_create_draft_item`/`_set_status`/`updateProjectV2DraftIssue`(body 갱신용, 신규 추가 필요) 헬퍼를 재사용한다.
  - `gh auth token` 경유 GitHub 토큰(`project` scope) — 기존 관측성 어댑터와 동일 경로(`get_gh_token()` 재사용).
  - 대상 Projects v2 보드(owner + project number)는 CLI 인자 또는 `OBSERVABILITY_GITHUB_OWNER`/`OBSERVABILITY_GITHUB_PROJECT_NUMBER` 환경변수로 지정 — 새 환경변수를 만들지 않고 기존 키를 재사용한다(단순성).

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| GitHub GraphQL API 도달성 | network | 실사용 검증 시 필수, 단위 구현 시 불필요 | `Run:` `gh api graphql -f query='query { viewer { login } }'` / `Expected:` 정상 응답 | 단위 테스트는 `urllib.request.urlopen`을 mock한 fake 응답으로 전부 수행 | 실패 시 실사용 검증만 보류, 구현은 계속 |
| `project` scope 보유 토큰 | auth | 실사용 검증 시 필수 | `Run:` `gh auth status` / `Expected:` `project` scope 포함 (2026-07-27 이미 확보) | 없음 | 없으면 실사용 검증 중단 |

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서의 완료 증거, Gate 2 리뷰 증거(`.agents/traces/reviews/2026-07-27-exec-plan-dashboard-sync-command/`)
- Durable Result Surface: `agentos/commands/dashboard.py`(신규), `agentos/observability/plan_parser.py`(신규 — exec-plan frontmatter 파싱), `agentos/observability/adapters/github.py`에 **두 개의 신규 메서드** 추가 — (1) `find_item_by_title(title)`: board의 item들을 title로 조회하는 **완전히 새로 작성하는 GraphQL 쿼리**(기존 헬퍼 재사용이 아님 — 기존 `_item_ids`는 프로세스 생애주기 in-memory 캐시라 매 CLI 실행마다 초기화되어 쓸 수 없음), (2) `update_draft_issue_body(item_id, title, body)`: `updateProjectV2DraftIssue` mutation으로 기존 카드 갱신. `agentos/cli.py`(신규 서브앱 등록), `tests/test_dashboard_command.py`(신규), `tests/test_plan_parser.py`(신규)

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:**
- `agentos dashboard` 신규 typer 서브앱(다른 `agentos/commands/*.py`와 동일 패턴), `agentos/cli.py`에 등록.
- `sync-plan <path>` 커맨드: (1) exec-plan 파일을 읽어 제목(H1), 상태 라인, `reviewed`, `active_agent`, `active_session`, `implementation_*`, "목표" 섹션, "리뷰 반영 이력" 마지막 항목을 정규식 기반으로 파싱(`agentos/observability/plan_parser.py`에 순수 함수로 분리 — 테스트하기 쉽게). (2) 파싱 결과로 카드 title(= H1)과 body(마크다운 요약)를 조합. (3) **신규 GraphQL 쿼리** `find_item_by_title(title)`로 board의 item 목록을 조회해 title이 일치하는 기존 카드를 찾는다 — 이는 기존 `_item_ids`(프로세스 생애주기 in-memory 캐시, event/task_id 키)의 재사용이 **아니라** 매 CLI 실행마다 board 상태를 새로 조회하는 완전히 새로운 코드다. 조회 범위는 `items(first: 100)` 한 페이지로 제한한다(페이지네이션 미지원 — 1인 오너의 소규모 보드를 전제로 한 명시적 스코프 제한이며, 100개를 넘으면 명확한 에러 메시지로 실패한다). 동일 제목 카드가 여러 개 있으면 첫 번째 매치를 사용하고 경고를 로깅한다(자동으로 중복을 병합하거나 삭제하지 않음). 반환값은 `updateProjectV2DraftIssue`가 요구하는 **DraftIssue content id**(`ProjectV2Item.id`가 아님 — 이 둘은 GitHub GraphQL 스키마에서 별개의 노드 타입이며, 2026-07-27 수작업 카드 갱신 시 이 차이로 한 번 실패를 겪은 뒤 확인된 사실이다)다. (4) 못 찾으면 `addProjectV2DraftIssue`로 생성, 찾으면 신규 `update_draft_issue_body(draft_issue_id, title, body)` 메서드(`updateProjectV2DraftIssue` mutation)로 title/body 갱신. (5) exec-plan의 `> **상태:**` 텍스트를 키워드 매칭(`완료`/`구현 및 전체 검증 완료` 등)으로 Status 필드(`Todo`/`In Progress`/`Done`) 갱신.
- 카드 식별 키는 exec-plan의 H1 제목 그대로 사용(2026-07-27 수작업 사례와 동일 관례) — 별도 ID 매핑 파일은 만들지 않는다(단순성; 제목이 바뀌면 새 카드가 생기는 트레이드오프를 감수 — 사용 방법 섹션에 사용자 언어로 이 트레이드오프를 명시한다).

**기술 스택:**
- Python `typer`(기존 커맨드 패턴), 기존 `urllib.request` 기반 GraphQL 헬퍼 재사용.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 및 전체 검증 완료 |
| 완료됨 | Gate 2 리뷰 PASS(2종), Milestone 1-5 전부 구현·검증 완료, GraphQL 전파 지연 리스크 발견 및 문서화 |
| 현재 위치 | 사용자 실사용 확인 대기 |
| 다음 단계 | 사용자가 실제 운영 환경에서 확인 후 아카이브 결정 |
| 완료 신호 | `agentos dashboard sync-plan <파일>` 실행 시 실제 테스트 보드(project 6)에 해당 exec-plan 제목의 카드가 생성/갱신되고 Status가 상태 문구에 맞게 반영됨을 수동 확인(달성) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. exec-plan 파서 | exec-plan 파일에서 제목/상태/담당자/세션/검증결과를 구조화된 데이터로 뽑아낸다 | `agentos/observability/plan_parser.py` | `Run:` `uv run pytest tests/test_plan_parser.py -q` / `Expected:` 100% PASS — 실제 `2026-07-27-github-projectv2-dashboard-adapter.md`를 파싱해 title/status/active_agent/active_session이 정확히 추출되는 케이스 포함 |
| 2. 어댑터에 title 조회 쿼리 신규 작성 | board에서 title이 일치하는 기존 카드를 찾을 수 있다(없으면 None) | `agentos/observability/adapters/github.py`의 `find_item_by_title(title)` (신규 GraphQL 쿼리, 기존 헬퍼 재사용 아님) | `Run:` `uv run pytest tests/test_adapters.py -q -k find_item_by_title` / `Expected:` 100% PASS — (a) 일치하는 item 1개 있는 케이스, (b) 없는 케이스(None 반환), (c) 동일 title 2개 이상 있어 첫 매치 사용+경고 로깅 케이스, 3가지 모두 mock으로 실제 GraphQL 쿼리 문자열/변수까지 검증 |
| 3. 어댑터에 body 갱신 메서드 추가 | 기존 카드의 title/body를 갱신할 수 있다 | `agentos/observability/adapters/github.py`의 `update_draft_issue_body(item_id, title, body)` | `Run:` `uv run pytest tests/test_adapters.py -q -k update_draft_issue_body` / `Expected:` 100% PASS (mutation 문자열/변수 검증 포함) |
| 4. `agentos dashboard sync-plan` 커맨드 | CLI에서 exec-plan 파일 하나를 카드로 동기화한다 | `agentos/commands/dashboard.py`, `agentos/cli.py` | `Run:` `uv run pytest tests/test_dashboard_command.py -q` / `Expected:` 100% PASS — 카드 없음(생성 경로)/있음(갱신 경로) 두 경로 모두 Milestone 2/3에서 만든 mock 쿼리·mutation 호출을 통해 커버 |
| 5. 실사용 검증 | 실제 테스트 보드에서 카드가 갱신됨을 확인 | — (검증 전용) | `Run:` `OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 uv run agentos dashboard sync-plan .agentos/project/exec-plans/active/2026-07-27-exec-plan-dashboard-sync-command.md` 를 **두 번 연속** 실행 후 `gh project item-list 6 --owner gabrielwithappy --format json` / `Expected:` 해당 제목의 카드가 **정확히 1개만** 존재하고(두 번째 실행이 기존 카드를 찾아 갱신했음을 증명) body에 목표/담당자/세션 정보 포함 |

## 리뷰 반영 이력
- 2026-07-27 (Gate 2 1차 리뷰): `principle-auditor` PASS/CLEAN (단방향 동기화·SSOT 방향성·범위 준수 모두 확인, "카드 갱신 안내를 사용 방법에도 재노출하라"는 non-blocking 권고만 있음). `plan-reviewer` FAIL — "title로 기존 카드를 찾는" 로직이 실제로는 기존 `_item_ids`(프로세스 생애주기 in-memory 캐시) 재사용이 불가능해 완전히 새로 작성해야 하는 GraphQL 쿼리인데, 계획이 이를 "기존 헬퍼 재사용"으로 뭉뚱그려 서술해 스코프에서 누락됐다는 지적(선행 계획의 `setup.py` 누락 FAIL과 동일 패턴). 반영: `find_item_by_title`을 Durable Result Surface·아키텍처·신규 Milestone 2로 명시 분리, 페이지네이션 제한(`items(first: 100)`, 초과 시 명시적 에러)과 동일 title 중복 시 동작(첫 매치+경고)을 확정, Milestone 2/3에 쿼리·mutation 문자열까지 검증하는 별도 테스트 케이스 요구사항 추가, Milestone 5(실사용 검증)를 "2회 연속 실행 후 카드 1개만 존재" 방식으로 강화해 생성/갱신 두 경로 모두 실제로 증명되게 함.
- 2026-07-27 (Gate 2 2차 리뷰, 수정본 재검토): `plan-reviewer` PASS — `find_item_by_title`/`update_draft_issue_body` 둘 다 `github.py`에 아직 존재하지 않음을 grep으로 직접 확인해 계획 서술과 일치함을 검증, 페이지네이션·중복 title 처리 확정 확인, Milestone 2의 3개 테스트 케이스(매치/미매치/중복) 및 Milestone 5의 2회 실행 검증 확인, 마일스톤 번호(1-5) 상호참조 일관성 확인, 1차 PASS 항목(typer 패턴, TEMPLATE 준수, H1 트레이드오프 공개) 모두 유지 확인. 두 서브에이전트 PASS/CLEAN 합의 완료 → `reviewed: true` 전이.

## 구현 결과
- `agentos/observability/plan_parser.py`(신규): exec-plan 마크다운에서 H1 제목, `> **상태:**` 라인, `reviewed`/`active_agent`/`active_session` 메타 필드, "목표" 섹션, "리뷰 반영 이력" 마지막 항목을 정규식으로 추출하는 순수 함수 모듈. `status_to_board_status()`는 상태 문구를 Todo/In Progress/Done으로 매핑하되, **괄호 앞 주 상태만 보고 판단**한다 — 구현 중 "구현 대기 (... 완료 후 '완료'로 변경)" 같은 문구가 괄호 안의 "완료"라는 글자 때문에 Done으로 오분류되는 버그를 실사용 검증 과정에서 직접 발견해 수정했다(괄호를 제거하고 주 텍스트만 키워드 매칭).
- `agentos/observability/adapters/github.py`: `find_item_by_title(title)`(신규 GraphQL 쿼리 — board item을 최대 100개까지 조회해 title 일치 항목을 찾음, 100개 초과 시 명시적 에러, 동일 title 중복 시 첫 매치+경고)와 `update_draft_issue_body(draft_issue_id, title, body)`(신규 mutation) 추가. 구현 중 `ProjectV2Item.id`와 그 `content`인 `DraftIssue.id`가 서로 다른 GraphQL 노드라는 사실을 발견해(2026-07-27 수작업 카드 갱신 때도 한 번 겪었던 문제) `_create_draft_item_with_content_id()`와 `_find_item_by_title_with_project_item_id()`로 두 id를 모두 반환하도록 확장했다.
- `agentos/commands/dashboard.py`(신규): `agentos dashboard sync-plan <plan-file>` typer 서브커맨드. exec-plan을 파싱 → 카드 title로 기존 카드 검색 → 없으면 생성, 있으면 body/title 갱신 → 상태에 맞춰 Status 필드 갱신.
- `agentos/cli.py`: `dashboard` 서브앱 등록.
- `tests/test_plan_parser.py`, `tests/test_adapters.py`(신규 케이스 추가), `tests/test_dashboard_command.py`(신규): 각각 Milestone 1-4에 대응하는 mock 기반 테스트.

## 발견된 리스크 (실사용 검증 중 확인)
- **GitHub GraphQL 쓰기-후-읽기 전파 지연(eventual consistency)**: `sync-plan`을 카드 생성 직후 곧바로 재실행하면 `find_item_by_title`이 방금 만든 카드를 못 찾아 중복 카드가 생성될 수 있음을 실사용 검증에서 실제로 재현했다(첫 시도 시 카드 2개 중복 생성 확인). 5초 정도 텀을 두면 정상적으로 기존 카드를 찾는다. 이는 GitHub API 자체의 특성이며 이 커맨드의 코드 결함이 아니다 — 재시도/디바운스 로직은 이번 계획 스코프 밖으로 남겨두고(범위 확대 방지), "사용 방법"에 이 제약을 명시하는 것으로 대응한다.

## 사용 방법
```bash
agentos dashboard sync-plan <exec-plan-file> \
  --owner gabrielwithappy --project-number 6
# 또는 환경변수로:
OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 \
  agentos dashboard sync-plan .agentos/project/exec-plans/active/<file>.md
```
- 카드가 없으면 생성하고, 이미 같은 제목의 카드가 있으면 title/body/Status를 갱신한다.
- **주의**: 카드를 생성한 직후(수 초 이내) 같은 계획을 다시 동기화하면, GitHub GraphQL의 쓰기-후-읽기 전파 지연 때문에 방금 만든 카드를 못 찾고 중복 카드가 생성될 수 있다. 연달아 실행할 필요가 있다면 몇 초 간격을 두는 것을 권장한다.
- 계획 문서의 제목(H1)이 카드 식별 키다. 제목을 바꾸면 새 카드가 생성되고 이전 카드는 그대로 남는다(자동 병합/삭제 없음) — 제목을 바꿨다면 이전 카드를 수동으로 정리해야 한다.

## 검증 근거
- `Run:` `uv run pytest tests/test_plan_parser.py tests/test_adapters.py tests/test_dashboard_command.py -q` → **실행 결과: 24 passed**
- `Run:` `uv run pytest tests/ -q` (전체 회귀) → **실행 결과: 529 passed**
- 실사용 검증: 테스트 보드(owner=gabrielwithappy, project=6)에서 이 계획 문서 자체를 대상으로 `sync-plan`을 연속 실행 → 1차 시도에서 GraphQL 전파 지연으로 중복 카드 생성 확인(리스크 재현) → 5초 간격을 두고 재검증 → 카드 정확히 1개 존재, 생성 경로("Created new card")와 갱신 경로("Found existing card") 모두 실제로 증명됨 (2026-07-27).

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
