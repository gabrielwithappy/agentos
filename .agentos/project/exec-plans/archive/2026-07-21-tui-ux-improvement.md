# AgentOS TUI (Pi TUI Parity) 개선 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-21<br>
> reviewed: true (Gate 2 3차: plan-reviewer/principle-auditor/usability-reviewer 모두 PASS, 증거 `.agents/traces/reviews/2026-07-21-tui-ux-improvement/`)<br>
> implementation_started_at: 2026-07-21T11:31:00Z<br>
> implementation_completed_at: 2026-07-21T11:48:46Z<br>
> implementation_duration: 약 18분<br>
> usability_review_required: true<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- Pi TUI와 AgentOS TUI(Textual 기반)의 사용 만족도를 100% 동일한 수준까지 끌어올리는 것.
- 사용자가 "pi 에서 제공하는 llm이 동작하는 과정에 대한 설명이나 slash command등 llm을 사용하기 위한 풍부한 TUI기능이 제공되지 않는다"고 지적한 구체적 격차, 즉 (1) LLM이 응답을 만들기까지 무엇을 하고 있는지(추론/도구 호출)에 대한 설명 부재, (2) LLM 사용을 돕는 슬래시 커맨드의 부족을 해소한다.

**사용자 결과 요약:**
- **에디터 UX / 히스토리 UX (완료됨):** 이미 이전 작업에서 Shift+Enter 줄바꿈, 방향키 히스토리, 채팅 말풍선, 스트리밍 스로틀링이 구현되어 있다. (근거: `git log` 상 `6d2ebd7`, `b018cea`, `f08ce29`, `9f6c42c` 커밋과 `.agentos/project/exec-plans/2026-07-21-tui-transcript-improvement.md`.) 이번 계획은 이 부분을 다시 구현하지 않는다.
- **LLM 동작 과정 설명 (신규):** 사용자가 메시지를 보내면, 최종 답변 텍스트만 보이는 것이 아니라 AgentOS/Codex가 무엇을 하고 있는지(추론 중, 도구 호출 중, 도구 결과)가 대화창에 구분되는 스타일로 표시된다. mock 공급자에서도 동일한 형태로 시연 가능하다.
- **풍부한 슬래시 커맨드 (신규):** `/tools` 명령으로 마지막 턴에서 어떤 도구가 호출되었는지 확인할 수 있고, `/usage` 명령으로 마지막 턴의 입력/출력 문자 수를 확인할 수 있다. `/help` 팔레트에 새 명령이 함께 표시된다.
- **바뀌지 않는 부분:** CLI 커맨드라인 로직과 세션/후크 저장 방식, 실제 LLM 공급자 인증/전송 방식은 바뀌지 않는다. 오직 이벤트 표현(타입 확장), TUI 렌더링, 슬래시 커맨드 카탈로그만 변경된다. Provider(모델) 실시간 전환 기능은 이번 범위에 포함하지 않는다.

**의존성 분석:**
- 외부 의존성: 없음. 기존 Textual(`pyproject.toml`에 `textual>=6.0.0`, 현재 잠금 버전 8.2.8), Rich, 그리고 이미 저장소에 존재하는 `codex` CLI 연동 경로(`agentos/llm/providers/codex_cli.py`)만 사용한다. 새 외부 서비스, 새 패키지, 새 자격증명을 추가하지 않는다.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서
- Durable Result Surface: `agentos/llm/types.py`, `agentos/llm/providers/mock.py`, `agentos/llm/providers/codex_cli.py`, `agentos/terminal/tui/renderers.py`, `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py`, `agentos/terminal/tui/commands.py`, `agentos/commands/run.py`, `docs/cli-reference.md`

**진행 상태:** Gate 2 3차 리뷰까지 완료 — `plan-reviewer`/`principle-auditor`/`usability-reviewer` 모두 PASS. 구현 착수 대기 중

