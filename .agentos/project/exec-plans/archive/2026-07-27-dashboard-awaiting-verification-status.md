# GitHub 대시보드 Status에 "Awaiting Verification" 5단계 추가 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 3종 PASS, 증거: `.agents/traces/reviews/2026-07-27-dashboard-awaiting-verification-status/{plan-reviewer,principle-auditor,usability-reviewer}.md`)<br>
> active_agent: Claude Code (claude-sonnet-5)<br>
> active_session: <br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0O9jA<br>
> implementation_started_at: 2026-07-27T22:30:00Z<br>
> implementation_completed_at: 2026-07-27T23:10:00Z<br>
> implementation_duration: 약 40분<br>

> **usability_review_required:** true<br>
> usability_review_reason: `agentos dashboard sync-plan` 콘솔 출력 문구와 GitHub Projects 보드 UI에 사용자가 직접 보는 Status 컬럼 구성(옵션 이름·개수)을 다시 바꾼다.<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `status_to_board_status()`(4단계: Backlog/Ready/In Progress/Done)는 "에이전트가 아직 코드를 작성 중인 계획"과 "코드·자동 테스트는 다 끝났고 사용자의 수동 확인(브라우저 로그인, 실제 보드 조회 등)만 남은 계획"을 똑같이 **In Progress**로 뭉뚱그린다. 그 결과 GitHub 대시보드만 봐서는 "지금 내가 뭘 해야 하는지"(에이전트 작업 대기 vs 내 확인 필요)가 구분되지 않는다(2026-07-27 대화, Claude OAuth provider 계획이 실사례로 지적됨). Status 컬럼에 5번째 단계 **Awaiting Verification**을 추가하고, 자동 검증까지 끝났지만 사람의 수동 확인만 남은 계획을 In Progress와 분리해 표시한다.

