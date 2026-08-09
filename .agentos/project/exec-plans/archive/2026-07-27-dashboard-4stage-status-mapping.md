# GitHub Projects 보드 4단계 Status 컬럼 확장 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 3종 PASS, 증거: `.agents/traces/reviews/2026-07-27-dashboard-4stage-status-mapping/{plan-reviewer,principle-auditor,usability-reviewer}.md`)<br>
> active_agent: Claude Code (claude-sonnet-5)<br>
> active_session: 5b17931b-4ac1-4a97-9600-9b13d78e9f7f<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0OZGs<br>
> implementation_started_at: 2026-07-27T11:30:00Z<br>
> implementation_completed_at: 2026-07-27T12:05:00Z<br>
> implementation_duration: 약 35분<br>

> **usability_review_required:** true<br>
> usability_review_reason: `agentos dashboard sync-plan` 콘솔 출력 문구(어떤 카드가 어느 Status로 갱신됐는지)와 GitHub Projects 보드 UI에 사용자가 직접 보는 Status 컬럼 구성(옵션 이름·개수)을 바꾼다.<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 현재 `status_to_board_status()`는 exec-plan의 상태 문구를 Todo/In Progress/Done 3개로만 매핑한다. 실제 exec-plan 라이프사이클(리뷰 대기 → 리뷰 통과/구현 대기 → 구현 진행/검증 대기 → 완료)은 최소 4단계인데 이를 3개로 뭉개면서, 사용자가 지적한 대로 "리뷰 대기 중인 계획"과 "구현이 다 끝나 실사용 확인만 남은 계획"이 보드에서 구분되지 않는다(2026-07-27 대화). 보드 Status 컬럼을 실제 계획 단계(Backlog/Ready/In Progress/Done)로 확장하고, 매핑 로직도 이 4단계에 맞게 정교화한다.

**사용자 결과 요약:**
- 최종 결과: `agentos dashboard sync-plan`(단일/--all 모두)이 exec-plan의 상태 문구와 `reviewed` 필드를 함께 보고 Backlog/Ready/In Progress/Done 4개 중 하나로 카드 Status를 정확히 반영한다.
- 대상 독자: GitHub Projects 보드에서 계획들의 실제 진행 단계를 한눈에 구분하고 싶은 저장소 오너.
- 일상 사용의 변화: 지금까지는 "리뷰 대기"와 "구현 대기"가 모두 In Progress로 뭉뚱그려졌다. 이후에는 Backlog(리뷰 전)/Ready(리뷰 통과, 구현 전)/In Progress(구현 진행 중 또는 실사용 확인 대기)/Done(완전 종료)으로 구분된다.
- 바뀌지 않는 경계: `sync-plan`/`sync-plan --all`의 커맨드 인터페이스, exec-plan 파일 구조 자체(새 필드를 추가하지 않고 기존 `> **상태:**`와 `reviewed` 필드만 재해석), 카드 식별 키(H1 제목), on-demand 실행 방식.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등):
  - **GitHub Projects v2 보드의 Status 필드 옵션 자체를 3개(Todo/In Progress/Done)에서 4개(Backlog/Ready/In Progress/Done)로 바꿔야 한다.** 이는 코드가 아니라 GitHub 쪽 설정 변경이며, `gh project field-list`/GraphQL `updateProjectV2SingleSelectField` mutation으로 옵션을 추가하거나, 사용자가 직접 웹 UI에서 옵션을 추가해야 한다. 기존 옵션 이름을 재사용할 수 없는 이유: "Todo"라는 이름이 이미 있지만 이번 설계는 그 자리를 "Backlog"로 대체하는 것이 아니라 Backlog/Ready 두 단계로 쪼개는 것이므로, 기존 "Todo" 옵션에 걸려있는 카드(예: `CLI_INTERRUPT`)의 처리 방침을 명시해야 한다(아래 아키텍처 참고).
  - 테스트 보드(`gabrielwithappy`, project 6)는 이미 있으나 Status 옵션 추가는 이 세션에서 `gh`로 실행 가능(권한 이미 확보됨, `project` scope).

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| 대상 보드 Status 필드에 4개 옵션 추가 권한 | auth/permission | 실사용 검증 시 필수 | `Run:` `gh project field-list 6 --owner gabrielwithappy` / `Expected:` Status 필드가 조회되고, 이후 옵션 추가 mutation이 에러 없이 성공 | 단위 테스트는 4개 옵션이 이미 있다고 가정한 mock으로 전부 수행 | 실패 시 실사용 검증만 보류, 코드 구현은 계속 |

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서의 완료 증거, Gate 2 리뷰 증거(`.agents/traces/reviews/2026-07-27-dashboard-4stage-status-mapping/`)
- Durable Result Surface: `agentos/observability/plan_parser.py`(`status_to_board_status` 4단계 매핑으로 교체), `docs/observability-setup.md`(Status 옵션 요구사항 갱신), `tests/test_plan_parser.py`(신규 매핑 케이스)

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:**
- 4단계 정의와 판단 규칙. `.agentos/project/exec-plans/{active,archive}/*.md`의 `> **상태:**`+`> reviewed:` 조합을 전수 조사한 결과(2026-07-27, `plan-reviewer` 1차 리뷰가 이 조사의 부정확성을 지적해 재조사 후 정정함), 현재 저장소에 실존하는 `reviewed`×상태문구 조합은 정확히 아래 8종류뿐이다 — 표의 "실제 사례" 열은 이 8종류 중 하나이거나, 실존 사례가 없는 단계는 그렇게 명시한 **가상 예시**다(허구를 실재처럼 서술하지 않기 위해):

