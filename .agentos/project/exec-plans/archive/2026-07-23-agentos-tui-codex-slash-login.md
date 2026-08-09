# AgentOS TUI Codex Slash Login 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-23<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-23T13:58:00Z<br>
> implementation_completed_at: 2026-07-23T14:03:35Z<br>
> implementation_duration: 5m 35s<br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** AgentOS TUI에서 Codex 전용 `/login`, `/logout`, 그리고 auth-aware `/status` 경로로 기존 Codex CLI 인증 흐름을 시작·확인·종료할 수 있는 최소 사용자 표면을 구현한다.

**사용자 결과:** 사용자는 TUI에서 Codex 로그인 시작, 현재 인증 상태 확인, 로그아웃까지 처리하는 핵심 흐름을 얻게 된다. 다만 실제 계정 승인 자체는 여전히 Codex CLI와 외부 브라우저/승인 화면에서 계속될 수 있으며, TUI는 그 진행 상태와 다음 행동을 안내하는 역할만 맡는다. 바뀌지 않는 경계는 native OAuth transport 자체 구현, browser/device-code 선택 UI, root docs/ADR 수정, 타 provider 범용 auth framework 도입이 이번 계획에 포함되지 않는다는 점이다.

**진행 상태:** 계획 범위를 core orchestration으로 축소했고, Gate 2 지적을 반영해 command 경계와 provider별 동작 규칙을 명시하는 revision 단계다. 현재 저장소에는 `/login`과 `/logout` slash command가 없고, `/status`는 일반 TUI 상태만 보여주며 Codex auth 상태는 `agentos llm status --provider codex` 또는 `codex login status`를 셸에서 직접 확인해야 한다.

**아키텍처:** TUI는 `/login`과 `/logout`를 Codex 전용 command로 추가하되 command palette와 help에서 이름/설명을 명시적으로 `Codex` 범위로 표시한다. 구현 경계는 설치된 `agentos` 바이너리를 다시 shell-out하지 않고, `agentos/commands/llm.py` 아래에 sanitized payload helper를 추가해 Typer command와 TUI worker가 같은 in-process contract를 공유하는 방식으로 고정한다. `/status`는 기존 TUI 상태 surface를 유지하면서, active provider가 `codex`이면 auth 상태 블록을 추가하고, `codex`가 아니면 Codex auth command가 비활성 의미임을 복구 문구로 안내한다.

**기술 스택:** Python 3.12+, Textual, Typer, pytest, 기존 AgentOS TUI/session framework, existing Codex CLI provider contract.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Gate 2 reviewer 3종 PASS, Codex slash auth surface 구현, focused verification PASS |
| 현재 위치 | 구현 및 fresh verification 완료 |
| 다음 단계 | 사용자 요청 시 archive/commit/PR 준비 |
| 완료 신호 | `uv run pytest tests/test_tui_cli.py -k "login or logout or status or codex" -q`, `uv run pytest tests/test_codex_provider.py tests/test_cli_contract.py -q`, docs grep PASS |

## 세션 인계 체크포인트

- 현재 완료 범위: Codex-only core auth surface(`/login`, auth-aware `/status`, `/logout`)로 범위를 축소했다.
- 미완료 작업: Gate 2 재리뷰, reviewer 지적 반영 확인, implementation-ready status 전환.
- 다음 세션 첫 작업: `plan-reviewer`, `principle-auditor`, `usability-reviewer` 재리뷰 결과를 반영하고 문서 해시를 고정한다.
- 아직 안 한 검증: gate2-review-check, lifecycle refresh.
- 관련 HISTORY checkpoint: 2026-07-23 Codex core foundation closeout 이후 TUI auth surface planning 시작.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | TUI 안에서 Codex 로그인 시작, 상태 확인, 로그아웃이 가능한 최소 slash auth 표면 |
| 누구를 위한 것인가? | AgentOS TUI를 사용하는 개발자와 Codex account-login을 쓰려는 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 더 이상 셸로 나가서 Codex login/status/logout을 직접 기억할 필요 없이 TUI에서 같은 핵심 흐름을 시작할 수 있다 |
| 무엇은 바뀌지 않는가? | 실제 auth transport 소유권, auth store schema, browser/device-code 선택 UI, 다른 provider의 로그인 UX, root docs/ADR |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. slash auth command 도입 | `/login`, `/logout`가 command palette와 help에 `Codex` 전용 command로 나타나고 `/status` 설명이 auth-aware 상태 surface로 갱신된다 | `agentos/terminal/tui/commands.py`, `agentos/terminal/tui/app.py`, tests | `PASS tui-auth-commands-planned` |
| 2. login orchestration UX | `/login` 실행 시 Codex CLI login 경로가 시작되고, TUI가 외부 승인 가능성·진행·결과·다음 행동을 안내한다 | `agentos/terminal/tui/app.py`, `agentos/commands/llm.py`, tests | TUI login orchestration tests PASS |
| 3. 상태/로그아웃 UX | `/status`, `/logout`가 provider별 규칙에 맞는 Codex 인증 상태와 다음 안전 행동을 안내한다 | `agentos/terminal/tui/app.py`, `agentos/commands/llm.py`, tests | TUI status/logout tests PASS |
| 4. 문서/회귀 증거 | 사용법과 경계가 CLI reference 및 테스트에 남는다 | `docs/cli-reference.md`, `tests/test_tui_cli.py`, `tests/test_codex_provider.py` | docs grep + focused pytest PASS |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, `.agents/traces/reviews/2026-07-23-agentos-tui-codex-slash-login/{plan-reviewer,principle-auditor,usability-reviewer}.json`
- durable result surface: `agentos/terminal/tui/{commands,app}.py`, `agentos/commands/llm.py`, `docs/cli-reference.md`, `tests/test_tui_cli.py`, `tests/test_codex_provider.py`
- documentation-only exception: 없음. 최종 결과는 TUI 코드/테스트/사용 문서에 남는다.