**사용자 결과 요약:**
- 최종 결과: `agentos dashboard sync-plan`(단일/--all)이 계획 문서의 상태 문구에 "사용자 실사용 확인 대기"가 포함되어 있으면(그리고 `reviewed: true`이고 "완료"로 시작하지 않으면) 카드 Status를 In Progress가 아니라 **Awaiting Verification**으로 반영한다.
- 대상 독자: GitHub Projects 보드를 보고 "지금 내가 확인해야 할 게 있는지"를 빠르게 파악하고 싶은 저장소 오너(1인 오너).
- 일상 사용의 변화: 지금까지는 "에이전트가 구현 중"과 "내 확인만 남음"이 둘 다 In Progress 카드로 보여서 매번 카드 본문을 열어 상태 문구를 읽어야 구분됐다. 이후에는 보드 컬럼만 봐도 Awaiting Verification 컬럼에 있는 카드는 "내가 확인할 차례"임을 바로 알 수 있다.
- 바뀌지 않는 경계: `sync-plan`/`sync-plan --all`의 커맨드 인터페이스, exec-plan 파일 구조(새 필드 추가 없이 기존 `> **상태:**`/`reviewed`만 재해석), 카드 식별 키(H1 제목), Backlog/Ready/Done 3단계의 판단 조건, 런타임 이벤트 알림 경로(`GithubDashboardAdapter._STATUS_BY_EVENT`, Todo 옵션)는 이번 계획과 무관하게 그대로 유지.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등):
  - GitHub Projects v2 보드의 Status 필드 옵션을 기존 5개(Todo/Backlog/Ready/In Progress/Done)에서 6개(+ Awaiting Verification)로 늘려야 한다. 이는 코드가 아니라 GitHub 쪽 설정 변경이며 `gh api graphql`의 `updateProjectV2Field` mutation 또는 웹 UI로 1회 수행한다.
  - 선행 계획(`2026-07-27-dashboard-4stage-status-mapping.md`)에서 이미 문서화된 리스크: `updateProjectV2Field`로 옵션을 추가하면 기존 카드 Status가 일시적으로 초기화되며, `sync-plan --all` 재실행으로 복구된다. 이번에도 동일 현상이 재현될 것으로 예상하고 문서에 재확인만 한다(새로운 리스크 아님).

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| 대상 보드 Status 필드에 6번째 옵션 추가 권한 | auth/permission | 실사용 검증 시 필수 | `Run:` `gh project field-list 6 --owner gabrielwithappy` / `Expected:` Status 필드가 조회되고 이후 옵션 추가 mutation이 에러 없이 성공 | 단위 테스트는 6개 옵션이 이미 있다고 가정한 mock으로 전부 수행 | 실패 시 실사용 검증만 보류, 코드 구현은 계속 |

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서의 완료 증거, Gate 2 리뷰 증거(`.agents/traces/reviews/2026-07-27-dashboard-awaiting-verification-status/`)
- Durable Result Surface: `agentos/observability/plan_parser.py`(`status_to_board_status` 5단계 판단 순서로 교체), `docs/observability-setup.md`(Status 옵션 요구사항 갱신), `tests/test_plan_parser.py`(신규 매핑 케이스)

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:**
- 판별 신호: 저장소 전수 조사 결과(2026-07-27, plan-reviewer 1차 리뷰에서 재검증), 자동화 불가 수동 확인만 남은 계획은 예외 없이 **`> **상태:**` 메타 라인**에 정확한 부분 문자열 `"사용자 실사용 확인 대기"`를 포함한다. 상태 라인 기준으로 재확인하면 active 6개 파일 중 이 문구를 가진 파일은 정확히 5개(이 계획 자신은 제외 — 이 계획의 `> **상태:**`는 "리뷰 대기 (완료 후 '완료'로 변경)"이고, 본문 프로즈에는 이 문구가 등장하지만 상태 라인에는 없음), archive 41개 중 0개다. **주의**: `grep -l "사용자 실사용 확인 대기" .agentos/project/exec-plans/active/*.md`(파일 전체 검색)를 그대로 실행하면 이 계획 문서 자신도 본문 프로즈에 이 문구가 등장하므로 6개가 매칭된다 — 이는 상태 라인 기준 5개 주장과 모순되지 않는다(검색 범위가 다를 뿐). 상태 라인만 검색하려면 `grep "^> \*\*상태:\*\*" .agentos/project/exec-plans/active/*.md | grep "사용자 실사용 확인 대기"`를 사용해야 정확히 5개가 나온다. 이 문자열이 없는 "완료"류/"구현 완료"류 문구는 기존 규칙대로 처리한다. 이 신호는 계획 작성자가 자율적으로 붙이는 관용구이며 강제되는 스키마 필드가 아니므로, 이 계획은 새 문구를 표준으로 확정하고 TEMPLATE.md에도 반영해 향후 계획들이 일관되게 이 문구를 쓰도록 유도한다(아래 Task 3 참고).
- **5단계 판단 순서** (기존 4단계 순서 중 In Progress 갈래만 세분화, 나머지 3개 조건은 무변경):
  1. 주 상태 문구(괄호 앞)가 "완료"로 시작 → **Done**.
  2. 그 외 `reviewed`가 true가 아님 → **Backlog**.
  3. `reviewed`가 true이고 주 상태 문구에 "완료"가 없음 → **Ready**.
  4. `reviewed`가 true이고 "완료"가 주 상태 문구에 있지만 "완료"로 시작하지 않고, 상태 문구 전체(괄호 포함)에 `"사용자 실사용 확인 대기"`가 포함됨 → **Awaiting Verification**(신설).
  5. 나머지(위 4번 조건에서 그 문구가 없는 경우, 예: "구현 완료") → **In Progress**.
