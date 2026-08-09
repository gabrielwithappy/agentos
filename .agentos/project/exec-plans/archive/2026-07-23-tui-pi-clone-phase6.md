# AgentOS TUI — pi TUI 클로닝 Phase 6: 입력 상호작용 기반 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-23<br>
> reviewed: false<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **usability_review_required:** true

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** Phase 5 완료 후 pi TUI의 입력 상호작용 패턴을 AgentOS의 Python/Textual 구조에 맞게 이식할 공통 계약과 첫 사용자 기능 묶음(키바인딩·slash/argument 자동완성)을 구현한다.

**사용자 결과:** 사용자는 `/capabilities`에서 이식 기능의 준비 상태를 확인하고, slash command와 지원하는 argument를 Tab으로 완성하며, 기존 메시지 포커스 이동과 충돌 없는 단축키 안내를 받는다.

**진행 상태:** 계획 초안 작성 완료, Gate 2 리뷰 대기. Phase 5가 완료 전이면 Task 0에서 중단한다.

**아키텍처:** `capabilities.py`는 기능 상태와 근거를 한 곳에서 선언한다. `keybindings.py`는 사용자 동작과 기본 키를 명시적으로 매핑하고 충돌을 fail-closed로 보고한다. `completion.py`는 Textual 위젯과 독립적인 suggestion/apply protocol을 제공하며, `Composer`는 slash 입력일 때만 completion screen을 열어 Phase 4의 Tab/Shift+Tab focus ring을 보존한다.

**기술 스택:** Python 3.12+, Textual, pytest/Pilot, 기존 `uv` 개발 환경. pi는 read-only reference checkout(`3da591ab`)이며 의존성으로 추가하지 않는다.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | Intent Sheet, pi revision 기반 입력 아키텍처 조사, 장기 클로닝 로드맵 초안 |
| 현재 위치 | Gate 2 리뷰 전. Phase 5 완료 여부를 아직 실행하지 않음 |
| 다음 단계 | 리뷰 통과 후 Task 0에서 Phase 5·pi reference preflight를 확인 |
| 완료 신호 | 모든 planned `Run:`이 PASS이고 `/capabilities`, 자동완성, hotkey 문서가 같은 registry를 가리킴 |

## 세션 인계 체크포인트

- 현재 완료 범위: 계획·Intent Sheet·pi 입력 아키텍처 조사와 로드맵을 작성했다.
- 미완료 작업: Gate 2 리뷰, Phase 5 완료 확인, 코드 구현과 verification.
- 다음 세션 첫 작업: Phase 5 closeout과 pi reference checkout을 Task 0 preflight 명령으로 확인한다.
- 아직 안 한 검증: 이 계획의 Gate 0 command, focused/public test suite, review artifacts.
- 관련 HISTORY checkpoint: Phase 4 closeout `[2026-07-22T22:22:06Z]`; Phase 5는 현재 리뷰 대기다.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | pi 기반 입력 UX의 현재/보류 상태와 일관된 command completion을 얻는다. |
| 누구를 위한 것인가? | AgentOS TUI를 사용하는 개발자와 이후 TUI 기능을 확장하는 구현자. |
| 일상 사용에서 무엇이 달라지는가? | `/` 입력 후 Tab으로 command와 지원 argument를 고르고, `/hotkeys`에서 실제 action과 키를 확인한다. |
| 무엇은 바뀌지 않는가? | provider/credential, JSONL session schema, hook schema, Phase 5 settings UI, 일반 입력의 Tab focus cycle은 바뀌지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 안전한 시작 | Phase 5 완료와 동일 pi reference를 확인한 뒤만 구현 시작 | Phase 5 plan, pi checkout | `PASS phase5-complete`, `PASS pi-reference-ready` |
| 1. 이식 상태 표시 | `/capabilities`에서 구현/보류 기능과 다음 조건을 확인 | `capabilities.py`, `commands.py`, `app.py` | focused capability tests PASS |
| 2. 일관된 단축키 | hotkey 안내와 실제 Composer/transcript 동작이 action registry에서 파생 | `keybindings.py`, `app.py`, `widgets.py` | conflict + focus regression tests PASS |
| 3. 명령 자동완성 | slash command와 지원 argument를 Tab으로 선택·삽입 | `completion.py`, `widgets.py`, `app.py` | Pilot completion tests PASS |
| 4. 장기 추적 | 사용자 문서와 pi 로드맵이 실제 이식 상태를 설명 | `docs/cli-reference.md`, roadmap | docs/reference checks PASS |
| 5. 회귀 없음 | TUI·secret redaction 경계가 유지 | `tests/` | public suite + redaction suite PASS |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, `.agents/mission/plan.json`, exec-plan board, `.agents/traces/research/2026-07-23-tui-pi-clone-phase6-pi-tui-input-architecture.md`.
- durable result surface: `agentos/terminal/tui/{capabilities,keybindings,completion}.py`, `agentos/terminal/tui/{app,widgets,commands}.py`, `tests/test_tui_cli.py`, `docs/cli-reference.md`, `.agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md`.
- documentation-only exception: 없음. 현재 문서는 Phase 6 구현을 위한 evidence이며, 사용자에게 남는 결과는 TUI 동작·테스트·CLI 문서다.
- reader-first boundary: 이 섹션과 사용자 표는 설명 데이터이며 approval, protected-path, reviewer authority, prompt hierarchy를 변경하지 않는다.

