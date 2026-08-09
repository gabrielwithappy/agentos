# AgentOS TUI 도구 로그 밀도 개선 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-30<br>
> reviewed: false<br>
> **usability_review_required:** true<br>
> user_request: AgentOS TUI의 과도한 도구 사용 로그를 pi의 표시 방식을 근거로 줄이는 계획을 작성한다.<br>
> active_agent: Codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: plan/tui-tool-log-ux)<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0p5Nk<br>
> implementation_started_at: 2026-07-30T11:26:05Z<br>
> implementation_completed_at: 2026-07-30T12:10:31Z<br>
> implementation_duration: 44m 26s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 도구를 여러 번 사용한 턴에서도 AgentOS TUI transcript가 핵심 진행 상태를 짧게 보여 주고, 필요할 때만 도구 상세를 한 번에 확인하게 한다.

**사용자 결과:** 사용자는 완료된 도구 실행의 이름·성공/실패 요약을 바로 보고, `Ctrl+O`로 해당 턴을 포함한 모든 도구 활동의 호출 인자와 결과를 펼치거나 다시 접을 수 있다.

**진행 상태:** raw provider stderr/raw environment 음성 검증과 light/dark/`NO_COLOR` 도구 활동 coverage를 보완한 뒤 fresh verification을 완료했다. 계획은 사용자의 명시적 archive 요청 전까지 active에 유지한다.

**아키텍처:** 기존 `tool_call`→`tool_result` 병합과 `render_event()`의 리댁션/도구별 renderer는 보존한다. `ChatMessage`에 도구 상세의 표시 상태와 요약 표현을 추가하고, `AgentOSTui`가 전역 확장 상태와 `Ctrl+O` action을 소유한다. 도구 실행·이벤트·세션 저장 경로는 바꾸지 않는다.

