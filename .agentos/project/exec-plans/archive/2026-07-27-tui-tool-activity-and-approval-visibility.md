# TUI 도구 활동 정보량·승인 팝업 가시성 개선 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-27<br>
> implementation_completed_at: 2026-07-27<br>
> implementation_duration: 단일 세션<br>

> **usability_review_required:** true<br>
> usability_review_reason: 이 계획은 TUI 대화창에 표시되는 도구 활동(Activity · Tool) 메시지 수와 승인 팝업(ConfirmToolScreen)의 레이아웃을 바꾼다. 둘 다 사용자가 매 턴 직접 보고 조작하는 화면이다.<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `2026-07-26-codex-tool-result-correlation` 구현 이후 실제 TUI 사용 중 발견된 두 가지 UX 결함을 고친다: (1) 도구 호출 하나당 두 개의 별도 Activity 블록(호출 1개 + 결과 1개)이 쌓여 대화창이 실제 대화보다 도구 잡음으로 채워진다. (2) 도구 승인 팝업(ConfirmToolScreen) 본문이 길면(`bash` 명령 최대 2000자, `edit`는 old/new 합쳐 최대 4000자) 팝업 컨테이너의 `max-height: 24`를 넘겨 승인/거부 옵션 목록이 화면에서 잘려 보이지 않는 경우가 생긴다.

**사용자 결과 요약:**
- 이 계획이 완료되면 TUI 사용자는 도구 호출 한 번당 "호출 → 결과"가 하나로 합쳐진 Activity 블록 한 개만 보게 되어 대화창을 스크롤하는 부담이 준다. 승인 팝업은 본문이 아무리 길어도 승인/거부 옵션이 항상 화면 안에 남아 있어, 팝업이 뜬 걸 알면서도 무엇을 눌러야 할지 못 찾는 상황이 사라진다.
- 대상: AgentOS TUI(`agentos`, `agentos run`)를 사용하는 모든 사용자. CLI plain 모드(`run_interactive`)는 이미 도구 호출을 `읽는 중: ...` 한 줄로만 표시해 이 문제가 없으므로 대상이 아니다.
- 일상 사용에서 달라지는 것: 도구를 많이 쓰는 요청(예: 여러 파일 조회) 후 대화창 스크롤량이 절반 가까이 줄고, `bash`/`edit` 같은 긴 승인 팝업에서도 스크롤해서 옵션을 찾을 필요 없이 항상 보인다.
- 바뀌지 않는 것: 도구 실행 로직, 승인 정책(거부 기본값, 매 호출 승인, `--yolo` 예외), `approval_prompt()`가 보여주는 내용의 양(꼬리 잘림 없이 전체 텍스트 유지, `_elide_middle` 정책 그대로), `render_event()`의 truncate(120자) 규칙, `mock_tool` 같은 커스텀 도구 렌더러, CLI plain 모드 출력.

**의존성 분석:**
- 외부 의존성: 없음. 변경은 로컬 TUI 렌더링 로직과 Textual 위젯 레이아웃(둘 다 이미 사용 중인 라이브러리 API)에 한정되며, fake/mock provider와 `textual`의 `run_test()` 헤드리스 파일럿으로 전부 검증한다.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, `HISTORY.md`, `.agents/traces/reviews/2026-07-27-tui-tool-activity-and-approval-visibility/`의 리뷰 증거.
- Durable Result Surface: `agentos/terminal/tui/app.py`, `agentos/terminal/tui/widgets.py`, `docs/cli-reference.md`, `tests/test_tui_cli.py`.
- Documentation-only exception: 없음.

**진행 상태:** 구현·전체 검증·Gate 2 리뷰 모두 완료.