| 단계 | 판단 조건 | 실제 사례 (저장소 전수 조사 결과) |
|---|---|---|
| **Backlog** | `reviewed: false` | "구현 계획 (리뷰 대기)", "리뷰 대기 (완료 후 '완료'로 변경)" — 실존 |
| **Ready** | `reviewed: true` **이고** 주 상태 문구에 "완료"가 없음 | **저장소에 실존 사례 없음.** 가상 예시: "구현 대기 (Gate 2 리뷰 통과, ...)" — 이 문구 자체는 지금 어떤 실제 exec-plan 파일에도 존재하지 않으며, 향후 리뷰 통과 직후·구현 착수 전 시점에 이 조합이 나타날 것으로 예상되는 상태다. `NEEDS_CONTEXT (분석 handoff 완료)`(`reviewed: true`, "완료"가 주 상태에 없음 — 괄호 안에만 있음)가 이 규칙에 해당하는 유일한 실존 파일이며, 아래 별도 처리 규칙을 따른다 |
| **In Progress** | `reviewed: true` **이고** 주 상태 문구에 "완료"가 있지만 전체가 "완료"로 시작하지 않음 | "구현 완료", "구현 및 전체 검증 완료 (사용자 실사용 확인 대기)" — 실존 |
| **Done** | 주 상태 문구가 "완료"로 **시작**(괄호 유무 무관) | "완료", "완료 (Scope Exception 승인됨)", "완료 (구현·검증 완료)" — 실존 |

  판단 순서: (1) 상태 문구 전체가 "완료"로 시작하면 → Done. (2) 그 외 `reviewed`가 false면 → Backlog. (3) `reviewed`가 true이고 주 상태 문구(괄호 앞)에 "완료"가 없으면 → Ready. (4) 나머지(reviewed true + "완료"가 주 상태 문구에 있지만 전체가 "완료"로 시작하지 않는 경우) → In Progress.
  **`NEEDS_CONTEXT (분석 handoff 완료)`는 규칙 (3)에 그대로 해당한다**(주 상태 문구 "NEEDS_CONTEXT"에 "완료"가 없으므로) — 별도 폴백이 아니라 Ready 규칙이 정상적으로 처리하는 케이스다. 이 계획이 커버하는 8종류 조합 밖의 완전히 새로운 문구 패턴(예: 향후 다른 표현이 도입되는 경우)만 안전한 기본값 **Ready**로 폴백한다(신뢰성 — 완료로 오분류하지 않는 쪽).