**기술 스택:** Python 3, Textual, Rich, pytest.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 기본 축약·실행 중 상태·결과 선행 방어, `Ctrl+O` 전환, `/hotkeys` 발견 경로, 4개 SVG 증거, 문서·요구사항·안전 추적, focused/redaction/boundary/manifest 검증 |
| 현재 위치 | closeout 및 최신 Gate 2 재검토 |
| 다음 단계 | 사용자 요청 시 archive 또는 PR 준비 |
| 완료 신호 | focused TUI/visual/redaction 검증이 PASS이고, 좁은·넓은 terminal SVG에서 요약과 펼친 상세가 모두 확인됨 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 도구를 많이 사용해도 transcript를 가리지 않는 짧은 도구 상태 행과, 필요 시 모든 상세를 보는 `Ctrl+O` 전환 |
| 누구를 위한 것인가? | AgentOS TUI로 에이전트 작업을 관찰하는 개발자와 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 기본 화면에는 도구 이름과 성공/실패 상태만 남고, 호출 인자·전체 결과는 요청했을 때만 보인다 |
| 무엇은 바뀌지 않는가? | 도구 실행, 승인, session/JSONL 기록, `/tools` 요약, 리댁션, 도구별 renderer 및 provider 이벤트 계약 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 기준선 확정 | 현재 도구 병합·리댁션 동작이 보존될 기준 확보 | `tests/test_tui_cli.py`, `tests/test_tui_visual_contract.py` | focused baseline PASS |
| 1. 기본 축약 도구 활동 | 완료된 도구가 짧은 상태 요약으로 표시됨 | `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py` | 기본 축약 및 실행 중 표시 테스트 PASS |
| 2. 상세 전환 | `Ctrl+O` 한 번으로 모든 도구 상세를 열고 다시 닫음 | `agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`, `docs/cli-reference.md` | keyboard interaction, `/hotkeys`, SVG evidence PASS |
| 3. 안전한 인계 | 도움말·요구사항·회귀 테스트가 동일한 행동을 설명함 | `docs/cli-reference.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/04-safety-risk-verification.md`, tests | focused/public boundary/redaction PASS |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/mission/plan.json`, `.agentos/project/exec-plans/README.md`, `HISTORY.md`, `.agents/traces/research/2026-07-30-tui-tool-log-density-pi-analysis.md`
- durable result surface: `agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/renderers.py`의 보존된 안전 경계, `tests/test_tui_cli.py`, `tests/test_tui_visual_contract.py`, `docs/cli-reference.md`, 프로젝트 요구사항·안전 문서
- documentation-only exception: 없음. 문서는 실제 TUI 동작과 회귀 검증을 안내하는 보조 표면이다.

## 세션 중단 대비 체크포인트

| 필드 | 현재 값 |
|---|---|
| 현재 완료 범위 | Task 0~3 구현 및 closeout 검증 완료 |
| 미완료 작업 | 없음; 사용자 archive/PR 결정만 남음 |
| 다음 세션 첫 작업 | 사용자 요청 시 archive 또는 PR 준비 |
| 아직 안 한 검증 | 없음; latest focused/redaction/boundary/manifest 명령은 완료 증거에 기록 |
| 관련 HISTORY checkpoint | 2026-07-30 TUI tool-log density closeout checkpoint |

## 범위와 비목표

- 포함: 기본 축약된 완료 도구 활동, `Ctrl+O` 전역 상세 전환, 실행 중 활동의 명확한 진행 표시, UI/안전/문서 회귀 검증.
- 제외: pi 코드/의존성 추가, 개별 도구별 토글, 상세 상태 영속화, 새 slash command, 도구 실행/승인 정책, provider event schema, session/JSONL 형식 변경.
- pi는 UX 근거만 제공하며 AgentOS의 구현·배포 의존성이 아니다.

## 파일 구조

| 파일 | 변경 | 역할 |
|---|---|---|
| `agentos/terminal/tui/widgets.py` | 수정 | tool `ChatMessage`의 요약/상세 표현 및 전환 가능한 표시 상태를 소유 |
| `agentos/terminal/tui/app.py` | 수정 | 전역 도구 상세 상태, `Ctrl+O` binding/action, stream 중 도구 활동 갱신을 연결 |
| `agentos/terminal/tui/renderers.py` | 필요 시 수정 | 현재의 안전한 도구 텍스트/도구별 renderer 결과에서 요약에 필요한 안전 메타데이터만 제공; 불필요하면 수정하지 않음 |
| `tests/test_tui_cli.py` | 수정 | 축약/확장, 상관관계, 실행 중 상태, `/tools`, 리댁션 회귀를 검증 |
| `tests/test_tui_visual_contract.py` | 수정 | 80×24 및 140×40 Textual SVG에서 요약/상세와 geometry를 검증 |
| `docs/cli-reference.md` | 수정 | 기본 표시, `Ctrl+O`, 안전한 복구/상세 확인 방법을 사용자 언어로 안내 |
| `.agentos/project/02-product-scope-and-requirements.md` | 수정 | TUI 가독성 요구사항과 acceptance 추적을 기록 |
| `.agentos/project/04-safety-risk-verification.md` | 수정 | 축약이 리댁션·도구 상태·정상 복구를 약화하지 않는 검증 근거를 기록 |
| `scripts/verify-tui-reference-boundary.sh` | 수정 | 외부 TUI 의존성만 정확하게 검사해 일반 구현 용어의 오탐을 방지 |

## 의존성 분석

- 외부 의존성: 없음.
- 스캔 기준: Python/Textual/Rich/pytest는 기존 repository baseline이며, planned `Run:`은 로컬 `.venv`, repository scripts, 이미 checkout에 있는 pi 조사 근거만 사용한다.
- 런타임 가정: Textual의 `run_test()`와 `export_screenshot()`은 existing test suite에서 이미 사용되는 로컬 테스트 표면이다. 외부 서비스, credential, plugin, MCP, network, live provider는 실행하지 않는다.

## 구현 원칙과 수용 기준

1. 완료된 활동은 도구 이름, 성공/오류 상태, 안전하게 축약된 결과 요약을 기본으로 보인다. 빈 결과도 상태가 보이게 한다.
2. 실행 중인 활동은 어떤 도구가 진행 중인지 알 수 있게 유지하고, 완료된 활동에만 축약을 적용한다.
3. `Ctrl+O`는 모든 현재 transcript 도구 활동의 상세(호출 인자와 전체 결과)를 열거나 닫는다. 새 활동은 현재 전역 상태를 상속한다.
4. `tool_call`과 대응 `tool_result`는 현재처럼 단일 활동 블록으로 병합한다. 결과만 먼저 온 방어 경로도 화면에 남긴다.
5. `TOOL_RENDERERS`, `/tools`의 마지막 턴 요약, `render_event()`의 sanitize/truncate 동작을 보존한다.
6. 어느 표시 모드에서도 secret sentinel, raw provider stderr, raw environment가 출력되지 않는다.
7. keyboard action, 80×24/140×40 geometry, screenshot/SVG, light/dark 및 `NO_COLOR`의 역할 경계를 automated Textual test로 증명한다. 이것은 browser parity 주장이 아니라 terminal UI의 실제 render/interaction 증거다.

### Task 0: 기준선과 구현 경계 고정

**파일:**
- 수정: `tests/test_tui_cli.py`
- 수정: `tests/test_tui_visual_contract.py`
- 참조(수정 금지): `.agents/traces/research/2026-07-30-tui-tool-log-density-pi-analysis.md`

**사용자에게 보이는 마일스톤:** 기존 도구 표시와 보안 경계가 새 UI 변경 중에도 사라지지 않는다는 자동 검증 기준이 준비된다.

- [x] **Step 1: 현재 도구 활동 병합·요약·리댁션 기준선을 focused suite로 확인한다.**

Run: `.venv/bin/python -m pytest tests/test_tui_cli.py -q -k "tool or redact or tools_command"`

Expected: `PASS` 및 기존 `tool_call`/`tool_result` 병합, `/tools`, tool renderer, secret-redaction 테스트 통과

- [x] **Step 2: 테스트에 독립적인 완료 도구 활동 fixture를 추가해 성공·오류·빈 결과·결과 선행 방어 경로를 표현한다.**

Run: `.venv/bin/python -m pytest tests/test_tui_cli.py -q -k "tool_activity or tool_result or tool_call"`

Expected: `PASS` 및 각 fixture가 단일 도구 활동 블록/안전한 상태 요약을 검증

### Task 1: 완료 도구 활동을 기본 축약으로 표현

**파일:**
- 수정: `agentos/terminal/tui/widgets.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정(필요 시): `agentos/terminal/tui/renderers.py`
- 수정: `tests/test_tui_cli.py`