**아키텍처:**
- `LLMEvent`/`EventType` (`agentos/llm/types.py`): `reasoning`, `tool_call`, `tool_result` 타입 추가. 세 타입 모두 기존 `text`/`metadata` 필드만 재사용하고 새 필드나 새 스키마 버전을 만들지 않는다.
- `MockProvider.stream_once`: 데모/테스트 목적으로 `reasoning` → `tool_call` → `tool_result` → `message_delta` 순서의 이벤트를 방출.
- `CodexCliProvider._parse_output_events`: codex `exec --json` 스트림에서 이미 버려지던 `reasoning`, `function_call`/`local_shell_call`(및 대응 `*_output`) item을 인식해 각각 새 이벤트 타입으로 변환.
- `render_event` (`renderers.py`): 새 이벤트 타입을 아래 고정 문구로만 렌더링한다(원문 타입 식별자를 그대로 노출하는 raw fallback 경로로 빠지지 않도록 각 타입을 명시적으로 분기한다):
  - `reasoning` → `Thinking: {text}`
  - `tool_call` → `Tool call: {name}({args_summary})` (`args_summary`는 `key=value` 콤마 나열, 120자 초과 시 말줄임)
  - `tool_result` → `Tool result: {summary}` (120자 초과 시 말줄임)
  - 위 세 타입 모두 기존 `sanitize()` 경유를 유지해 시크릿 유출을 막는다.
- `Transcript`/`ChatMessage` (`widgets.py`): `role="process"`(추론/도구) 메시지를 assistant 답변과 분리된 스타일(무채색/축소 강조)로 렌더링.
- `AgentOSTui.run_stream` (`app.py`): `reasoning`/`tool_call`/`tool_result` 페이로드를 assistant 텍스트에 이어붙이지 않고 별도 transcript 메시지로 추가. 마지막 턴의 도구 호출 목록(`self.last_tool_calls`)과 사용량(`self.last_usage`)을 턴마다 갱신해 상태로 보관하고, 새 턴 시작 시 초기화한다.
- `commands.py`: `/tools`, `/usage` 슬래시 커맨드 추가, `command_palette_text()`/`/help`에 자동 반영. 정확한 출력 문구는 마일스톤 4를 참조. `/tools`의 `name(args) -> result` 줄도 `render_event`와 동일한 120자 말줄임 규칙을 재사용해 두 표시(실시간 transcript vs `/tools` 조회)가 서로 다른 길이로 잘리지 않게 한다.
- `agentos/commands/run.py` / `docs/cli-reference.md` (JSONL 계약 정합성): `docs/cli-reference.md:68`은 현재 "Provider event names remain `start`, `message_delta`, `done`, and `error`"라고 닫힌 계약을 선언한다. 이 계획은 **이 계약을 확장하는 쪽으로 명시적으로 결정한다** — `agentos run --once --json`은 새 이벤트 타입도 그대로(필터링 없이) sanitized JSON 라인으로 통과시키고, 문서를 "Provider event names include `start`, `message_delta`, `reasoning`, `tool_call`, `tool_result`, `done`, and `error`."로 갱신한다. 기존 소비자는 알 수 없는 타입을 무시할 수 있는 형태(각 라인이 독립된 JSON object)이므로 하위 호환은 유지되며, `agentos.cli-event/v1` 스키마 버전은 그대로 둔다. 이 변경은 회귀 테스트로 고정한다(마일스톤 3 검증 참조).