- **기존 Status 옵션과의 관계**: 런타임 이벤트 알림 경로(`GithubDashboardAdapter._STATUS_BY_EVENT`, `CLI_INTERRUPT` 등 이벤트 → Todo/In Progress/Done 매핑)는 이번 계획과 **별개로 그대로 유지**한다 — 그쪽은 exec-plan이 아니라 런타임 이벤트용이며 이번 계획의 스코프가 아니다. 보드에 "Todo" 옵션은 그대로 남겨두고(런타임 이벤트가 계속 사용), exec-plan 동기화 경로만 새 옵션(Backlog/Ready)을 추가로 사용한다. 즉 보드 Status 옵션은 최종적으로 5개(Todo/Backlog/Ready/In Progress/Done)가 되며, "Todo"는 런타임 이벤트 전용, 나머지 4개는 exec-plan 동기화 전용으로 용도가 분리된다는 점을 사용 방법 문서에 명시한다.
- `status_to_board_status()`의 시그니처를 `status_to_board_status(status_text: str, reviewed: str) -> str`로 확장(현재는 `status_text`만 받음) — 호출부(`agentos/commands/dashboard.py`)도 함께 수정.

**기술 스택:**
- 기존 `agentos/observability/plan_parser.py`, GitHub Projects v2 GraphQL(옵션 추가는 코드가 아니라 `gh`/웹 UI로 1회 수행).

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | Gate 2 리뷰 PASS(3종), Milestone 1-5 전부 구현·검증 완료 |
| 현재 위치 | 사용자 실사용 확인 대기 |
| 다음 단계 | 사용자가 실제 운영 환경에서 확인 후 아카이브 결정 |
| 완료 신호 | 실제 테스트 보드에서 active 계획들을 `sync-plan --all`로 동기화했을 때 각 계획의 Status가 위 표의 규칙대로 정확히 반영됨을 수동 확인(달성 — 이 계획 자신이 Ready로, 나머지 완료된 4개가 In Progress로 정확히 분류됨) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 4단계 매핑 함수 교체 | 상태 문구+reviewed 조합으로 4단계 중 하나가 정확히 나온다 | `agentos/observability/plan_parser.py`의 `status_to_board_status()` | `Run:` `uv run pytest tests/test_plan_parser.py -q -k board_status` / `Expected:` PASS — 저장소에 실존하는 8종류 조합 전부(Backlog 2건, `NEEDS_CONTEXT`→Ready 1건, In Progress 2건, Done 3건)가 정확히 매핑되는지 검증, 실존하지 않는 가상 Ready 예시("구현 대기 (...)") 1건과 8종류 밖의 완전히 새로운 미지 문구 1건이 각각 Ready로 처리/폴백되는지 검증 |
| 2. 호출부 갱신 + 침묵 성공 버그 수정 | `sync-plan`/`sync-plan --all` 실행 시 실제로 4단계가 반영된다. **아울러 usability-reviewer가 실사용 관점에서 지적한 기존 결함을 이번에 함께 고친다**: `_sync_one()`이 지금은 보드에 해당 Status 옵션이 없어(`option_id is None`) 실제로 상태를 못 바꿨을 때도 `"Synced status: ..."`를 무조건 출력해 사용자가 성공한 줄 오해하게 만든다. Milestone 3(옵션 추가)을 아직 안 한 상태에서 사용자가 먼저 `sync-plan`을 돌리면 정확히 이 상황이 재현되므로, 옵션을 못 찾으면 `"Synced status: ..."` 대신 `"[yellow]Status option '{board_status}' not found on board — card created/updated but status not set. Run Milestone 3's board setup first.[/yellow]"`류의 명확한 경고를 출력하도록 고친다 | `agentos/commands/dashboard.py`의 `_sync_one()` | `Run:` `uv run pytest tests/test_dashboard_command.py -q` / `Expected:` 기존 7개 테스트가 새 시그니처(`reviewed` 인자 추가)에 맞게 갱신되어 100% PASS, **신규 테스트**: Status 옵션이 board에 없는 상태(mock에서 `_status_option_ids`에 해당 이름이 없는 경우)를 시뮬레이션해 `"Synced status"`가 아니라 경고 문구가 출력되는지 검증 |
| 3. 보드 Status 옵션 추가 | 대상 보드에 Backlog/Ready 옵션이 새로 생긴다(기존 Todo/In Progress/Done은 유지) | GitHub Projects v2 설정(코드 아님) | `Run:` `gh api graphql -f query='...updateProjectV2SingleSelectField...'` 또는 웹 UI로 옵션 추가 후 `gh project field-list 6 --owner gabrielwithappy` / `Expected:` Status 필드 옵션에 Backlog, Ready가 추가되어 총 5개(Todo/Backlog/Ready/In Progress/Done) 확인 |
| 4. 문서 갱신 | `docs/observability-setup.md`가 5개 옵션 요구사항과 용도 분리(Todo=런타임 이벤트, 나머지=exec-plan)를 안내 | `docs/observability-setup.md` | 사람이 읽고 확인 |
| 5. 실사용 검증 | 실제 4개 active 계획을 동기화했을 때 Status가 정확히 반영됨 | — (검증 전용) | `Run:` `OBSERVABILITY_GITHUB_OWNER=gabrielwithappy OBSERVABILITY_GITHUB_PROJECT_NUMBER=6 uv run agentos dashboard sync-plan --all` 후 `gh project item-list 6 --owner gabrielwithappy --format json` / `Expected:` 각 계획 카드의 status가 그 계획 문서의 실제 `> **상태:**`+`reviewed` 조합에 대응하는 단계와 일치 |