**아키텍처:**
- `AgentOSTui.run_stream()`(`agentos/terminal/tui/app.py`, 약 682-881행)의 이벤트 루프가 `tool_call`/`tool_result` 이벤트마다 각각 새 `ChatMessage`를 추가하는 대신, `tool_call`에서 만든 메시지 위젯을 기억해뒀다가 이어지는 `tool_result`에서 그 위젯의 텍스트를 갱신(merge)하는 방식으로 바뀐다. `render_event()`가 만드는 문자열 내용·순서(`Tool call: ...` 다음 줄에 결과)는 그대로 이어붙이기만 하고, `renderers.py`의 렌더링 규칙(truncate, 커스텀 도구 렌더러, redaction)은 손대지 않는다.
- `ConfirmToolScreen`(`agentos/terminal/tui/widgets.py`)의 `compose()`가 본문 `Static`을 `VerticalScroll` 컨테이너로 감싸 본문에만 높이 상한을 주고, `OptionList`(승인/거부)는 그 바깥의 형제 위젯으로 유지해 컨테이너 `max-height: 24` 안에서 항상 렌더링되도록 한다. 본문 내용 자체(꼬리 잘림 방지용 `_elide_middle`)는 바꾸지 않고, 길면 스크롤해서 볼 수 있게만 한다.

**기술 스택:** Python 3, Textual, pytest, `textual.pilot`.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 완료 |
| 완료됨 | Task 1(도구 활동 메시지 병합)·Task 2(승인 팝업 스크롤·옵션 항상 노출)·Task 3(문서·전체 회귀) 모두 구현·검증 |
| 현재 위치 | 완료 증거 기록, 사용자 요청 시 archive/commit/PR 대기 |
| 다음 단계 | 사용자 요청 시 commit/PR 준비 |
| 완료 신호 | focused TUI test·전체 suite(433 passed)·`git diff --check`가 모두 PASS — 모두 확인됨 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 도구 활동 메시지 통합 | 도구 호출 1건당 Activity 블록 1개만 보인다(호출+결과 통합). | `agentos/terminal/tui/app.py` | focused TUI activity test PASS |
| 2. 승인 팝업 옵션 항상 노출 | 본문이 길어도 승인/거부 옵션이 팝업 안에서 항상 보인다. | `agentos/terminal/tui/widgets.py` | 긴 본문 회귀 테스트(geometry 단정) PASS |
| 3. 전체 회귀·문서 반영 | 문서가 새 동작을 정확히 설명하고, 기존 기능은 깨지지 않는다. | `docs/cli-reference.md`, 전체 테스트 | full suite·`git diff --check` PASS |

## 구현 단계

### Task 1: 도구 호출+결과를 TUI 대화창에서 Activity 블록 하나로 합친다

**파일:**
- 수정: `agentos/terminal/tui/app.py`
- 수정: `tests/test_tui_cli.py`