- `status_to_board_status()`의 반환 타입(문자열)과 시그니처(`status_text: str, reviewed: str`)는 변경하지 않는다 — 새 반환값 `"Awaiting Verification"`만 추가.
- **기존 Status 옵션과의 관계**: 런타임 이벤트 알림 경로는 이번 계획과 무관하게 그대로 유지한다(선행 계획과 동일한 경계). 보드 Status 옵션은 최종 6개(Todo/Backlog/Ready/In Progress/Awaiting Verification/Done)가 되며, Todo는 런타임 이벤트 전용, 나머지 5개는 exec-plan 동기화 전용이라는 기존 용도 분리가 그대로 확장된다.
- `agentos/commands/dashboard.py`의 `_sync_one()`은 `status_to_board_status()`가 반환한 문자열을 그대로 `adapter._status_option_ids`에서 조회하는 기존 로직을 재사용하므로, 옵션이 보드에 없을 때의 경고 처리(선행 계획에서 이미 구현됨)는 수정 없이 새 반환값에도 그대로 적용된다 — 코드 변경 불필요, 회귀 테스트로만 확인.

**기술 스택:**
- 기존 `agentos/observability/plan_parser.py`, GitHub Projects v2 GraphQL(옵션 추가는 코드가 아니라 `gh`/웹 UI로 1회 수행).

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Task 1-4 구현·검증·실사용 확인 완료 |
| 완료됨 | Gate 2 리뷰 3종 PASS, Task 1-4 구현, 전체 테스트 스위트 538 passed(회귀 없음), 보드 옵션 6종 추가, 실사용 sync-plan --all로 5개 카드 정확히 반영 확인 |
| 현재 위치 | 완료 |
| 다음 단계 | 없음(아카이브 결정 대기) |
| 완료 신호 | 아래 Task별 `Run`/`Expected` 전부 PASS(확인됨) + 전체 테스트 스위트 회귀 없음(확인됨) + 실제 테스트 보드에서 active 계획을 `sync-plan --all`로 동기화했을 때 "사용자 실사용 확인 대기" 문구를 가진 4개 계획이 Awaiting Verification으로, 이 계획 자신이 Ready로 정확히 분류됨(확인됨) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 5단계 매핑 함수 확장 | "사용자 실사용 확인 대기" 문구가 포함된 계획만 Awaiting Verification으로, 나머지는 기존 4단계 규칙 그대로 매핑된다 | `agentos/observability/plan_parser.py`의 `status_to_board_status()` | `Run:` `uv run pytest tests/test_plan_parser.py -q -k board_status` / `Expected:` PASS — 기존 8종류 조합(Backlog/Ready/In Progress/Done)이 회귀 없이 그대로 유지되고, 신규로 현재 active 5개 계획의 실제 상태 문구(`"구현 및 전체 검증 완료 (사용자 실사용 확인 대기)"`)가 Awaiting Verification으로, 문구는 있지만 `reviewed: false`인 가상 케이스는 Backlog로(우선순위 확인), "구현 완료"처럼 해당 문구가 없는 in-progress 케이스는 기존대로 In Progress로 매핑되는지 검증 |
| 2. 보드 Status 옵션 추가 | 대상 보드에 Awaiting Verification 옵션이 새로 생긴다(기존 5개 유지) | GitHub Projects v2 설정(코드 아님) | `Run:` `gh api graphql -f query='...updateProjectV2Field...'` 또는 웹 UI로 옵션 추가 후 `gh project field-list 6 --owner gabrielwithappy` / `Expected:` Status 필드 옵션에 Awaiting Verification이 추가되어 총 6개 확인 |
| 3. 템플릿·문서 갱신 | 앞으로 작성되는 계획들이 "실사용 확인만 남음" 상태를 일관된 문구로 표시하도록 안내되고, 대시보드 설정 문서가 6개 옵션 요구사항을 안내한다 | `.agentos/project/exec-plans/TEMPLATE.md`(상태 문구 규칙에 짧은 안내 추가), `docs/observability-setup.md` | 사람이 읽고 확인 |
| 4. 실사용 검증 | 실제 active 계획을 동기화했을 때 Status가 정확히 반영됨 | — (검증 전용) | `Run:` `OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 uv run agentos dashboard sync-plan --all` 후 `gh project item-list 6 --owner gabrielwithappy --format json` / `Expected:` "사용자 실사용 확인 대기" 문구를 가진 카드들은 Awaiting Verification으로, 이 계획 자신(`reviewed: false`)은 Backlog로 반영 |