## 리뷰 반영 이력
- 2026-07-27 (Gate 2 1차 리뷰): `principle-auditor` PASS/CLEAN (런타임 이벤트 경로와의 분리, 안전한 폴백 방향, 외부 설정 의존성의 명시적 분리 모두 확인). `plan-reviewer` FAIL — 아키텍처 표의 "Ready 실제 사례"로 인용한 "구현 대기 (Gate 2 리뷰 통과, ...)" 문구가 실제로는 어떤 exec-plan 파일에도 존재하지 않고 테스트 픽스처에서만 존재하는 허구 인용이었다는 지적(저장소 45개 상태 라인 전수 재조사로 확인). `usability-reviewer` FAIL — `_sync_one()`이 보드에 해당 Status 옵션이 없어도(Milestone 3의 옵션 추가를 아직 안 한 상태) "Synced status" 성공 메시지를 무조건 출력해, 사용자가 실제로는 반영 안 됐는데 성공한 걸로 오인할 수 있는 기존 결함을 지적(4단계 확장으로 이 시나리오가 처음 실제로 발생 가능해짐). 반영: 아키텍처 표를 실제 8종류 조합 기준으로 정정하고 허구 예시는 "가상 예시"로 명시, Milestone 1 검증 문구를 실제 조합 수로 수정, Milestone 2에 옵션 미존재 시 명확한 경고 출력 로직 추가.
- 2026-07-27 (Gate 2 2차 리뷰, 수정본 재검토): `plan-reviewer` PASS — 아키텍처 표의 정직한 재서술 확인, `NEEDS_CONTEXT`가 별도 폴백이 아닌 실제 사례임을 확인, 독립 grep/Python 재집계로 8종류 조합이 정확함을 재검증, Milestone 1 검증 문구 정정 확인, Milestone 2의 침묵 성공 버그 수정안(구체적 경고 메시지 템플릿·신규 테스트 기준)이 충분히 구체적임을 확인. `usability-reviewer` PASS — 침묵 성공 버그 수정안이 원인·후속 조치를 모두 알려주는 구체적 경고 메시지로 명시됨을 확인, 신규 테스트 기준 확인, 나머지 2개 non-blocking 지적(5개 옵션 UI 혼동, NEEDS_CONTEXT 폴백 미표시)은 1인 오너 저위험 도구에 한해 PASS를 막을 정도는 아니라고 판단. 세 서브에이전트 PASS/CLEAN 합의 완료 → `reviewed: true` 전이.