**기술 스택:**
- Python 3.12, Textual 8.2.8 (`pyproject.toml` 요구사항: `textual>=6.0.0`), Rich

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 및 검증 완료 |
| 완료됨 | 마일스톤 0-5 전체 구현. 전체 테스트 `uv run pytest tests/ -q` 83 passed |
| 현재 위치 | 완료 및 사용자 확인 대기 |
| 다음 단계 | 없음 (사용자 요청 시 archive/commit/PR 준비) |
| 완료 신호 | 마일스톤 0의 기존 회귀 수정 포함, mock 공급자 기준 TUI에서 추론/도구 호출/도구 결과가 답변과 구분되어 표시되고, `/tools`·`/usage` 명령이 동작하며, `tests/test_tui_cli.py` 및 전체 테스트가 통과할 때 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 0. 기존 회귀 테스트 수정 (선행 작업) | 사용자가 보내는 메시지가 대화창에 `You: ...` 접두어와 함께 화면에 다시 표시됨(커밋 `9f6c42c`가 `Transcript.render()`를 삭제하면서 `_format_message()`가 더 이상 호출되지 않아 실제 화면에서도 접두어가 사라진 상태였음 — 이번 마일스톤이 화면 표시 자체를 복원). 함께, 테스트는 더 이상 존재하지 않는 `Transcript.render()` 문자열이 아니라 실제로 마운트된 `ChatMessage` 콘텐츠를 검증하도록 고쳐짐 | `agentos/terminal/tui/widgets.py` (`Transcript.add_message`), `tests/test_tui_cli.py` (mounted `ChatMessage.text`를 읽는 헬퍼로 교체) | `Run:` `uv run pytest tests/test_tui_cli.py -q` / `Expected:` 전체 PASS (현재 `10 failed, 12 passed`로 재현됨을 `uv run pytest tests/test_tui_cli.py -q` 실행으로 확인함 — plan-reviewer 2차 리뷰 지적 사항) |
| 1. 에디터 UX (Composer) 재설계 | Enter(전송), Shift+Enter(줄바꿈), Up/Down(히스토리), kill-ring, paste marker 지원 | `agentos/terminal/tui/widgets.py` (Composer) | 마일스톤 0 완료 후 확인. `Run:` `uv run pytest tests/test_tui_cli.py -k composer -q` / `Expected:` PASS |
| 2. 대화 히스토리 (Transcript) 재설계 | 채팅 말풍선 UI, 스트리밍 시 깜빡임 없는 렌더링 | `agentos/terminal/tui/widgets.py`, `app.py` | 마일스톤 0 완료 후 확인. `Run:` `uv run pytest tests/test_tui_cli.py -k "transcript or markdown" -q` / `Expected:` PASS |
| 3. LLM 동작 과정 표시 | 메시지 전송 후 `Thinking: ...`, `Tool call: name(args)`, `Tool result: ...` 같은 고정 문구가 최종 답변 앞에 구분된 스타일로 순서대로 나타나고, 마지막에만 답변이 markdown으로 렌더링됨. 실제 시크릿 값은 어떤 줄에도 노출되지 않음 | `agentos/llm/types.py`, `agentos/llm/providers/mock.py`, `agentos/llm/providers/codex_cli.py`, `agentos/terminal/tui/renderers.py`, `agentos/terminal/tui/widgets.py`, `agentos/terminal/tui/app.py`, `agentos/commands/run.py`, `docs/cli-reference.md` | `Run:` `uv run pytest tests/test_tui_cli.py -k "process or reasoning or tool_call" -q` / `Expected:` PASS. `Run:` `AGENTOS_TEST_SECRET=AGENTOS_SENTINEL_SECRET uv run pytest tests/ -k redact -q` (mock `tool_call`/`tool_result`에 시크릿 센티널을 주입하는 신규 테스트 포함) / `Expected:` PASS, 센티널 문자열이 렌더링 결과에 없음. `Run:` `AGENTOS_TUI_TEST_PLAIN=1 uv run agentos --provider mock <<< $'hello\n/exit\n'` / `Expected:` 출력에 `Thinking:`, `Tool call:`, `Tool result:` 줄이 그대로(raw 타입 식별자 없이) 보임. `Run:` `uv run agentos run --once "hi" --provider mock --json \| grep -o '"type": *"[a-z_]*"' \| sort -u` / `Expected:` `reasoning`, `tool_call`, `tool_result` 포함, `docs/cli-reference.md`의 갱신된 이벤트 목록과 일치 |
| 4. 풍부한 슬래시 커맨드 | `/tools` 입력 시 도구 호출이 없으면 `No tool calls in the last turn. Next: send a message that needs a tool.`, 있으면 `Tools used in the last turn:` 뒤에 `name(args) -> result` 줄 목록이 보임. `/usage` 입력 시 턴이 없으면 `No usage yet. Next: send a message.`, 있으면 `Last turn usage: input N chars, output M chars`가 보임. `/help`와 `docs/cli-reference.md`의 명령 목록에 두 명령이 함께 표시됨 | `agentos/terminal/tui/commands.py`, `agentos/terminal/tui/app.py`, `docs/cli-reference.md` | `Run:` `uv run pytest tests/test_tui_cli.py -k "tools_command or usage_command or palette" -q` / `Expected:` PASS (빈 상태 문구와 채워진 상태 문구를 모두 검증). `Run:` `grep -n "/tools\|/usage" docs/cli-reference.md` / `Expected:` 두 명령 모두 출력됨 |
| 5. 전체 안정성 검증 | 기존 TUI 명령어와 LLM 상호작용이 깨지지 않음 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` 전체 PASS (기존 실패 없음) |

## 리뷰 반영 이력
- (개정 초안) 마일스톤 1-2는 `2026-07-21-tui-transcript-improvement.md`(별도 계획, 완료 처리됨)와 선행 커밋(`6d2ebd7`, `b018cea`, `f08ce29`, `9f6c42c`)에서 이미 구현되어 이번 계획은 재구현하지 않고 검증만 유지한다.
- **1차 Gate 2 리뷰 (2026-07-21):** `plan-reviewer` FAIL, `principle-auditor` REVISE, `usability-reviewer` FAIL. 증거: `.agents/traces/reviews/2026-07-21-tui-ux-improvement/{plan-reviewer,principle-auditor,usability-reviewer}.md`(1차본).
  - plan-reviewer 지적: (1) 마일스톤 3에 시크릿 유출 검증 `Run/Expected` 부재 → 추가함. (2) `docs/cli-reference.md`가 Durable Result Surface에는 있으나 마일스톤 4에 연결되지 않음 → 마일스톤 4 owner surface/검증에 추가함. (3, non-blocking) Tech Stack의 Textual 버전이 실제 설치본과 다름 → `8.2.8`로 수정함.
  - principle-auditor 지적: (1) `docs/cli-reference.md:68`의 "이벤트 타입은 4종으로 고정" 계약이 마일스톤 3의 변경과 충돌하는데 계획이 해소 방법을 명시하지 않음 → 계약을 확장하는 쪽으로 명시적으로 결정하고 `agentos/commands/run.py`/`docs/cli-reference.md`를 Durable Result Surface와 마일스톤 3 owner surface/검증에 추가함. (2) 중복된 활성 계획 `active/2026-07-20-tui-pi-ux-improvement.md`가 방치됨 → Phase 1/2는 완료된 작업과 중복, Phase 3(오토컴플리트 오버레이/IME 동기화)은 범위 밖으로 명시하고 `archive/`로 이동함(아카이브 사유는 해당 파일의 `## 아카이브 결정` 참조). (3, non-blocking) 마일스톤 3의 수동 확인 문구가 주관적 → `AGENTOS_TUI_TEST_PLAIN=1` 기반의 grep 가능한 검증으로 대체함.
  - usability-reviewer 지적: (1) `docs/cli-reference.md` durable-surface 주장이 마일스톤과 연결되지 않음 → 위와 동일하게 해결. (2) `/tools`/`/usage`의 정확한 출력 문구와 빈 상태 처리가 없음 → 정확한 문구를 아키텍처/마일스톤 4에 고정함. (3) `reasoning`/`tool_call`/`tool_result`의 사용자 표시 문구가 고정되지 않아 원문 타입 식별자가 노출될 위험 → 아키텍처 섹션에 `Thinking:`/`Tool call:`/`Tool result:` 고정 문구를 명시하고 `render_event`가 raw fallback으로 빠지지 않게 명시적으로 분기하도록 함.