## 구현 단계

### Task 1: `status_to_board_status()` 5단계 확장 (`agentos/observability/plan_parser.py`)

**파일:**
- 수정: `agentos/observability/plan_parser.py`
- 수정: `tests/test_plan_parser.py`

- [x] `status_to_board_status(status_text: str, reviewed: str) -> str`의 판단 순서에 4번째 갈래를 삽입한다(기존 순서 1-3은 그대로, 기존 "나머지"였던 In Progress 갈래 앞에 삽입):
  1. `primary_status.startswith("완료")` → `"Done"` (무변경)
  2. `not is_reviewed` → `"Backlog"` (무변경)
  3. `"완료" not in primary_status` → `"Ready"` (무변경)
  4. **신설**: `"사용자 실사용 확인 대기" in status_text` (원문 전체 `status_text`에서 검사 — 이 문구는 항상 괄호 안에 있으므로 `primary_status`가 아니라 원본 `status_text`를 검사해야 함) → `"Awaiting Verification"`
  5. 나머지 → `"In Progress"` (무변경)
- [x] `status_to_board_status()`의 docstring을 5단계 판단 순서로 갱신한다.
- [x] **`tests/test_plan_parser.py:83`의 기존 단정을 수정한다(신규 추가가 아니라 의도된 동작 변경).** 현재 `test_status_to_board_status_real_in_progress_cases()`(line 81-83)의 두 번째 단정 `assert status_to_board_status("구현 및 전체 검증 완료 (사용자 실사용 확인 대기)", "true") == "In Progress"`는 Task 1의 신규 4번째 갈래 도입 후 실제로 `"Awaiting Verification"`을 반환하게 되므로 **이 값 그대로 두면 테스트가 FAIL한다.** 이는 우연한 회귀가 아니라 이 계획이 의도적으로 바꾸는 동작이므로, 이 단정을 `test_status_to_board_status_real_in_progress_cases()`에서 제거하고(line 82의 `"구현 완료"` → `"In Progress"` 단정만 이 테스트에 남긴다), 신설되는 `test_status_to_board_status_awaiting_verification_cases()`에 다음 케이스로 옮겨 작성한다: (a) 현재 active 5개 계획과 동일한 실제 문구 `"구현 및 전체 검증 완료 (사용자 실사용 확인 대기)"` + `reviewed: "true"` → `"Awaiting Verification"`, (b) 동일 문구 + `reviewed: "false"` → `"Backlog"`(리뷰 우선순위가 신규 갈래보다 앞섬을 확인).
- [x] 나머지 기존 테스트(`test_status_to_board_status_real_backlog_cases`, `test_status_to_board_status_real_needs_context_maps_to_ready`, `test_status_to_board_status_virtual_ready_example`, `test_status_to_board_status_real_done_cases`, `test_status_to_board_status_unknown_text_falls_back_to_ready`, 그리고 수정 후의 `test_status_to_board_status_real_in_progress_cases`)가 전부 그대로 PASS함을 재실행으로 확인한다(line 83 수정 외에는 어떤 기존 단정도 값이 바뀌지 않아야 한다).

Run: `uv run pytest -q tests/test_plan_parser.py -k board_status`
Expected: 전체 PASS. `test_status_to_board_status_real_in_progress_cases`는 `"구현 완료"` 단정만 남아 PASS, 신설된 `test_status_to_board_status_awaiting_verification_cases`가 신규 2케이스로 PASS, 그 외 기존 케이스는 값 변경 없이 전부 PASS.