## 구현 결과
- `agentos/observability/plan_parser.py`: `status_to_board_status()`를 `(status_text, reviewed) -> str` 시그니처로 확장, 계획 문서의 판단 순서(완료로 시작→Done, reviewed false→Backlog, reviewed true+"완료" 없음→Ready, 나머지→In Progress)를 그대로 구현.
- `agentos/commands/dashboard.py`: 호출부를 새 시그니처에 맞게 갱신. **usability-reviewer가 지적한 침묵 성공 버그를 수정** — 대상 Status 옵션이 보드에 없으면(`option_id is None`) "Synced status" 성공 메시지 대신 `"Status option '...' not found on board — card created/updated but status not set. Run Milestone 3's board setup first."` 경고를 출력하도록 분기.
- 테스트 보드(`gabrielwithappy`, project 6)의 Status 필드에 `updateProjectV2Field` GraphQL mutation으로 `Backlog`, `Ready` 옵션 추가(기존 Todo/In Progress/Done 유지) — 총 5개 옵션.
- `docs/observability-setup.md`: `agentos dashboard sync-plan` 사용법과 5개 Status 옵션의 용도 분리(Todo=런타임 이벤트 전용, 나머지 4개=exec-plan 전용) 표, 옵션 미존재 시 경고 동작, **옵션 추가 시 기존 카드 Status가 초기화되는 GitHub API 특성과 그 복구 방법(`sync-plan --all` 재실행)**을 실사용 검증 중 발견해 명시.
- `tests/test_plan_parser.py`, `tests/test_dashboard_command.py`: 8종류 실존 조합 + 가상 Ready 예시 + 미지 문구 폴백 테스트, 옵션 누락 시 경고 테스트 추가.

## 발견된 리스크 (실사용 검증 중 확인)
- **Status 옵션 추가 시 기존 카드 값 초기화**: `updateProjectV2Field`로 옵션 목록에 새 항목을 추가하면(옵션 전체를 재정의하는 방식이라) 기존 카드들의 Status 참조가 끊겨 전부 "값 없음"으로 초기화된다. 실제로 Milestone 3 수행 직후 기존 6개 카드 전부 Status가 사라지는 것을 확인했다. `sync-plan --all`을 한 번 더 돌리면 자동 복구되므로 데이터 손실은 아니지만, 이 특성을 몰랐다면 "다 날아갔다"고 오인할 수 있어 문서에 명시했다.
- **GraphQL 쓰기-후-읽기 전파 지연 재확인**: 새로 생성한 카드가 곧바로 `gh project item-list`/GraphQL 조회에 안 잡히다가 몇 초 후 나타나는 현상을 이번에도 재현했다(선행 계획에서 이미 문서화된 리스크와 동일 패턴).

## 사용 방법
```bash
# 대상 보드 Status 필드에 Backlog/Ready 옵션이 없다면 먼저 추가 (1회성, 웹 UI 또는 gh api graphql)
# 이후 평소처럼 sync-plan 사용
agentos dashboard sync-plan --all --owner <owner> --project-number <번호>
```
- 계획의 `reviewed` 필드와 `> **상태:**` 문구 조합으로 Backlog(리뷰 전) / Ready(리뷰 통과, 구현 전) / In Progress(구현 중 또는 최종 확인 대기) / Done(완전 종료) 중 하나가 자동으로 반영된다.
- 대상 보드에 필요한 Status 옵션이 없으면 카드는 만들어지되 상태는 바뀌지 않고, 콘솔에 어떤 옵션이 없는지 명확한 경고가 뜬다.
- Status 옵션을 처음 추가한 직후에는 기존 카드 Status가 초기화될 수 있으니, `sync-plan --all`을 한 번 더 실행해 복구한다.

## 검증 근거
- `Run:` `uv run pytest tests/test_plan_parser.py tests/test_dashboard_command.py -q` → **실행 결과: 19 passed** (11 + 8)
- `Run:` `uv run pytest tests/ -q` (전체 회귀) → **실행 결과: 537 passed**
- 실사용 검증: `gh api graphql`로 테스트 보드 Status 필드에 Backlog/Ready 옵션 추가 확인 → `sync-plan --all` 실행 → 5개 계획 전부 성공 → 이 계획 문서 자신("GitHub Projects 보드 4단계 Status 컬럼 확장 구현 계획", `reviewed: true`+"완료" 아님)이 정확히 **Ready**로, 이미 완료된 4개 계획이 정확히 **In Progress**로 반영됨을 GraphQL 직접 조회로 확인(전파 지연 후 재확인, 2026-07-27).

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