## 의존성 분석

- 외부 의존성: existing `agentos llm login/status/logout --provider codex --json` contract, local Codex CLI executable
- 네트워크 의존성: 실제 로그인 시 Codex CLI가 외부 auth 흐름을 여는 것은 허용하지만, 계획/테스트 단계는 fake executable과 mock/stub으로 닫는다
- 보안 의존성: raw token, refresh token, raw callback query, raw stderr를 transcript/log/test artifact에 노출하지 않고, 실패 시에는 sanitized `message`, `status`, `recovery`, `next_command`만 사용자 표면에 남긴다
- SSOT 근거: auth credential ownership과 transport 경계는 `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`를 따른다. 이번 계획은 그 경계를 변경하지 않고 TUI orchestration surface만 추가한다.

## 의존성 게이트

### codex-cli-auth-surface-available

- name: codex-cli-auth-surface-available
- type: local-command
- required: true
- purpose: 구현 초기 단계에서 TUI slash auth surface가 재사용할 existing sanitized contract와 provider 경로가 살아 있는지 확인한다.
- preflight:
  Run: `grep -q '^def login(' agentos/commands/llm.py && grep -q '^def status(' agentos/commands/llm.py && grep -q '^def logout(' agentos/commands/llm.py && grep -q 'json_output: bool' agentos/commands/llm.py && grep -q 'class CodexCliProvider' agentos/llm/providers/codex_cli.py && echo "PASS codex-cli-auth-surface-available"`
  Expected: `PASS codex-cli-auth-surface-available`
- fallback:
  available: false
  reason: slash command가 호출할 local contract와 Codex provider path가 없으면 이번 범위는 native auth plan과 얽혀 과대해진다.
- failure_behavior: NEEDS_CONTEXT

## 파일 구조

- 수정: `agentos/terminal/tui/commands.py` — `/login`, `/logout` command registry를 `Codex login`, `Codex logout` 의미로 추가하고 `/status` 설명을 auth-aware surface로 갱신
- 수정: `agentos/terminal/tui/app.py` — slash auth command dispatch, provider별 gating, auth status rendering, in-process worker orchestration, recovery copy
- 수정: `agentos/commands/llm.py` — Typer command와 TUI가 함께 쓰는 sanitized payload helper(`login/status/logout`용) 추가 또는 명시적 분리
- 수정: `docs/cli-reference.md` — TUI slash auth command 사용법과 core-only 범위/한계, 외부 브라우저 승인 경계 반영
- 수정: `tests/test_tui_cli.py` — `/login`, `/status`, `/logout`, provider gating, recovery, secret boundary focused tests
- 수정: `tests/test_codex_provider.py` — Codex login/status/logout payload contract tests

## 구현 작업

### Task 0: 현재 surface preflight

**파일:**
- 수정 없음
- 확인: `agentos/commands/llm.py`
- 확인: `agentos/terminal/tui/commands.py`
- 확인: `agentos/llm/providers/codex_cli.py`

**사용자에게 보이는 마일스톤:** 구현이 추정이 아니라 현재 AgentOS contract와 existing Codex CLI surface 위에서 시작된다.

