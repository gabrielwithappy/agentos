# GitHub Projects v2(GraphQL) 대시보드 어댑터 교체 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 2종 PASS, 증거: `.agents/traces/reviews/2026-07-27-github-projectv2-dashboard-adapter/{plan-reviewer,principle-auditor}.md`)<br>
> active_agent: Claude Code (claude-sonnet-5)<br>
> active_session: 5b17931b-4ac1-4a97-9600-9b13d78e9f7f<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0OQ0U<br>
> implementation_started_at: 2026-07-27T09:30:00Z<br>
> implementation_completed_at: 2026-07-27T09:55:00Z<br>
> implementation_duration: 약 25분<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 기존 `GithubDashboardAdapter`(REST `/repos/{repo}/projects/{project_id}/columns`, Classic Projects API)는 GitHub이 신규 계정/리포에서 Classic Projects REST 엔드포인트를 은퇴시켜 실제로 404로 실패한다(2026-07-27 수동 검증: `gh api repos/gabrielwithappy/agentos/projects` → 404, `has_projects: true`인데도 재현). 사용자가 지금 실제로 쓰는 **GitHub Projects v2**(GraphQL 전용)를 대상으로 어댑터를 재작성해, `OBSERVABILITY_ENABLED=1` 알림 흐름이 실제로 카드 상태를 반영하게 만든다.

**사용자 결과 요약:**
- 최종 결과: `OBSERVABILITY_ENABLED=1` + Projects v2 보드 설정을 마치면, `notify_lifecycle_event`가 발생할 때마다 대상 Project 보드에 해당 이벤트의 draft item이 생성되거나 기존 item의 Status가 갱신된다. 지금처럼 API가 404로 조용히 실패하는 대신 실제로 보드에 반영된다.
- 대상 독자: `OBSERVABILITY_ENABLED=1`을 켜고 GitHub Projects로 AgentOS 실행 상태를 보고 싶은 사용자(현재는 저장소 오너 1인).
- 일상 사용의 변화: `.env` 설정 키가 `OBSERVABILITY_GITHUB_REPO`/`OBSERVABILITY_GITHUB_PROJECT_ID`(Classic, `owner/repo` + 숫자 project id)에서 `OBSERVABILITY_GITHUB_OWNER`/`OBSERVABILITY_GITHUB_PROJECT_NUMBER`(Projects v2, owner login + 프로젝트 번호)로 바뀐다. 대화형 마법사(`setup_observability()`)의 질문 문구와 `.env` 기록 키도 함께 바뀐다. `docs/observability-setup.md`도 이에 맞춰 갱신한다.
- 바뀌지 않는 경계: `DashboardNotifier`(fire-and-forget, 예외 흡수) 구조, `notify_lifecycle_event` 호출부(`agentos/terminal/hooks.py`), 에러 발생 시 메인 프로세스가 절대 중단되지 않는다는 보장, `OBSERVABILITY_ENABLED` 토글 방식.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등):
  - GitHub GraphQL API(`https://api.github.com/graphql`) — Projects v2 mutation(`addProjectV2DraftIssue`, `updateProjectV2ItemFieldValue`) 및 query(`node(id:)`로 필드/옵션 조회).
  - `gh auth token`이 제공하는 토�큰에 `project` scope 필요(Classic 때와 동일하게 `gh auth refresh -s project`로 사용자가 이미 확보함, 2026-07-27 확인 완료).
  - 실사용 검증에는 실제 Projects v2 보드(테스트용으로 `gabrielwithappy/AgentOS Dashboard Test`, project number `6`, node id `PVT_kwHOBiJEFc4Bek_E`를 이미 생성해 둠)가 필요.

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| GitHub GraphQL API 도달성 | network | 실사용 검증 시 필수, 단위 구현 시 불필요 | `Run:` `gh api graphql -f query='query { viewer { login } }'` / `Expected:` `{"data":{"viewer":{"login":"..."}}}` 형태의 정상 응답 | 구현·단위 테스트는 `urllib.request.urlopen`을 mock한 fake 응답으로 전부 수행 | 실패 시 실사용 검증 단계만 `NEEDS_CONTEXT`로 보류, 구현은 계속 진행 |
| `project` scope 보유 토큰 | auth | 실사용 검증 시 필수 | `Run:` `gh auth status` / `Expected:` `Token scopes` 목록에 `project` 포함 (2026-07-27 이미 확인됨) | 없음 — 이미 충족 | 스코프 없으면 실사용 검증 중단, 사용자에게 `gh auth refresh -s project` 안내 |

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서의 완료 증거, Gate 2 리뷰 증거 파일(`.agents/traces/reviews/2026-07-27-github-projectv2-dashboard-adapter/`)
- Durable Result Surface: `agentos/observability/adapters/github.py`(재작성), `agentos/observability/setup.py`(실제 프로덕션 조립 지점 — env var 이름·마법사 문구·`.env` 기록 키·생성자 호출을 모두 새 시그니처에 맞춰 갱신. plan-reviewer가 2026-07-27 1차 리뷰에서 이 파일 누락을 FAIL 사유로 지적해 추가함), `tests/test_adapters.py`(GraphQL mock으로 갱신), `tests/test_notifier.py`(setup_observability 관련 테스트가 있다면 새 env var로 갱신), `docs/observability-setup.md`(Projects v2 설정 안내로 갱신)

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:**
- `DashboardAdapter` 프로토콜(`send_notification(payload)`)은 그대로 유지. `GithubDashboardAdapter` 내부 구현만 REST Classic 호출 → GraphQL v2 mutation 호출로 교체.
- item 매핑 전략: payload의 `event`(및 선택적 `task_id`)를 키로 삼아 "해당 이벤트에 대응하는 item이 보드에 없으면 `addProjectV2DraftIssue`로 draft item을 새로 만들고, 있으면 그 item의 Status 필드를 갱신"한다. item 존재 여부 추적은 어댑터 인스턴스 내 in-memory dict(`event/task_id → item_id`)로 충분 — 프로세스 재시작 시 초기화되어도 새 draft item이 다시 생성될 뿐이라 데이터 유실이 아니다(단순성 우선, 영속 캐시는 만들지 않는다).
- Status 필드/옵션 id는 매 호출 시 조회하지 않고, 어댑터 생성 시 1회 `node(id: $projectId) { ... fields ... }` 쿼리로 캐싱한다.