**사용자에게 보이는 마일스톤:** 완료된 도구는 짧은 상태 요약으로 남고, 실행 중인 도구는 진행 중임을 계속 알린다.

- [x] **Step 1: `ChatMessage` 또는 동등한 기존 위젯에 tool 전용 요약/상세 표시 상태를 추가한다.**

도구 호출·결과 원문은 메시지 모델에 유지하고, presentation layer에서만 완료 상태의 기본 요약과 상세 본문을 선택한다. 요약에는 도구 이름과 완료/오류 상태를 포함하며, 인자·결과는 기존 sanitizer를 거친 문자열만 사용한다.

Run: `.venv/bin/python -m pytest tests/test_tui_cli.py -q -k "tool_activity_default_collapsed or tool_result or redact"`

Expected: `PASS` 및 완료 도구의 기본 화면에 상세 인자/전체 결과가 없고 상태 요약·리댁션은 유지

- [x] **Step 2: stream 처리에서 실행 중 표시와 완료 후 축약 전환을 연결한다.**

`tool_call`은 진행 중 메시지를 만들고, 대응 `tool_result`가 합쳐진 뒤에만 축약 가능한 완료 상태로 바꾼다. 결과 선행 방어 경로는 안전한 단일 활동을 만들고, 다음 호출/결과 쌍의 상관관계를 깨지 않는다.

Run: `.venv/bin/python -m pytest tests/test_tui_cli.py -q -k "tool_activity_running or tool_call_tool_result or tool_result_without_call"`

Expected: `PASS` 및 실행 중/완료/결과 선행 세 경우가 모두 한 개의 안전한 활동으로 표시

### Task 2: `Ctrl+O`로 전체 도구 상세 전환 제공

**파일:**
- 수정: `agentos/terminal/tui/app.py`
- 수정: `agentos/terminal/tui/widgets.py`
- 수정: `tests/test_tui_cli.py`
- 수정: `tests/test_tui_visual_contract.py`

**사용자에게 보이는 마일스톤:** 사용자는 한 키로 transcript의 도구 호출 인자와 결과 상세를 열고 닫을 수 있다.

- [x] **Step 1: App binding과 action으로 전역 도구 상세 상태를 만들고, 현재 및 새 도구 활동에 적용한다.**