- [ ] **Step 1: 현재 AgentOS에 CLI login/status/logout은 있지만 TUI `/login`, `/logout`은 없고 `/status`는 일반 상태 surface임을 확인한다.**

Run: `grep -q '^def login(' agentos/commands/llm.py && grep -q '^def status(' agentos/commands/llm.py && grep -q '^def logout(' agentos/commands/llm.py && ! grep -q '"/login"' agentos/terminal/tui/commands.py && ! grep -q '"/logout"' agentos/terminal/tui/commands.py && grep -q 'SlashCommand("/status", "Show provider, session, hooks, and last turn state"' agentos/terminal/tui/commands.py && echo "PASS tui-auth-gap-confirmed"`
Expected: `PASS tui-auth-gap-confirmed`

### Task 1: slash auth command registry 추가

**파일:**
- 수정: `agentos/terminal/tui/commands.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** `/login`, `/logout`가 command palette, `/help`, autocomplete 대상에 `Codex` 전용 command로 나타나고 `/status` 설명이 auth-aware 상태 surface로 갱신된다.

- [ ] **Step 1: slash command registry에 `/login`, `/logout`를 추가하되 description/hint/help copy에서 Codex 전용 command임을 명시한다.**

Run: `grep -q 'SlashCommand("/login", "Codex login' agentos/terminal/tui/commands.py && grep -q 'SlashCommand("/logout", "Codex logout' agentos/terminal/tui/commands.py && grep -q 'auth status' agentos/terminal/tui/commands.py && echo "PASS tui-auth-commands-planned"`
Expected: `PASS tui-auth-commands-planned`

- [ ] **Step 2: unknown command와 충돌 없이 `/login`, `/logout`, auth-aware `/status` dispatch path를 고정한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "login_command_catalog or logout_command_catalog or status_auth" -q`
Expected: pytest PASS

### Task 2: `/login` orchestration UX

**파일:**
- 수정: `agentos/terminal/tui/app.py`
- 수정: `agentos/commands/llm.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** `/login` 실행 시 사용자는 Codex CLI login이 시작되었는지, 외부 브라우저/승인이 이어질 수 있는지, 완료됐는지, 실패했는지, 다음에 무엇을 해야 하는지를 TUI에서 본다.

- [ ] **Step 1: TUI는 설치된 `agentos` 바이너리를 다시 shell-out하지 않고, `agentos/commands/llm.py`의 sanitized helper를 worker에서 호출한다.**

Run: `grep -q 'def .*login.*payload' agentos/commands/llm.py && uv run pytest tests/test_tui_cli.py -k "login_starts_worker or login_success or login_failure" -q`
Expected: helper 존재 확인 후 pytest PASS

- [ ] **Step 2: `/login` 결과는 authenticated/unauthenticated/failed/missing_cli를 구분해 transcript와 recovery copy로 보여주며, 외부 승인 가능성을 숨기지 않는다.**

Run: `uv run pytest tests/test_tui_cli.py tests/test_codex_provider.py -k "login_recovery or login_missing_cli or login_failed or login_external_approval_copy" -q`
Expected: pytest PASS

- [ ] **Step 3: active provider가 `codex`가 아니면 `/login`은 실행 대신 `/model codex` 전환 안내를 보여준다.**

Run: `uv run pytest tests/test_tui_cli.py -k "login_requires_codex_provider or login_provider_gating" -q`
Expected: pytest PASS

### Task 3: `/status`와 `/logout` auth status surface

**파일:**
- 수정: `agentos/terminal/tui/app.py`
- 수정: `agentos/commands/llm.py`
- 수정: `tests/test_tui_cli.py`
- 수정: `tests/test_codex_provider.py`

**사용자에게 보이는 마일스톤:** 사용자는 현재 TUI 상태와 Codex 인증 상태를 함께 확인하고, 로그아웃 결과를 즉시 본다.

- [ ] **Step 1: `/status`는 기존 TUI 상태 줄을 유지하면서 Codex provider일 때만 auth 상태 블록을 추가하고, non-Codex provider일 때는 비활성 안내만 추가한다.**

Run: `uv run pytest tests/test_tui_cli.py tests/test_codex_provider.py -k "status_authenticated or status_unauthenticated or status_missing_cli or status_failed or status_non_codex_provider" -q`
Expected: pytest PASS

- [ ] **Step 2: unauthenticated 상태에서는 `/login` 재실행, missing_cli 상태에서는 Codex CLI 설치, failed 상태에서는 retry 안내를 명시한다.**

Run: `uv run pytest tests/test_tui_cli.py tests/test_codex_provider.py -k "status_recovery or missing_cli_recovery or login_retry_recovery" -q`
Expected: pytest PASS

- [ ] **Step 3: `/logout`는 provider가 `codex`일 때만 auth action을 수행하고, 이미 로그아웃된 상태는 no-op success with explanation으로 보여준다.**

Run: `uv run pytest tests/test_tui_cli.py tests/test_codex_provider.py -k "logout_flow or logout_idempotent or logout_already_signed_out or status_after_logout" -q`
Expected: pytest PASS

### Task 4: 문서와 보안 경계

**파일:**
- 수정: `docs/cli-reference.md`
- 수정: `tests/test_tui_cli.py`
- 수정: `tests/test_codex_provider.py`

**사용자에게 보이는 마일스톤:** 사용자는 slash auth command 사용법과 한계를 문서에서 보고, transcript/log에는 민감 정보가 남지 않으며 실패 시에도 다음 행동을 이해할 수 있다.

- [ ] **Step 1: CLI reference에 `/login`, `/status`, `/logout` TUI 사용법과 Codex-only/core-only 범위, 외부 브라우저 승인 경계를 추가한다.**

Run: `grep -n '/login\|/status\|/logout\|Codex\|browser' docs/cli-reference.md`
Expected: `/login`, `/status`, `/logout`, Codex, browser 관련 설명 줄이 출력된다.

- [ ] **Step 2: raw token, refresh token, raw callback query, raw stderr가 transcript와 테스트 캡처에 남지 않고, 실패 시에는 sanitized recovery copy만 남는 focused 회귀를 추가한다.**

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_tui_cli.py tests/test_codex_provider.py -k "login and (secret or redact or stderr or recovery)" -q`
Expected: pytest PASS and no raw sentinel/raw stderr leak