**기술 스택:**
- Python `urllib.request`(기존 방식 유지, 신규 의존성 추가 없음), GitHub GraphQL API v4.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 및 전체 검증 완료 |
| 완료됨 | Gate 2 리뷰 PASS(2종), Milestone 1-5 전부 구현·검증 완료 |
| 현재 위치 | 사용자 실사용 확인 대기 |
| 다음 단계 | 사용자가 실제 운영 환경에서 확인 후 아카이브 결정 |
| 완료 신호 | `tests/test_adapters.py`가 GraphQL mutation 호출 형태를 검증하며 100% PASS(달성), 실제 테스트 보드(`PVT_kwHOBiJEFc4Bek_E`)에 draft item이 생성되고 Status가 갱신됨을 수동 확인(달성) |

### event → Status 매핑 (확정)

`notify_lifecycle_event`가 실제로 보내는 event 종류(`agentos/terminal/hooks.py` 및 호출부 기준)를 Status 옵션에 고정 매핑한다. 모르는 event는 항상 `Todo`로 폴백한다(경고 없이 — 미지의 event는 정상적인 신규 이벤트일 수 있어 경고를 남발하지 않는다):

| event | Status |
|---|---|
| `CLI_INTERRUPT`, `TASK_BLOCKED`, 예외 발생 계열 | `Todo` (사람 개입 필요 신호) |
| `TASK_STATE_CHANGED`(진행 중) | `In Progress` |
| `TASK_COMPLETED` | `Done` |
| 그 외 알 수 없는 event | `Todo` (기본 폴백) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. GraphQL 어댑터 재작성 | `notify_lifecycle_event` 호출 시 Classic REST 404 대신 GraphQL mutation이 나간다 | `agentos/observability/adapters/github.py` | `Run:` `uv run pytest tests/test_adapters.py -q` / `Expected:` 100% PASS, mock된 `urlopen` 호출 URL이 `https://api.github.com/graphql`이고 body에 `addProjectV2DraftIssue` 또는 `updateProjectV2ItemFieldValue` mutation 포함. GraphQL 응답이 HTTP 200이면서 body에 `"errors"` 키가 있는 case(partial failure)도 테스트로 커버 — 이 경우 예외를 던지지 않고 `DashboardNotifier._safe_send`가 잡을 수 있는 예외를 명시적으로 발생시켜 경고로만 남긴다 |
| 2. Status 필드 매핑 | event 종류에 따라 보드의 Status 컬럼이 위 매핑표대로 바뀐다 | `agentos/observability/adapters/github.py`(필드 캐싱 로직) | `Run:` `uv run pytest tests/test_adapters.py -q -k status_mapping` / `Expected:` PASS — 매핑표의 4개 케이스(Todo/In Progress/Done/알 수 없는 event→Todo 폴백) 각각 검증, 매핑 실패해도 예외 없이 경고만 |
| 3. 프로덕션 조립 지점 갱신 | `setup_observability()`가 새 env var(`OBSERVABILITY_GITHUB_OWNER`, `OBSERVABILITY_GITHUB_PROJECT_NUMBER`)를 읽고 마법사 질문 문구·`.env` 기록 키도 이에 맞춰 바뀐다. 기존 `OBSERVABILITY_GITHUB_REPO`/`OBSERVABILITY_GITHUB_PROJECT_ID`는 완전히 대체(하위호환 유지 안 함 — 사용자 1인 환경, 레거시 부담보다 단순성 우선) | `agentos/observability/setup.py` | `Run:` `uv run pytest tests/test_notifier.py tests/test_adapters.py -q` / `Expected:` 100% PASS. 수동: `OBSERVABILITY_GITHUB_OWNER`/`OBSERVABILITY_GITHUB_PROJECT_NUMBER` 미설정 + TTY 환경에서 `agentos doctor` 실행 시 마법사가 새 키 이름으로 질문하는지 육안 확인 |
| 4. 설정 가이드 갱신 | `docs/observability-setup.md`가 `OBSERVABILITY_GITHUB_PROJECT_ID` 대신 Projects v2용 키(`OBSERVABILITY_GITHUB_PROJECT_NUMBER`, `OBSERVABILITY_GITHUB_OWNER`)를 안내 | `docs/observability-setup.md` | 사람이 읽고 확인 (문서 변경, 자동 검증 없음) |
| 5. 실사용 검증 | 실제 테스트 보드에 draft item이 뜨고 Status가 바뀜을 확인 | — (검증 전용, 코드 변경 없음) | `Run:` `OBSERVABILITY_ENABLED=1 OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 agentos doctor` 후 `gh project item-list 6 --owner gabrielwithappy` / `Expected:` 새 item 1건 이상 등장, Status가 매핑표대로 설정됨 |