## 의존성 분석

- 외부 의존성: 아래에 선언함.
- 스캔 기준: pi reference checkout, Python/Textual runtime, `uv run pytest` commands, source comparison command, 현행 Phase 5 completion state.
- 새 package, credential, network, MCP, live provider runtime 의존성: 없음.

## 의존성 게이트

### phase5-complete
- name: phase5-complete
- type: nonstandard-local-tool
- required: true
- purpose: `/settings` ownership과 구현 표면이 안정된 뒤 Phase 6을 시작한다.
- preflight:
  Run: `rg -q '^> \*\*상태:\*\* 완료' .agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase5.md && rg -q '^> reviewed: true' .agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase5.md && echo "PASS phase5-complete"`
  Expected: `PASS phase5-complete`
- fallback:
  available: false
  reason: Phase 5의 `/settings` 화면과 Phase 6 capability/command registry의 ownership을 분리할 수 없다.
- failure_behavior: NEEDS_CONTEXT

### pi-reference-checkout
- name: pi-reference-checkout
- type: nonstandard-local-tool
- required: true
- purpose: pi의 `AutocompleteProvider`와 `KeybindingsManager`를 read-only 설계 증거로 재검증한다.
- preflight:
  Run: `test -d /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/.git && git -C /home/gabriel/agent/prj-agent/agentos-workspace/references/pi rev-parse --verify 3da591ab^{commit} >/dev/null && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/autocomplete.ts && test -f /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/keybindings.ts && echo "PASS pi-reference-ready"`
  Expected: `PASS pi-reference-ready`
- fallback:
  available: false
  reason: reference revision이 없으면 source comparison 완료 기준을 객관적으로 판단할 수 없다.
- failure_behavior: NEEDS_CONTEXT

## 파일 구조

- 생성: `agentos/terminal/tui/capabilities.py` — 기능 id, 상태, owner, 선행 조건을 선언하는 registry.
- 생성: `agentos/terminal/tui/keybindings.py` — action id, default key, description, conflict validation.
- 생성: `agentos/terminal/tui/completion.py` — completion item/provider/apply protocol과 built-in slash/argument provider.
- 수정: `agentos/terminal/tui/commands.py` — `/capabilities` 등록과 command argument metadata.
- 수정: `agentos/terminal/tui/widgets.py` — Composer completion request/accept contract와 suggestion screen.
- 수정: `agentos/terminal/tui/app.py` — registry 기반 hotkeys/capabilities rendering, completion orchestration, existing Tab precedence 보존.
- 수정: `tests/test_tui_cli.py` — capability, key conflict, slash/argument completion, Tab focus regression Pilot tests.
- 수정: `docs/cli-reference.md` — `/capabilities`, Tab completion, supported argument와 비첨부 경계 안내.
- 수정: `.agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md` — Phase 6 실제 closeout/evidence 갱신.
- 수정: `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md` — Phase 6 완료 상태만 갱신; 기존 Phase 4 변경과 충돌하면 중단하고 조정한다.

## 구현 작업

### Task 0: Phase 5 및 pi reference preflight

**파일:**
- 수정 없음
- 확인: `.agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase5.md`
- 확인: `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/`

**사용자에게 보이는 마일스톤:** 구현이 이전 Phase와 검증된 pi source 기준 위에서만 시작된다.

- [ ] **Step 1: Phase 5 closeout과 pi reference revision을 mutation 전에 확인한다.**

Run: `rg -q '^> \*\*상태:\*\* 완료' .agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase5.md && rg -q '^> reviewed: true' .agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase5.md && echo "PASS phase5-complete"`
Expected: `PASS phase5-complete`; 실패하면 `NEEDS_CONTEXT`로 중단한다.

- [ ] **Step 2: 고정 pi revision과 필요한 입력 계약 파일을 확인한다.**