**실제 결과:** `7 passed`(PASS).

**계획에 없던 회귀 발견 및 수정(구현 중 확인):** `tests/test_dashboard_command.py`의 `PLAN_TEXT` 픽스처가 정확히 `"구현 및 전체 검증 완료 (사용자 실사용 확인 대기)"` 문구를 사용하고 있어, Task 1 적용 후 이 픽스처의 매핑 결과가 `In Progress`에서 `Awaiting Verification`으로 바뀌었다. `_project_metadata_response()`의 기본 mock 옵션 목록에 `Awaiting Verification`이 없어 `test_sync_plan_creates_card_when_not_found`(옵션 조회 실패 아님 — status 설정 자체가 스킵되는 경로)와 `test_sync_plan_all_option_syncs_every_file_in_active_dir`(옵션 없음 경고로 exit code 1)가 실패했다. 이 계획서에는 `tests/test_dashboard_command.py`를 수정 대상으로 명시하지 않았으나, Task 1의 실제 코드 변경이 이 파일의 테스트 픽스처와 충돌하는 것을 실행 중 발견해 다음과 같이 최소 수정했다: (1) `_project_metadata_response()`의 기본 옵션 목록에 `{"id": "opt_awaiting_verification", "name": "Awaiting Verification"}` 추가(Task 2에서 실제 보드에 옵션을 추가하는 것과 동일한 성격 — 테스트의 "보드에 이미 6개 옵션이 있다" 가정을 갱신), (2) `test_sync_plan_creates_card_when_not_found`의 `optionId` 단정을 `"opt_inprogress"`에서 `"opt_awaiting_verification"`으로 갱신(픽스처의 상태 문구가 실제로 Awaiting Verification에 해당하므로 정확한 값으로 수정, 회귀 은폐 아님). `uv run pytest -q tests/test_plan_parser.py tests/test_dashboard_command.py` → `20 passed`로 확인.

### Task 2: 보드 Status 옵션 추가 (GitHub Projects v2 설정)

**파일:** 없음(GitHub 쪽 설정, 코드 변경 아님)

- [x] `gh api graphql`의 `updateProjectV2Field` mutation으로 테스트 보드(`gabrielwithappy`, project 6)의 Status 필드에 `Awaiting Verification` 옵션을 추가한다(기존 Todo/Backlog/Ready/In Progress/Done 유지, 옵션 전체 재정의 방식이므로 기존 5개를 모두 포함한 목록에 신규 1개를 추가해서 보낸다).
- [x] 옵션 추가 직후 기존 카드 Status가 초기화되는 선행 계획에서 이미 확인된 현상이 재현되는지 확인하고, `sync-plan --all` 재실행으로 복구되는지 검증한다. (Task 4의 실사용 검증 단계에서 함께 확인)

Run: `gh project field-list 6 --owner gabrielwithappy`
Expected: Status 필드 옵션에 `Awaiting Verification` 포함 총 6개(Todo/Backlog/Ready/In Progress/Awaiting Verification/Done) 확인.

**실제 결과:** `updateProjectV2Field` mutation 성공, GraphQL 재조회로 6개 옵션(Todo/Backlog/Ready/In Progress/Awaiting Verification/Done) 확인. `Awaiting Verification` 옵션 ID: `55536f82`.

### Task 3: 템플릿·문서 갱신

**파일:**
- 수정: `.agentos/project/exec-plans/TEMPLATE.md`
- 수정: `docs/observability-setup.md`

- [x] `TEMPLATE.md`의 상태 문구 관련 안내(파일 상단 주석 또는 별도 섹션)에, 구현·자동 검증은 끝났지만 사람의 수동 확인만 남은 경우 상태 문구에 정확히 `"(사용자 실사용 확인 대기)"`를 포함시키라는 짧은 안내를 추가한다(새 필드를 만들지 않고 기존 관용구를 표준화).
- [x] `docs/observability-setup.md`에 6번째 옵션(Awaiting Verification)의 용도와 판단 조건(정확한 문구 매칭)을 표에 추가한다.