- [ ] `run_stream()` 안의 `add_tool_message` 클로저(현재 `-> None`, `Transcript.add_message()`의 반환값을 버림)를 `-> ChatMessage`로 바꿔 생성한 위젯을 반환하게 한다. 대응하는 `Transcript.update_message()` 호출용 클로저 `update_tool_message(message: ChatMessage, text_content: str) -> None`을 새로 추가한다.
- [ ] 이벤트 루프 상단에 `current_tool_message: ChatMessage | None = None`을 선언한다. `tool_call` 이벤트에서는 `current_tool_message = self.call_from_thread(add_tool_message, rendered)`로 새 메시지를 만들고 반환된 위젯을 저장한다(현재 코드는 `self.call_from_thread(add_tool_message, rendered)`의 반환값을 버리므로, 이 대입을 추가하는 것 자체가 변경 사항이다).
- [ ] 이어지는 `tool_result` 이벤트에서 `current_tool_message`가 있으면 새 메시지를 추가하지 않고, `render_event(payload)`로 얻은 결과 텍스트를 `f"{current_tool_message.text}\n{rendered}"`로 이어붙여 `self.call_from_thread(update_tool_message, current_tool_message, merged_text)`로 갱신한 뒤 `current_tool_message = None`으로 초기화한다. `current_tool_message`가 없으면(예: 대응하는 `tool_call` 이벤트 없이 `tool_result`만 온 방어적 상황) 기존처럼 `self.call_from_thread(add_tool_message, rendered)`로 새 메시지를 추가한다.
- [ ] `render_event()`가 만드는 문자열 자체(“Tool call: name(args)”, “Tool result: ...” 또는 등록된 커스텀 도구 렌더러 출력)는 변경하지 않는다 — 오직 그 결과를 같은 `ChatMessage`에 넣을지, 새 메시지에 넣을지만 바꾼다.
- [ ] `tests/test_tui_cli.py`의 `test_tool_border_tool_call_has_tool_class`(현재 “Mock provider emits tool_call + tool_result → at least 2 tool messages”, `assert len(tool_messages) >= 2`)를 실제 mock provider 동작에 맞춰 `assert len(tool_messages) == 2`로 갱신한다. `agentos/llm/providers/mock.py`의 `stream_context()`는 도구 호출이 없는 상태(`tool_already_executed=False`)에서 먼저 `request.tools[0]`(TUI 기본 도구 순서상 `read`)에 대한 맨 tool_call만 내보내고, `ConversationRuntime`이 이를 실행한 뒤 별도 `tool_result` 이벤트를 내며 provider를 재호출한다. 재호출 시(`tool_already_executed=True`) provider가 `reasoning`+`tool_call(mock_tool)`+`tool_result(mock_tool)`+`message_delta`+`done`을 낸다. 즉 한 턴에 (read 호출, read 결과) + (mock_tool 호출, mock_tool 결과) 총 두 번의 호출/결과 라운드가 있으므로, 병합 후에도 tool 메시지는 정확히 2개(라운드당 1개)다. docstring/주석을 “각 라운드의 tool_call과 그 tool_result는 하나의 tool 메시지로 합쳐지며, 이 mock 흐름은 두 라운드를 거치므로 tool 메시지는 정확히 2개다”로 고친다.
- [ ] `test_activity_turn_contract_preserves_event_order_and_turn_id`의 `assert [m.role for m in messages] == ["reasoning", "tool", "tool", "assistant"]`를 `== ["reasoning", "tool", "assistant"]`로 갱신한다. 같은 테스트의 `presentation.index("Activity · Thinking") < presentation.index("Activity · Tool") < presentation.index("AgentOS · complete")` 단정은 그대로 유지한다(Activity · Tool 헤더가 여전히 정확히 한 번 등장해야 함).
- [ ] 기존 `test_tui_shows_tool_execution_progress_and_final_answer_for_read_tool_call`(“Tool call: read(” 부분 문자열 단정)과 `test_transcript_shows_process_events_before_final_answer`(`mock_tool` 커스텀 테이블 렌더러 단정)는 병합 후에도 같은 문자열이 같은 메시지 안에 그대로 남아있어야 하므로 수정하지 않는다 — 이 두 테스트가 통과하는 것 자체가 “내용은 그대로, 메시지 개수만 준다”는 불변식의 회귀 증거다.

Run: `uv run pytest -q tests/test_tui_cli.py -k "tool_border or activity_turn_contract or tool_execution_progress or process_events_before_final_answer"`
Expected: 선택된 모든 테스트 통과. `tool_border` 테스트가 정확히 2개의 tool 메시지(read 라운드 1개 + mock_tool 라운드 1개)를 단정하고, `activity_turn_contract` 테스트가 `["reasoning", "tool", "assistant"]` 순서를 단정하며, 나머지 두 테스트는 병합 후에도 원래 문자열이 여전히 존재함을 확인한다.

### Task 2: 승인 팝업 본문이 길어도 승인/거부 옵션이 항상 보이게 한다

**파일:**
- 수정: `agentos/terminal/tui/widgets.py`
- 수정: `tests/test_tui_cli.py`

- [ ] `ConfirmToolScreen.compose()`에서 본문 `Static(self._body, id="confirm-body")`를 `VerticalScroll(id="confirm-body-scroll")`로 감싼다. `OptionList("거부 (기본)", "승인", id="confirm-options")`는 이 스크롤 컨테이너 밖, `#confirm-container`(`Vertical`)의 형제 자식으로 유지한다.
- [ ] `DEFAULT_CSS`에 `#confirm-body-scroll { max-height: 14; margin-bottom: 1; }`를 추가한다. `#confirm-container`의 기존 `max-height: 24`는 그대로 둔다(제목 약 2줄 + 스크롤 본문 최대 14줄 + 옵션 약 4줄 + padding/border로 24줄 예산 안에 들어오도록 계산됨).
- [ ] `on_mount()`가 `#confirm-options`를 포커스하는 기존 동작(`options.highlighted = 0; options.focus()`)은 그대로 유지한다 — 기본 포커스가 옵션에 가 있으므로 화살표 키 동작은 바뀌지 않는다.
- [ ] `describe_tool_call()`/`approval_prompt()`(`agentos/llm/tools/approval.py`)의 내용·길이 정책(`_elide_middle`, `MAX_COMMAND_CHARS=2000`, `CONTENT_PREVIEW_LINES=5`)은 변경하지 않는다 — 위험한 명령의 꼬리가 화면 밖으로 잘리지 않아야 한다는 기존 불변식을 그대로 지킨다.
- [ ] `tests/test_tui_cli.py`에 새 회귀 테스트를 추가한다: `_elide_middle` 상한에 가까운 긴 `bash` 명령(예: 2000자에 가까운 문자열)으로 `ConfirmToolScreen`을 만들어 `push_screen`한 뒤, (a) `#confirm-options`가 마운트되어 있고(`is_mounted`), 렌더링된 높이가 0보다 큰지(`options.region.height > 0`), (b) `#confirm-options`의 화면 좌표(`options.region.y + options.region.height`)가 `#confirm-container`의 화면 좌표 범위 안에 들어오는지, (c) `#confirm-body-scroll`의 `virtual_size.height`가 자신의 `size.height`보다 커서(스크롤 가능 상태) 넘치는 내용이 옵션 영역을 밀어내지 않고 스크롤로 흡수됐는지를 단정한다.

Run: `uv run pytest -q tests/test_tui_cli.py -k "confirm_screen"`
Expected: 기존 `test_tui_confirm_screen_defaults_focus_to_deny`와 신규 긴 본문 테스트 모두 PASS. 신규 테스트가 긴 본문에서도 옵션 위젯이 화면 영역 안에서 실제로 렌더링됨(0보다 큰 높이, 컨테이너 범위 내 좌표)을 단정한다.

### Task 3: 전체 회귀 검증과 문서 반영

**파일:**
- 수정: `docs/cli-reference.md`
- 수정 없음(검증): 나머지

- [ ] `docs/cli-reference.md`의 “Activity” 절(“Tool results also appear as `Activity · Tool`. ...” 부분)을 갱신해, 도구 호출과 그 결과가 이제 Activity 블록 하나에 함께 표시된다는 사실과, `mock_tool`처럼 등록된 커스텀 렌더러가 있는 도구는 여전히 그 렌더러의 출력(예: 표)이 같은 블록 안에 이어붙는다는 점을 설명한다.
- [ ] 같은 문서의 승인 화면 절(“The approval screen shows the full action, not a truncated summary.” 인근)에 한 문장을 추가해, TUI에서 본문이 길면 스크롤 영역 안에서 스크롤되고 승인/거부 옵션은 항상 화면에 남는다는 점을 설명한다.
- [ ] 전체 스위트와 공백 오류 검사를 fresh run한다.

Run: `uv run pytest -q && git diff --check`
Expected: 전체 테스트 통과(회귀 없음, Task 1/2에서 의도적으로 갱신한 두 단정 제외), `git diff --check` 출력 없음 및 exit 0.

## 범위와 비목표

- 포함: TUI(`agentos/terminal/tui/app.py`)의 도구 호출/결과 메시지 병합, TUI 승인 팝업(`ConfirmToolScreen`)의 스크롤 가능한 본문·항상 보이는 옵션, 관련 문서·테스트 갱신.
- 제외: `render_event()`/`renderers.py`의 truncate·redaction·커스텀 도구 렌더러 로직 변경, `approval_prompt()`/`describe_tool_call()`의 내용·길이 정책 변경, CLI plain 모드(`run_interactive`)의 출력, 도구 실행·승인 정책(`confirm_tool_call`, `--yolo`, 턴당 도구 호출 상한) 변경, 새 슬래시 커맨드나 새 설정 옵션 추가.

## 리뷰 반영 이력

- 1차 `plan-reviewer` FAIL: (1) 존재하지 않는 `AgentOSTui._run_turn()` 참조(실제 이름은 `run_stream()`), (2) `add_tool_message`가 이미 `ChatMessage`를 반환한다는 잘못된 가정(`-> None`이며 반환값을 버리고 있었음) — `update_tool_message` 클로저 신설과 반환값 캡처 단계를 추가해 해결, (3) mock provider가 "hello" 한 턴에 tool_call/tool_result 쌍 1개만 낸다는 잘못된 사실 — 실제로는 두 라운드(맨 `read` 호출+런타임 결과, 이어서 `reasoning`+`tool_call(mock_tool)`+`tool_result(mock_tool)`)를 낸다는 것을 실제 코드(`agentos/llm/providers/mock.py`)와 헤드리스 파일럿 실행으로 확인해 목표를 `== 2`로 수정.
- 2차 라운드에서 `plan-reviewer`·`principle-auditor`가 각각 독립적으로 Task 1의 `Run:`/`Expected:` 서술(77행)이 수정된 체크리스트(72행, `== 2`)와 불일치("정확히 1개"로 남아있음)한다는 동일한 결함을 발견 — 한 줄 수정으로 해결.
- 3차 라운드: `plan-reviewer`·`principle-auditor`·`usability-reviewer` 모두 최종본에 대해 PASS, `review_artifacts.py record`로 Gate 2 증거 파일 3종 기록. `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-27-tui-tool-activity-and-approval-visibility.md` → `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`.

## 구현 결과

- `agentos/terminal/tui/app.py`(`AgentOSTui.run_stream()`): `add_tool_message`가 생성한 `ChatMessage`를 반환하도록 바꾸고, 새 `update_tool_message()` 클로저를 추가했다. `tool_call` 이벤트에서 만든 메시지를 `current_tool_message`에 저장해뒀다가, 이어지는 `tool_result` 이벤트에서 같은 메시지에 결과 텍스트를 개행으로 이어붙여 갱신한다(대응하는 `tool_call`이 없는 방어적 상황에서는 기존처럼 새 메시지를 추가). `render_event()`가 만드는 문자열 자체는 변경하지 않았다.
- `agentos/terminal/tui/widgets.py`(`ConfirmToolScreen`): 본문 `Static`을 `VerticalScroll(id="confirm-body-scroll", max-height: 14)`로 감싸고, `OptionList`는 그 바깥 형제 위젯으로 유지했다. `#confirm-container`의 `max-height: 24`는 그대로 두었다. `approval_prompt()`/`describe_tool_call()`의 내용·길이 정책은 손대지 않았다.
- `docs/cli-reference.md`: Activity 절에 도구 호출+결과가 한 블록으로 합쳐진다는 설명, 승인 화면 절에 TUI에서 본문이 길면 스크롤되고 옵션은 항상 보인다는 설명을 추가했다.
- `tests/test_tui_cli.py`: `test_tool_border_tool_call_has_tool_class`를 `== 2`(라운드당 1개 병합 메시지) 단정과 `await_transcript` 기반 완료 대기로 갱신, `test_activity_turn_contract_preserves_event_order_and_turn_id`를 `["reasoning", "tool", "assistant"]`로 갱신, 신규 `test_tui_confirm_screen_keeps_options_visible_with_long_body`를 추가(옵션 위젯이 0보다 큰 높이로 컨테이너 범위 안에 렌더링되고, 본문 스크롤 영역의 `virtual_size.height`가 자신의 `size.height`보다 커서 실제로 넘친 내용을 흡수했음을 단정). 수정 전 코드로 되돌려 이 신규 테스트가 `NoMatches: No nodes match '#confirm-body-scroll'`로 실패함을 직접 확인해 회귀 가드로서 유효함을 검증했다.

## 사용 방법

별도 설정 없이 `agentos`/`agentos run`으로 TUI를 실행하면 자동 적용된다. 도구를 호출하는 요청을 보내면 호출+결과가 Activity · Tool 블록 하나로 보이고, `write`/`edit`/`bash` 승인 팝업은 본문이 길어도 승인/거부 옵션이 항상 화면에 남는다(본문이 길면 스크롤해서 전체 내용을 볼 수 있다).

## 완료 증거

- PASS `uv run pytest -q tests/test_tui_cli.py -k "tool_border or activity_turn_contract or tool_execution_progress or process_events_before_final_answer"` (5 passed)
- PASS `uv run pytest -q tests/test_tui_cli.py -k "confirm_screen"` (2 passed)
- PASS `uv run pytest -q` (433 passed, 회귀 없음)
- PASS `git diff --check` (출력 없음, exit 0)
- PASS Gate 2: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-27-tui-tool-activity-and-approval-visibility.md` → `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`

## 아카이브 결정

구현·검증 후 사용자가 명시적으로 요청할 때만 archive한다.