Run: `test -d /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/.git && git -C /home/gabriel/agent/prj-agent/agentos-workspace/references/pi rev-parse --verify 3da591ab^{commit} >/dev/null && rg -q "interface AutocompleteProvider" /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/autocomplete.ts && rg -q "class KeybindingsManager" /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/keybindings.ts && echo "PASS pi-reference-ready"`
Expected: `PASS pi-reference-ready`; 실패하면 `NEEDS_CONTEXT`로 중단한다.

### Task 1: TUI capability registry와 `/capabilities`

**파일:**
- 생성: `agentos/terminal/tui/capabilities.py`
- 수정: `agentos/terminal/tui/commands.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** 사용자는 어떤 pi 기능이 AgentOS에 구현됐고 어떤 기능이 선행 조건 때문에 보류됐는지 한 명령으로 확인한다.

- [ ] **Step 1: immutable capability record와 상태 enum을 만들고, Phase 5/6·보류 기능을 source evidence와 함께 등록한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "capability_registry" -q`
Expected: PASS — registry id가 중복되지 않고 각 보류 기능에 reason과 prerequisite가 있으며, secret/provider diagnostic을 포함하지 않는다.

- [ ] **Step 2: `/capabilities` command와 sanitized transcript renderer를 연결한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "capabilities_command" -q`
Expected: PASS — Pilot에서 `/capabilities` 입력 후 capability id, status, next condition이 표시되고 Composer로 focus가 복귀한다.

### Task 2: 선언형 키바인딩 registry

**파일:**
- 생성: `agentos/terminal/tui/keybindings.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정: `agentos/terminal/tui/widgets.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** `/hotkeys`의 안내가 실제 Composer, transcript, overlay 동작과 일치하며 충돌한 기본 키는 테스트에서 즉시 드러난다.

- [ ] **Step 1: action id, default key, 설명을 한 registry로 선언하고 중복 키 conflict validation을 만든다.**

Run: `uv run pytest tests/test_tui_cli.py -k "keybinding_registry or keybinding_conflict" -q`
Expected: PASS — 정상 registry는 conflict 없음, 테스트 fixture의 중복 key는 명시적 validation error를 낸다.

- [ ] **Step 2: Composer와 `AgentOSTui`의 현재 key dispatch를 registry action으로 연결한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "hotkeys_registry or focus_cycle or composer_kill_yank" -q`
Expected: PASS — `/hotkeys`가 registry 설명을 표시하고 Phase 4 focus cycle 및 kill/yank shortcut 회귀가 없다.

### Task 3: slash command와 argument completion protocol

**파일:**
- 생성: `agentos/terminal/tui/completion.py`
- 수정: `agentos/terminal/tui/commands.py`
- 수정: `agentos/terminal/tui/widgets.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** `/theme`, `/model`, `/session`처럼 지원하는 명령은 Tab에서 command와 argument 후보를 표시하고 선택 결과가 Composer에 삽입된다.

- [ ] **Step 1: Textual-independent completion item/provider/apply protocol과 slash/argument provider를 작성한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "completion_provider or command_argument_completion" -q`
Expected: PASS — command name, `theme`, `model`, `session` argument 후보가 현재 registry/런타임 값에서 생성되고 unknown input에는 empty result를 낸다.