- **2차 Gate 2 리뷰 (2026-07-21):** `principle-auditor` PASS(APPROVE), `usability-reviewer` PASS. `plan-reviewer`는 새 항목 1건으로 FAIL: 실제로 `uv run pytest tests/test_tui_cli.py -q`를 실행해 `10 failed, 12 passed`를 재현함 — 커밋 `9f6c42c`가 `Transcript.render()`를 삭제하며 (a) 기존 테스트들의 `.render()` 기반 단언이 깨졌고 (b) `_format_message()`가 더 이상 호출되지 않아 사용자 메시지의 `You: ` 접두어가 화면에서도 실제로 사라진 회귀임을 확인함. 증거: `.agents/traces/reviews/2026-07-21-tui-ux-improvement/{plan-reviewer,principle-auditor,usability-reviewer}.md`(2차본, `plan-reviewer.md`는 3차본으로 갱신되며 히스토리 보존됨). usability-reviewer는 non-blocking 제안 2건도 남김(`/usage` 요약 문구를 실제 출력과 맞추기, `/tools`와 실시간 transcript의 말줄임 규칙 통일) → 둘 다 본문에 반영함.
  - 대응: "마일스톤 0. 기존 회귀 테스트 수정"을 마일스톤 1 앞에 신설. `Transcript.add_message`가 사용자 메시지에 `_format_message()`(→ `You: ` 접두어)를 다시 적용하도록 프로덕션 코드를 고치고, `tests/test_tui_cli.py`는 `Transcript.render()` 대신 마운트된 `ChatMessage.text`를 읽는 헬퍼로 단언을 교체한다. 마일스톤 1/2는 "완료됨" 독립 주장을 제거하고 "마일스톤 0 완료 후 확인"으로 수정.