Run: `grep -q "사용자 실사용 확인 대기" .agentos/project/exec-plans/TEMPLATE.md && grep -q "Awaiting Verification" docs/observability-setup.md`
Expected: 두 grep 모두 매치(문서 콘텐츠 자체가 완료 기준).

**실제 결과:** `BOTH MATCH` 출력 확인. TEMPLATE.md에 상태 문구 관용구 안내 섹션 추가, observability-setup.md의 Status 컬럼 표를 5종→6종으로 갱신(판단 조건 열 추가).

### Task 4: 전체 회귀 및 실사용 검증

**파일:** 없음(검증

## 범위와 비목표

- 포함: `status_to_board_status()` 5단계 확장, 보드 Status 옵션 추가, TEMPLATE.md/observability-setup.md 문서 갱신, 실사용 검증.
- 제외: 카드 본문(`render_card_body`)에 별도 행동 라벨 추가(질문 단계에서 검토했으나 컬럼 분리 방식으로 결정), 런타임 이벤트 알림 경로(`GithubDashboardAdapter._STATUS_BY_EVENT`) 변경, 새 exec-plan 메타 필드 추가(기존 상태 문구 관용구 확장으로 처리), Backlog/Ready/Done 판단 조건 변경.

## 리뷰 반영 이력
- 초안 작성 시 사용자와 결정: GitHub 대시보드가 "구현 완료"인 계획을 In Progress로 보여줘 사용자가 해야 할 행동이 구분되지 않는다는 지적에서 출발. 원인은 매핑 버그가 아니라 In Progress 라벨이 "에이전트 작업 중"과 "사람 확인 대기"라는 서로 다른 의미를 뭉뚱그리는 표현력 부족임을 확인(현재 active 5개 계획 전부가 "사용자 실사용 확인 대기" 상태인 반면 archive 41개는 0개 — 이 상태가 예외가 아니라 반복되는 정상 단계임을 저장소 전수 조사로 확인). 대안(카드 본문에 행동 라벨만 추가) 대신 컬럼 분리(5단계 확장)로 진행하기로 결정.
- **1차 Gate 2 리뷰 결과: `principle-auditor` PASS(비차단 노트: substring 매칭 신뢰성), `usability-reviewer` PASS(비차단 노트 2건: 경고 문구 stale 참조, Task 3 grep 검증의 가독성 미보장), `plan-reviewer` FAIL.** `plan-reviewer` FAIL 사유: (a) Task 1 적용 후 `tests/test_plan_parser.py:83`의 기존 단정(`"사용자 실사용 확인 대기"` 문구 입력 → `"In Progress"` 기대)이 새 동작과 충돌해 FAIL하는데, 계획이 이 기존 단정의 수정을 지시하지 않고 신규 케이스 추가만 언급함, (b) 아키텍처 절이 제시한 검증용 grep 명령(`grep -l ... active/*.md`, 파일 전체 검색)이 실제로는 6개 매치(이 계획 문서 자신의 본문 프로즈 포함)를 반환해 "active 5개 전부" 주장과 자기모순.
- **반영**: Task 1 체크리스트에 `tests/test_plan_parser.py:83`의 기존 단정을 명시적으로 제거·이동하도록 지시(신규 `test_status_to_board_status_awaiting_verification_cases`로 이관, 의도된 동작 변경임을 명시). 아키텍처 절의 판별 신호 설명을 상태 라인 전용 검색(5개 매치)과 파일 전체 검색(6개 매치, 이 계획 자신 포함)으로 구분하고, 상태 라인만 검색하는 정확한 grep 명령(`grep "^> \*\*상태:\*\*" ... | grep "..."`)을 추가.
- **2차 Gate 2 리뷰(재검토) 결과: `plan-reviewer` PASS.** 두 지적 모두 독립 재검증(실제 grep 재실행 포함) 완료. 세 서브에이전트 PASS 합의 완료 → `reviewed: true` 전이.

## 구현 결과

- **Task 1** — `agentos/observability/plan_parser.py`의 `status_to_board_status()`에 4번째 판단 갈래(Awaiting Verification)를 기존 In Progress 갈래 앞에 삽입. `tests/test_plan_parser.py`의 기존 In Progress 회귀 케이스 중 "사용자 실사용 확인 대기" 문구를 가진 단정을 신설 `test_status_to_board_status_awaiting_verification_cases()`로 이관(값 `In Progress` → `Awaiting Verification`, 의도된 동작 변경). **구현 중 계획에 없던 회귀를 추가로 발견·수정**: `tests/test_dashboard_command.py`의 `PLAN_TEXT` 픽스처가 동일 문구를 쓰고 있어 mock 옵션 목록과 `optionId` 단정 2건이 새 매핑값과 충돌 — `_project_metadata_response()`에 `Awaiting Verification` mock 옵션 추가, `test_sync_plan_creates_card_when_not_found`의 기대값을 정확한 값(`opt_awaiting_verification`)으로 갱신.
- **Task 2** — GitHub Projects v2 보드(`gabrielwithappy`, project 6)의 Status 필드에 `updateProjectV2Field` GraphQL mutation으로 `Awaiting Verification` 옵션(색상 ORANGE) 추가. 기존 5개(Todo/Backlog/Ready/In Progress/Done) 유지, 총 6개.
- **Task 3** — `.agentos/project/exec-plans/TEMPLATE.md`에 "상태 문구 관용구" 안내 섹션 추가(자동 검증 완료·수동 확인만 남은 경우 `"(사용자 실사용 확인 대기)"` 문구 사용 안내). `docs/observability-setup.md`의 "Status 컬럼 5종" 절을 "6종"으로 갱신하고 판단 조건 열을 추가.
- **Task 4** — 전체 테스트 스위트 fresh run(538 passed, 회귀 없음), `git diff --check` 통과. 실제 테스트 보드에 `sync-plan --all` 실행 후 GraphQL 재조회로 5개 카드(이 계획 자신 포함) 전부 정확한 Status로 반영됨을 확인.

## 사용 방법

1. exec-plan 작성 시, 구현·자동 검증은 끝났지만 사람의 수동 확인만 남은 상태라면 `> **상태:**` 문구에 `"(사용자 실사용 확인 대기)"`를 포함시킨다(TEMPLATE.md에 안내 반영됨).
2. `agentos dashboard sync-plan --all --owner <owner> --project-number <번호>`를 실행하면 이 문구가 있는 계획은 보드에서 `Awaiting Verification` 컬럼으로, 없는 계획은 기존 Backlog/Ready/In Progress/Done 4단계 규칙대로 분류된다.
3. 대상 보드에 `Awaiting Verification` Status 옵션이 없으면 카드는 만들어지되 상태는 바뀌지 않고, 콘솔에 `Status option 'Awaiting Verification' not found on board` 경고가 뜬다 — 웹 UI 또는 `gh api graphql`의 `updateProjectV2Field`로 옵션을 먼저 추가한다.
4. Status 옵션을 처음 추가한 직후에는 기존 카드 Status가 일시적으로 초기화될 수 있으니(GitHub API 특성), `sync-plan --all`을 한 번 더 실행해 복구한다.

## 아카이브 결정

구현·전체 회귀·Gate 2 리뷰(3종 PASS)·실사용 검증(실제 보드에서 5개 카드 정확한 매핑 확인)을 모두 완료했다. 사용자가 명시적으로 archive를 요청하면 archive로 이동한다.