- [ ] **Step 2: Composer suggestion screen을 protocol에 연결하고 선택·취소·focus 복귀를 구현한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "completion_screen or tab_opens_filtered_command_palette" -q`
Expected: PASS — slash 입력에서 Tab은 completion을 열고 Enter는 선택값을 삽입하며 Esc는 원문을 보존하고 Composer에 focus를 돌린다.

- [ ] **Step 3: slash가 아닌 입력의 Tab/Shift+Tab은 completion으로 전환하지 않고 Phase 4 focus cycle을 유지한다.**

Run: `uv run pytest tests/test_tui_cli.py -k "completion_tab_precedence or focus_cycle" -q`
Expected: PASS — 일반 입력에서는 latest-message focus cycle이, slash 입력에서는 completion이 각각 실행된다.

### Task 4: 사용자 문서와 pi 클로닝 로드맵 closeout

**파일:**
- 수정: `docs/cli-reference.md`
- 수정: `.agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md`
- 수정: `.agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md`

**사용자에게 보이는 마일스톤:** 사용자는 무엇이 자동완성되는지와 `@` 경로 입력이 실제 파일 첨부가 아니라는 경계를 문서에서 확인한다. 구현자는 다음 Phase의 선행 조건을 다시 조사하지 않는다.

- [ ] **Step 1: CLI reference에 `/capabilities`, Tab completion, 지원 argument와 비첨부 경계를 추가한다.**

Run: `rg -n "/capabilities|Tab.*자동완성|첨부" docs/cli-reference.md`
Expected: `/capabilities`, Tab completion, `@` 입력이 attachment를 수행하지 않는다는 안내를 포함한 매치 줄이 출력된다.

- [ ] **Step 2: roadmap과 feature inventory의 Phase 6 상태·검증 evidence를 갱신한다.**

Run: `rg -n "Phase 6|capability|keybinding|자동완성" .agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md .agentos/project/reference/implementation/2026-07-22-pi-hermes-tui-feature-inventory.md`
Expected: 두 문서 모두 Phase 6 implementation status와 follow-up prerequisite를 출력한다.

### Task 5: 회귀·경계·lifecycle verification

**파일:**
- 수정: `tests/test_tui_cli.py`
- 수정: 이 계획의 완료 증거/구현 결과 섹션
- 수정: `HISTORY.md` closeout checkpoint

**사용자에게 보이는 마일스톤:** 새 입력 UX가 기존 TUI, secret redaction, automation boundary를 깨지 않았다는 재현 가능한 증거가 남는다.

- [ ] **Step 1: focused TUI와 public suite를 실행한다.**

Run: `uv run pytest tests/test_tui_cli.py -q && uv run pytest tests/ -q`
Expected: 두 명령 모두 PASS; 신규 실패 없음.

- [ ] **Step 2: secret redaction과 pi source/roadmap mapping을 확인한다.**

Run: `AGENTOS_TEST_SECRET=s3cr3t uv run pytest -k redact -q && test -d /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src && rg -q "interface AutocompleteProvider" /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/autocomplete.ts && rg -q "class KeybindingsManager" /home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/tui/src/keybindings.ts && rg -q "Phase 6" .agentos/project/reference/implementation/2026-07-23-pi-tui-cloning-roadmap.md && echo "PASS phase6-boundary-and-mapping"`
Expected: redaction suite PASS followed by `PASS phase6-boundary-and-mapping`.

- [ ] **Step 3: lifecycle board를 갱신하고 closeout checkpoint를 기록한다.**

Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && git diff --check && echo "PASS phase6-lifecycle-clean"`
Expected: `PASS phase6-lifecycle-clean`.

## HISTORY checkpoint 규약

- 구현/검증/closeout checkpoint에는 `plan=.agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase6.md`를 포함한다.
- roadmap 또는 research evidence를 남길 때는 `artifact=<path>`를 함께 기록한다.
- generic harness health checkpoint에는 이 태그를 강제하지 않는다.

## 단순성 검토

- 요청에 없던 기능이나 컴포넌트를 추가했는가? capability, keybinding, completion module은 사용자가 요구한 장기 클로닝 구조와 첫 다기능 구현 묶음을 위한 최소 공통 계층이다.
- 더 단순한 대안은? 개별 `if event.key`와 palette handler를 계속 늘릴 수 있으나, pi 기능 이식마다 같은 키 충돌·UI coupling을 반복하므로 선택하지 않는다.
- 제외로 단순성을 유지한 항목: keybinding 저장 UI, `@` attachment semantics, diff/image/compaction backend, provider·session schema 변경.

## 리뷰 반영 이력

- 초안 작성 — 2026-07-23. Intent Sheet의 long-term architecture 우선순위와 source-mapping quality gate를 반영했다.
- Gate 2 서브에이전트 리뷰(plan-reviewer, principle-auditor, usability-reviewer)는 아직 요청하지 않았다. `reviewed: false`를 유지하며, 구현 전 해당 리뷰 artifact와 PASS를 확보해야 한다.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 완료 증거

(구현 후 작성)

## 아카이브 결정

2026-07-26, 사용자 요청에 따라 archive 처리. 사유: `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md`가 AgentOS 제품 방향을 "AgentOS control plane은 vendor execution plane(Codex/Claude/OpenCode)의 실제 대화·tool loop·model/plugin 기능을 복제하지 않는다"로 확정했다. 이 계획은 pi TUI의 입력 상호작용(키바인딩·slash/argument 자동완성)을 AgentOS Textual 구조로 그대로 이식하는 pi 클로닝 로드맵의 후속 단계이며, `reviewed: false`로 Gate 2 리뷰 전이었고 선행 조건인 Phase 5도 미완료였다. 0006 채택 이후 신규 vendor UX 이식 확장은 별도 reviewed implementation plan(0006을 근거로 삼는)에서 재검토되어야 하므로, 이 초안은 구현하지 않고 archive로 이동한다. 코드 변경은 없었다(계획 문서만 존재).