## 리뷰 반영 이력
- 2026-07-27 (Gate 2 1차 리뷰): `principle-auditor` PASS/CLEAN (단순성·신뢰성·범위 모두 적절, GraphQL partial-failure 처리는 non-blocking 권고). `plan-reviewer` FAIL — 실제 프로덕션 조립 지점인 `agentos/observability/setup.py`(env var 이름, 마법사 문구, `.env` 기록 키, 생성자 호출)가 스코프에서 완전히 누락되어 Milestone 4(구 번호) 검증이 성립 불가능하다는 지적. 반영: `setup.py`를 Durable Result Surface와 신규 Milestone 3으로 명시 추가, event→Status 매핑표를 확정해 모호성 제거, GraphQL partial-failure(200+errors) 테스트 케이스를 Milestone 1 검증에 추가.
- 2026-07-27 (Gate 2 2차 리뷰, 수정본 재검토): `plan-reviewer` PASS — `setup.py` 스코프/마일스톤/검증 명령 반영 확인(`setup.py` 실제 코드를 직접 읽고 계획의 서술과 일치함을 독립 검증), 매핑표 구체화 확인, 마일스톤 번호·상호참조 일관성 확인. 두 서브에이전트 PASS/CLEAN 합의 완료 → `reviewed: true` 전이.