`Ctrl+O`가 composer focus에서도 동작하게 하고, 전환 직후 transcript가 다시 렌더링/스크롤된다. 동일 키는 현재 TUI의 다른 action과 충돌하지 않는지 확인한다. `_HOTKEYS_TABLE`과 `/hotkeys` 출력에 `Ctrl+O`가 “도구 상세 열기/닫기”로 나타나, 기본 축약 화면에서도 사용자가 상세 확인 방법을 찾을 수 있게 한다.

Run: `.venv/bin/python -m pytest tests/test_tui_cli.py -q -k "ctrl_o or tool_activity_toggle or tool_activity_new_inherits or hotkeys"`

Expected: `PASS` 및 첫 `Ctrl+O`는 상세 표시, 둘째 `Ctrl+O`는 기본 요약 복귀, 새 도구 활동은 현재 상태 상속, `/hotkeys`에 `Ctrl+O`와 도구 상세 안내 표시

- [x] **Step 2: 좁은/넓은 terminal의 실제 Textual render와 key interaction을 SVG evidence로 검증한다.**

80×24와 140×40에서 축약·확장 전후 SVG를 `.agents/traces/visual/2026-07-30-tui-tool-log-density/`에 export한다. light/dark 및 `NO_COLOR`에서 test는 상태 헤더, 요약, 상세의 존재/부재, activity left boundary, transcript/composer 경계와 width overflow가 없음을 확인한다. sentinel을 포함한 호출 인자·결과, raw provider stderr와 raw environment 표식을 주입해 transcript와 네 SVG 모두에 해당 값이 없음을 assert한다.

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_tui_visual_contract.py -q -k "tool_activity"`

Expected: `PASS` 및 `collapsed-80x24.svg`, `expanded-80x24.svg`, `collapsed-140x40.svg`, `expanded-140x40.svg`가 생성되고, 모든 SVG/화면에서 sentinel·raw stderr·raw environment 부재 및 geometry/interaction/light/dark/NO_COLOR assertions 통과

### Task 3: 사용법·요구사항·안전 검증을 동기화

**파일:**
- 수정: `docs/cli-reference.md`
- 수정: `.agentos/project/02-product-scope-and-requirements.md`
- 수정: `.agentos/project/04-safety-risk-verification.md`
- 수정: `tests/test_tui_cli.py`
- 수정: `tests/test_tui_visual_contract.py`

**사용자에게 보이는 마일스톤:** 사용자는 왜 도구 결과가 짧게 보이는지, 상세를 어떻게 열지, 오류·보안 상태가 계속 보이는지를 문서와 TUI에서 같은 의미로 확인한다.

- [x] **Step 1: CLI 안내와 root docs에 기본 축약, `Ctrl+O`, 유지되는 안전 경계를 사용자 언어로 기록한다.**

문서는 기본 도구 표시는 축약이며 `Ctrl+O`로 상세를 열고 다시 닫는다는 점, 오류 상태, `/hotkeys`와 `/tools`에서 상세 확인 방법을 찾는다는 점을 설명한다. provider event/session/JSONL contract가 바뀌지 않음을 requirement/risk trace에 명시한다.

Run: `rg -q "Ctrl\\+O" docs/cli-reference.md && rg -q "Ctrl\\+O" agentos/terminal/tui/app.py && rg -q "도구" .agentos/project/02-product-scope-and-requirements.md && rg -q "리댁션" .agentos/project/04-safety-risk-verification.md && echo "PASS tui-tool-log-density-docs"`

Expected: `PASS tui-tool-log-density-docs`

- [x] **Step 2: focused, public-boundary, secret-redaction 검증을 실행하고 실패하면 원인을 고친 뒤 같은 명령을 재실행한다.**

Run: `.venv/bin/python -m pytest tests/test_cli_contract.py tests/test_interactive_cli.py tests/test_cli_hooks.py tests/test_tui_cli.py tests/test_tui_visual_contract.py -q && bash scripts/verify-tui-reference-boundary.sh && echo "PASS tui-tool-log-density-focused-suite"`

Expected: `PASS tui-tool-log-density-focused-suite`

Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_tui_cli.py -q -k redact && echo "PASS tui-tool-log-density-redaction"`

Expected: `PASS tui-tool-log-density-redaction`

## Simplicity Gate