- **3차 Gate 2 리뷰 (2026-07-21):** `plan-reviewer` PASS — 재실행한 `uv run pytest tests/test_tui_cli.py -q`로 실패 재현을 독립 확인하고, 신설된 마일스톤 0의 owner surface(`agentos/terminal/tui/widgets.py`, `tests/test_tui_cli.py`)가 근본 원인 위치와 정확히 일치하며 구현 시 10건 실패가 모두 해소될 것이라고 코드 수준에서 확인함. Non-blocking 참고 3건(진행 상태 필드 최신화, 마일스톤 0 문구의 어감 상충 가능성, principle-auditor/usability-reviewer 증거가 마일스톤 0 추가 이전 시점이라는 점) 중 앞의 두 건은 본문에 반영함. 세 번째는 plan-reviewer 스스로 "마일스톤 0은 순수 버그 수정이라 principle/usability 심사 영역과 실질적으로 겹치지 않아 기존 PASS를 무효화하지 않는다"고 평가했고, 이 판단을 그대로 채택해 principle-auditor/usability-reviewer 재실행 없이 진행한다. 최종 증거: `.agents/traces/reviews/2026-07-21-tui-ux-improvement/{plan-reviewer(3차본, 1·2차 판정 이력 보존),principle-auditor(2차본, PASS),usability-reviewer(2차본, PASS)}.md`.
- **Gate 2 최종 결과: 3개 리뷰어 모두 PASS.** `reviewed: true`로 전환.