## 구현 결과
- `agentos/observability/adapters/github.py`: Classic REST 호출을 완전히 제거하고 GraphQL 기반으로 재작성. 프로젝트/Status 필드 메타데이터는 어댑터 인스턴스 생애주기 동안 1회만 조회해 캐싱. event별 Status 매핑표(`_STATUS_BY_EVENT`)를 코드에 그대로 반영, 미지의 event는 `Todo`로 폴백. `event/task_id → item_id` in-memory dict로 같은 task에 대한 반복 이벤트는 새 item을 만들지 않고 기존 item의 Status만 갱신. GraphQL이 HTTP 200 + `errors` 필드로 partial failure를 반환하는 경우를 명시적으로 감지해 `ValueError`를 던지고, 이는 `DashboardNotifier._safe_send`가 잡아 경고 로깅만 하도록 기존 안전장치를 그대로 활용.
- `agentos/observability/setup.py`: env var를 `OBSERVABILITY_GITHUB_REPO`/`OBSERVABILITY_GITHUB_PROJECT_ID`에서 `OBSERVABILITY_GITHUB_OWNER`/`OBSERVABILITY_GITHUB_PROJECT_NUMBER`로 전면 교체(하위호환 유지 안 함, 계획대로). 대화형 마법사 문구도 Projects v2 기준으로 갱신.
- `tests/test_adapters.py`: GraphQL mock 기반으로 전면 재작성. draft item 생성+Status 갱신 흐름, 4가지 event→Status 매핑 케이스, 동일 task 재사용 시 item 재생성 안 함, GraphQL partial-failure 시 예외 발생, 설정 불완전 시 API 호출 자체를 건너뜀 — 총 5개 시나리오 커버.
- `docs/observability-setup.md`: Projects v2 전용 안내로 갱신 (owner/project number, `gh auth refresh -s project` 안내, Status 옵션 요구사항 명시).

## 사용 방법
```bash
# 1. project scope 확보 (최초 1회)
gh auth refresh -s project --hostname github.com

# 2. 환경변수 설정 (또는 .env 파일에 기록)
export OBSERVABILITY_ENABLED=1
export OBSERVABILITY_GITHUB_OWNER="gabrielwithappy"
export OBSERVABILITY_GITHUB_PROJECT_NUMBER="6"

# 3. agentos 실행 — TTY 환경에서 위 두 값이 비어 있으면 마법사가 물어보고 .env에 저장
agentos run
```
대상 Projects v2 보드에 `Status`(단일 선택) 필드가 있고 `Todo`/`In Progress`/`Done` 옵션이 있으면, CLI 인터럽트/상태 변경/완료 등 이벤트가 발생할 때마다 보드에 draft item이 생성되거나 기존 item의 Status가 자동 갱신된다.

## 검증 근거
- `Run:` `uv run pytest tests/test_adapters.py tests/test_notifier.py -q` → `Expected:` 100% PASS → **실행 결과: 10 passed**.
- `Run:` `uv run pytest tests/ -q` (전체 회귀) → **실행 결과: 513 passed**.
- 실사용 검증: 테스트 보드(`gabrielwithappy` owner, project number `6`, node id `PVT_kwHOBiJEFc4Bek_E`)에 대해 `OBSERVABILITY_ENABLED=1 OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6`로 `notify_lifecycle_event("CLI_INTERRUPT", ...)`를 직접 트리거 → `gh project item-list 6 --owner gabrielwithappy --format json` 결과 `{"title":"CLI_INTERRUPT","status":"Todo"}` draft item 1건 생성 확인 (2026-07-27).

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