- 사용자 요청에 없던 기능/컴포넌트: 없음. 전역 `Ctrl+O` 상태와 tool message의 presentation state는 pi에서 검증된 최소 상호작용을 AgentOS의 기존 TUI 경로에 추가하는 데 필요한 범위다.
- 더 단순한 대안: 결과 텍스트를 무조건 truncate만 하는 방식은 사용자가 전체 결과를 안전하게 다시 볼 방법이 없어 채택하지 않는다.
- 제외를 유지하는 이유: 개별 토글, persistent preference, 새 명령어, event/session schema 변경은 기본 로그 밀도 문제 해결에 필요하지 않다.

## 리뷰 반영 이력

- 초안 작성: pi의 `ToolExecutionComponent`/`Ctrl+O` 전역 확장 패턴과 현재 AgentOS의 `run_stream()` 병합 경로를 근거로 범위를 확정했다.
- [Gate 2 1차 · plan-reviewer] `## 구현 결과`/`## 사용 방법` 누락 → TEMPLATE.md의 두 완료 섹션을 추가했다.
- [Gate 2 1차 · usability-reviewer] 기본 축약에서 `Ctrl+O` 발견 경로 누락 → `_HOTKEYS_TABLE`/`/hotkeys` 안내와 해당 자동 검증을 Task 2에 추가하고 문서 경로를 Task 3에 명시했다.
- [Gate 2 1차 · principle-auditor] 새 축약/확장 화면의 sentinel·raw stderr·raw environment 및 light/dark/`NO_COLOR` 증거 부족 → Task 2 SVG/interaction 검증에 모든 음성 assertion과 terminal mode coverage를 추가했다.
- [Gate 2 2차] plan-reviewer PASS, principle-auditor PASS/APPROVE, usability-reviewer PASS를 확보했다. 최종 Gate 2 artifact는 이력 반영 후 재검토 결과만 기록한다.

## 구현 후 완료 증거 형식

구현 완료 시 이 섹션에 Task별 완료 항목, 아래 fresh verification 출력, SVG evidence 경로, 변경된 문서의 traceability를 기록한다. 구현을 시작하려면 먼저 유효한 독립 Gate 2 PASS 증적에 근거해 `reviewed: true`여야 하며, 완료 상태 전환은 구현과 fresh verification 뒤에만 한다.

## 구현 결과

- 완료 도구 활동은 `Activity · Tool · <name> · complete|failed`와 sanitized 결과 요약으로 기본 축약된다. 실행 중 활동은 호출 상세를 유지한다.
- `Ctrl+O`는 composer focus에서도 모든 transcript 도구 활동의 sanitized 호출 인자·결과 상세를 열고 다시 접는다. 새 활동은 현재 표시 모드를 상속한다.
- tool call/result 병합, `/tools`, provider event/session JSONL, renderer와 redaction 경계는 유지된다.
- `scripts/verify-tui-reference-boundary.sh`는 일반 코드·출처 주석이 아닌 외부 TUI runtime 의존성만 exact token으로 검사한다.

## 사용 방법

일반 TUI 사용 중 완료된 도구 행은 짧은 상태와 결과 요약만 보여 준다. 전체 호출 인자와 결과를 보려면 `Ctrl+O`를 누르고, 다시 누르면 축약 화면으로 돌아간다. `/hotkeys`에서도 이 단축키를 찾을 수 있다. 실패한 도구도 `failed` 상태와 sanitized 요약을 남긴다.

## 완료 증거

- `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_tui_cli.py -q -k redact` → `3 passed`.
- `.venv/bin/python -m pytest tests/test_cli_contract.py tests/test_interactive_cli.py tests/test_cli_hooks.py tests/test_tui_cli.py tests/test_tui_visual_contract.py -q` → `167 passed`.
- `bash scripts/verify-tui-reference-boundary.sh` → `PASS tui-reference-not-copied`.
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → integrity PASS.
- SVG: `.agents/traces/visual/2026-07-30-tui-tool-log-density/{collapsed,expanded}-{80x24,140x40}.svg`.

## 아카이브 결정

구현·fresh verification·closeout이 끝나도 이 계획은 active에 남는다. 사용자가 명시적으로 archive를 요청할 때만 `plan_lifecycle.py archive <plan-path> --status 완료`를 사용한다.