## 구현 결과
- **마일스톤 0 (회귀 수정):** `Transcript.add_message`가 사용자 메시지에 `_format_message()`(→ `You: ` 접두어)를 다시 적용하도록 복원. `tests/test_tui_cli.py`는 존재하지 않는 `Transcript.render()` 대신 마운트된 `ChatMessage.text`를 읽는 `_transcript_text()` 헬퍼로 전체 단언을 교체. `uv run pytest tests/test_tui_cli.py -q`가 `10 failed, 12 passed`에서 전체 PASS로 복구됨.
- **마일스톤 3 (LLM 동작 과정 표시):** `agentos/llm/types.py`의 `EventType`에 `reasoning`/`tool_call`/`tool_result` 추가. `MockProvider.stream_once`가 `reasoning → tool_call → tool_result → message_delta → done` 순서로 데모 이벤트를 방출. `CodexCliProvider`는 새 `_iter_items`/`_classify_item`으로 codex `exec --json`의 `reasoning`, `function_call`/`local_shell_call`(및 대응 `*_output`) item을 인식해 더 이상 버리지 않고 같은 세 타입으로 변환. `render_event`가 `Thinking: ...`/`Tool call: name(args)`/`Tool result: ...` 고정 문구로만 렌더링(120자 말줄임, `sanitize()` 유지). `AgentOSTui.run_stream`은 이 세 이벤트를 assistant 답변과 분리된 `role="process"` transcript 메시지로 추가하고, assistant 말풍선은 첫 `message_delta` 도착 시점에 지연 생성해 항상 process 메시지들 다음에(최종 답변 위치에) 오도록 순서를 보장. `agentos/commands/run.py`의 `--json` 출력과 `docs/cli-reference.md`도 확장된 이벤트 집합을 그대로 노출하도록 갱신.
- **마일스톤 4 (풍부한 슬래시 커맨드):** `/tools`(마지막 턴 도구 호출 목록, 빈 상태 안내 포함), `/usage`(마지막 턴 입력/출력 문자 수, 빈 상태 안내 포함) 슬래시 커맨드 추가. `renderers.format_tool_summary`를 공유해 `/tools`와 실시간 transcript의 말줄임 규칙을 통일. `/help` 팔레트와 `docs/cli-reference.md`에 반영.
- **마일스톤 5 (전체 안정성 검증):** `uv run pytest tests/ -q` 83 passed(신규 코드 경로 커버 테스트 8건 포함: TUI 프로세스 이벤트 순서, TUI/렌더러 시크릿 리댁션, `/tools`·`/usage` 빈 상태/채워진 상태, codex reasoning/tool_call 파싱, codex 시크릿 리댁션).

## 사용 방법
- `uv run agentos --provider mock` (또는 `codex`)로 TUI를 실행하고 아무 메시지나 보내면, 답변 앞에 `Thinking:`/`Tool call:`/`Tool result:` 줄이 구분된 스타일로 먼저 나타난 뒤 최종 답변이 markdown으로 렌더링된다.
- `/tools`를 입력하면 마지막 턴에서 호출된 도구 목록을(없으면 안내 문구를) 확인할 수 있다.
- `/usage`를 입력하면 마지막 턴의 입력/출력 문자 수를(아직 턴이 없으면 안내 문구를) 확인할 수 있다.
- `/help` 또는 `/`로 전체 명령 목록을 확인할 수 있다.
- `agentos run --once "..." --json` 소비자는 `reasoning`/`tool_call`/`tool_result` 타입을 그대로 받거나, 필요 없으면 무시하면 된다(문서: `docs/cli-reference.md`의 JSONL 절).

## 완료 증거
- `Run:` `uv run pytest tests/ -q` / `결과:` 83 passed
- `Run:` `AGENTOS_TEST_SECRET=AGENTOS_SENTINEL_SECRET uv run pytest tests/ -k redact -q` / `결과:` 6 passed
- `Run:` `uv run agentos run --once "hi" --provider mock --json | grep -o '"type": *"[a-z_]*"' | sort -u` / `결과:` `done`, `message_delta`, `reasoning`, `start`, `tool_call`, `tool_result` 모두 확인
- `Run:` (plain transcript 경유) `Thinking:`/`Tool call:`/`Tool result:` 줄이 raw 식별자 없이 최종 답변 앞에 순서대로 출력됨을 직접 실행으로 확인
- `Run:` `grep -n "/tools\|/usage" docs/cli-reference.md` / `결과:` 두 명령 모두 발견
- Gate 2 증거: `.agents/traces/reviews/2026-07-21-tui-ux-improvement/{plan-reviewer,principle-auditor,usability-reviewer}.md`

## 아카이브 결정
- 구현·검증·Gate 2 리뷰가 모두 완료되었으나, 사용자의 명시적 archive 요청 전까지는 `.agentos/project/exec-plans/active/`에 유지한다(자동 archive 금지 원칙). 사용자 요청 시 `.agentos/project/exec-plans/archive/`로 이동하고 `06-decisions-change-log.md`에 기록한다.