### Task 5: closeout verification

**파일:**
- 수정: 이 계획의 완료 증거/구현 결과 섹션

**사용자에게 보이는 마일스톤:** 구현 후 사용자는 무엇이 동작하고 무엇이 아직 native auth plan에 남아 있는지 명확히 판단할 수 있다.

- [ ] **Step 1: focused suite와 public suite를 실행한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "login or logout or status or codex" -q && uv run pytest tests/test_codex_provider.py -q`
Expected: 두 명령 모두 pytest PASS

- [ ] **Step 2: 계획 closeout에 사용 방법, 완료 증거, native auth/transport 미포함 경계를 기록한다.**

Run: `grep -q '## 사용 방법' .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md && grep -q '## 완료 증거' .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md && echo "PASS closeout-sections-present"`
Expected: `PASS closeout-sections-present`

## 리뷰 반영 이력

- [Gate 2 1차] `/status` 기존 의미와 새 auth status가 충돌할 수 있음 → bare `/status`를 없애지 않고 기존 TUI 상태를 유지하면서 Codex auth 블록만 추가하는 원칙을 명시했다.
- [Gate 2 1차] `/login`, `/logout`가 범용 provider command처럼 보임 → command palette/help/description에서 `Codex login`, `Codex logout` 의미를 명시하도록 바꿨다.
- [Gate 2 1차] “TUI를 벗어나지 않고 로그인” 약속이 과함 → 실제 외부 브라우저/승인 경계를 사용자 결과와 Task 2 검증에 명시했다.
- [Gate 2 1차] 실제 호출 경계가 숨겨져 있음 → 설치된 `agentos` 재실행이 아니라 `agentos/commands/llm.py`의 sanitized helper를 TUI worker와 CLI가 공유하는 경계로 고정했다.
- [Gate 2 1차] non-Codex provider에서의 `/login`·`/logout`·`/status` 동작이 불명확함 → `/model codex` 전환 안내와 non-Codex `/status` 비활성 안내를 명시했다.
- [Gate 2 1차] mandatory verification이 `rg`에 의존함 → `grep` 기반 portable verification으로 치환했다.
- [Gate 2 1차] template/Gate 2 섹션과 SSOT 경계, artifact 위치가 부족함 → `리뷰 반영 이력`, closeout placeholder, SSOT 근거, exact review artifact path를 추가했다.

## 리뷰 반영 이력

- [Gate 2 1차] `/status` 기존 의미와 새 auth status가 충돌할 수 있음 → bare `/status`를 없애지 않고 기존 TUI 상태를 유지하면서 Codex auth 블록만 추가하는 원칙을 명시했다.
- [Gate 2 1차] `/login`, `/logout`가 범용 provider command처럼 보임 → command palette/help/description에서 `Codex login`, `Codex logout` 의미를 명시하도록 바꿨다.
- [Gate 2 1차] “TUI를 벗어나지 않고 로그인” 약속이 과함 → 실제 외부 브라우저/승인 경계를 사용자 결과와 Task 2 검증에 명시했다.
- [Gate 2 1차] 실제 호출 경계가 숨겨져 있음 → 설치된 `agentos` 재실행이 아니라 `agentos/commands/llm.py`의 sanitized helper를 TUI worker와 CLI가 공유하는 경계로 고정했다.
- [Gate 2 1차] non-Codex provider에서의 `/login`·`/logout`·`/status` 동작이 불명확함 → `/model codex` 전환 안내와 non-Codex `/status` 비활성 안내를 명시했다.
- [Gate 2 1차] mandatory verification이 `rg`에 의존함 → `grep` 기반 portable verification으로 치환했다.
- [Gate 2 1차] template/Gate 2 섹션과 SSOT 경계, artifact 위치가 부족함 → `리뷰 반영 이력`, closeout placeholder, SSOT 근거, exact review artifact path를 추가했다.
- [Gate 2 2차] `plan-reviewer` PASS, `principle-auditor` PASS/CLEAN, `usability-reviewer` PASS artifact를 `.agents/traces/reviews/2026-07-23-agentos-tui-codex-slash-login/`에 기록했고, 구현 전 재검증이 완료됐다.

## 구현 결과
- TUI slash command catalog에 `/login`, `/logout`를 추가하고, `/status`를 Codex auth-aware 상태 surface로 확장했다.
- `agentos/commands/llm.py`에 sanitized payload helper를 추가해 Typer command와 TUI worker가 같은 in-process contract를 공유하도록 정리했다.
- active provider가 `codex`가 아닐 때는 `/login`·`/logout`가 실행 대신 `/model codex` 전환 안내를 보여주고, `/status`는 기존 footer 상태를 유지한 채 Codex auth 비활성 안내만 덧붙이도록 했다.
- `/logout`는 이미 로그아웃된 상태를 no-op success with guidance로 처리하고, 문서에 외부 browser approval 경계를 추가했다.

## 사용 방법
- TUI에서 provider가 `codex`가 아니면 먼저 `/model codex`를 실행한다.
- `/login`은 Codex CLI account-login 흐름을 시작하고, 필요하면 외부 browser approval이 이어질 수 있음을 transcript에 안내한다.
- `/status`는 기존 TUI session/footer 상태와 함께 Codex auth 상태 또는 비활성 recovery copy를 보여준다.
- `/logout`는 현재 Codex CLI session을 종료하거나, 이미 signed out 상태면 no-op 안내를 보여준다.

## 완료 증거
- PASS `uv run pytest tests/test_tui_cli.py -k "login or logout or status or codex" -q` → `8 passed, 58 deselected`
- PASS `uv run pytest tests/test_codex_provider.py tests/test_cli_contract.py -q` → `23 passed`
- PASS `grep -n '/login\|/status\|/logout\|Codex\|browser' docs/cli-reference.md` → slash auth commands와 browser boundary 줄 출력 확인
- PASS `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md` (closeout 직전) → `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`

## 아카이브 결정
이 계획은 active에 남아 있으며, 사용자가 명시적으로 archive를 요청하면 `plan_lifecycle.py archive .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md --status 완료`로 이동한다. closeout 이후 본문이 바뀌었으므로 Gate 2 artifact hash는 사전-구현 계획 시점 기준으로 남는 것이 정상이다.

## 장기 재사용 근거

- 현재 AgentOS에서 이미 가진 재사용 표면:
  - `agentos llm login --provider codex --json`
  - `agentos llm status --provider codex --json`
  - `agentos llm logout --provider codex --json`
- 이번 계획에서 재사용할 패턴:
  - TUI slash command가 기존 sanitized contract를 orchestration layer로 감싼다
  - 기존 `/status` command 이름은 유지하고, auth-aware surface로 확장한다
  - login UX는 method selector 같은 새 transport UI를 추가하지 않고 결과/복구 안내 중심으로 닫는다
  - provider가 `codex`가 아닐 때는 command를 숨기기보다 명시적 recovery copy로 비활성 의미를 드러낸다

## 단순성 검토

- 요청에 없던 기능을 추가했는가? 아니오. 오히려 browser/device-code selector 같은 초안 과범위를 제거하고 existing Codex CLI orchestration으로 축소했다.
- 더 단순한 대안은? `/login`만 구현할 수 있었지만, 사용자가 상태 확인과 종료까지 함께 원했고 현재 existing CLI contract도 세 동작을 모두 제공하므로 `/login`·auth-aware `/status`·`/logout`를 최소 세트로 유지했다.
