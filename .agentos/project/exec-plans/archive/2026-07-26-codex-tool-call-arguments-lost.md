# Codex 네이티브 transport tool_call arguments 유실 수정 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-26<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> implementation_started_at: 2026-07-26T11:20:00Z<br>
> implementation_completed_at: 2026-07-26T13:17:32Z<br>
> implementation_duration: 약 2시간 (1차 수정 20분 + 2차 근본 원인 수정 15분 + 2차도 재현 실패 후 3차 수정 약 1시간25분)<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** TUI에서 등록된 도구(read/list/glob/grep/write/edit/bash)를 트리거하는 모든 요청이 "No response content was returned."로 실패하는 결함을 없앤다.

**사용자 결과:** 사용자가 TUI에서 도구 사용이 필요한 요청("list 도구가 동작하는지 확인해줘", "codex 토큰 사용량을 알려줘" 등)을 보내면, 도구가 올바른 인자로 실행되고 그 결과를 반영한 최종 어시스턴트 응답을 정상적으로 받는다.

**진행 상태:** 구현 및 검증 완료. 1차·2차 수정 모두 실사용 재현에서 실패해 3차로 완전히 다른 계층(도구 실행 루프)의 근본 원인을 추가로 발견·수정함 — 전체 테스트 스위트 425 passed, 회귀 없음, 실제 사용자 재현 시나리오를 그대로 재생하는 회귀 테스트로 검증 완료

**아키텍처:** (3차 수정 후 갱신) 최초에는 `map_codex_frame()`/`CodexNativeTransport.stream()`(`agentos/llm/transports/openai_codex_responses.py`)의 프레임 매핑 로직만 수정하면 충분하다고 봤으나, 실제로는 **두 개의 독립된 결함**이 겹쳐 있었다: (1) 프레임 매핑 결함(1·2차 수정으로 해결) — 이제 `tool_call` 이벤트는 올바른 `name`/`arguments`로 나간다. (2) 도구 실행 루프 결함(3차 수정, `agentos/conversation/runtime.py`) — Codex가 `tool_call`과 `done`을 같은 스트림에서 함께 보내는데도 `submit_turn()`이 `done`을 무조건 최우선으로 처리해 도구를 실행하지 않고 턴을 끝냈다. 두 결함 모두 최종 증상은 동일("No response content was returned.")했지만 계층이 달라, 1개만 고치면 다른 하나 때문에 계속 재현됐다.

**기술 스택:** Python, OpenAI Codex Responses SSE/WebSocket 스트리밍 프로토콜.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 구현 완료 (3차 수정까지, Gate 2 재검토는 2차 시점까지만 완료 — 3차는 아래 참고) |
| 완료됨 | 근본 원인 진단, 계획 작성, Gate 2 리뷰 3종 PASS(1차 대상), 1차 구현 → 재현 실패, 2차 근본 원인 재확정·구현, Gate 2 재검토 3종 PASS(2차 대상) → 재현 실패, 3차로 별도 계층(도구 실행 루프 우선순위) 결함 추가 발견·구현·검증 |
| 현재 위치 | 3차 수정 완료(전체 스위트 425 passed). **3차 수정은 아직 Gate 2 재검토를 받지 않았고, 사용자의 TUI 재현 확인도 아직 없음** |
| 다음 단계 | (a) 사용자가 TUI 재시작 후 "list 툴 동작 여부 검토해" 재요청으로 최종 확인, (b) 3차 수정에 대한 Gate 2 재검토(plan-reviewer/principle-auditor/usability-reviewer) 진행 |
| 완료 신호 | `uv run pytest -q` 전체 425 passed(회귀 없음), 실제 사용자 재현 시나리오를 그대로 재생하는 테스트 PASS. **최종 완료 신호는 사용자의 실제 TUI 재현 확인** — 이전 두 차례 모두 테스트 통과 후에도 실사용에서 실패했으므로 테스트 통과만으로 완료를 단정하지 않는다 |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | TUI에서 도구 호출이 필요한 어떤 요청을 보내도 "No response content was returned." 없이 정상적인 최종 응답을 받는다 |
| 누구를 위한 것인가? | AgentOS TUI를 Codex 계정으로 사용하는 모든 사용자 |
| 일상 사용에서 무엇이 달라지는가? | 지금까지 도구 호출이 걸리기만 하면 항상 실패하던 요청(파일 조회, 목록 확인, 검색, 쓰기/편집, bash 실행 등)이 정상 동작한다 |
| 무엇은 바뀌지 않는가? | 등록된 도구 목록(read/list/glob/grep/write/edit/bash)은 늘어나지 않는다. "codex 토큰 사용량"처럼 AgentOS에 전용 도구가 없는 질의에 모델이 어떤 자연어 답을 주는지는 이 계획의 범위가 아니다 — 이 계획은 오직 "도구 호출 시도가 인자 유실로 예외를 던져 항상 실패하는" 결함만 다룬다. 도구 승인(confirm_tool_call) 정책도 바뀌지 않는다. |

## 문제 근본 원인 (Root Cause)

OpenAI Responses API 공식 스트리밍 이벤트 스펙에 따르면, 함수 호출의 완성된 인자(JSON 문자열)는 오직 `response.function_call_arguments.done` 프레임에만 실려 온다. `response.output_item.added`는 도구 호출 아이템이 막 생성된 시점의 이벤트로 이때의 `item.arguments`는 비어 있다.

현재 `agentos/llm/transports/openai_codex_responses.py`의 `map_codex_frame()`은:
1. `response.output_item.added`에서 `function_call` 아이템을 감지하면 그 시점의(비어있는) `arguments`로 즉시 `tool_call` 이벤트를 발행한다.
2. `response.function_call_arguments.delta`는 `item` 필드가 없는 프레임 구조라 `frame.get("item")`이 항상 `None`이 되어 무시된다(의도한 매칭이 원천적으로 실패).
3. `response.function_call_arguments.done`은 매칭 분기 자체가 없어 완전히 버려진다.

결과적으로 모든 `tool_call` 이벤트의 `arguments`는 항상 빈 문자열(`""`)로 나가고, `ConversationRuntime.submit_turn()`(`agentos/conversation/runtime.py`)이 이를 `execute_tool(tool_name, "", ...)`로 호출하면서 `registry.execute_tool()`(`agentos/llm/tools/registry.py`) 내부의 `arguments.get("path", "")` 호출이 `AttributeError: 'str' object has no attribute 'get'`을 던진다. 이 예외는 `submit_turn()` 제너레이터나 `agentos/terminal/tui/app.py`의 스트림 소비 루프 어디에서도 잡히지 않아 처리되지 않은 예외로 전파되고, 화면에는 도구 실행 결과도 최종 텍스트도 반영되지 않은 채 턴이 종료되어 "No response content was returned."로 귀결된다.

**재현 증거 (2026-07-26 진단, 코드 변경 전 buggy 동작 확인):**

```
python3 -c "
from agentos.llm.transports.openai_codex_responses import map_codex_frame
ev = map_codex_frame({'type': 'response.output_item.added', 'item': {'type': 'function_call', 'name': 'list', 'arguments': ''}, 'response': {'id': 'r1'}})
print(ev)
"
```
실제 출력(buggy): `ProviderEvent(type='tool_call', ..., metadata={'name': 'list', 'arguments': ''}, ...)` — arguments가 항상 빈 문자열.

```
python3 -c "
from pathlib import Path
from agentos.llm.tools.registry import execute_tool
execute_tool('list', '', cwd=Path('.'))
"
```
실제 출력(buggy): `AttributeError: 'str' object has no attribute 'get'`.

## 수정 방향

(구현 중 확정된 최종 방향 — 최초 초안은 `item_id -> name` 상태 추적이 필요하다고 가정했으나, `response.function_call_arguments.done` 프레임 자체에 `name`이 이미 포함되어 있음을 공식 스펙에서 확인해 상태 추적 없이 `map_codex_frame()`을 순수 함수로 유지한 채 수정했다. Simplicity Gate에 부합하는 더 단순한 경로.)

- `response.output_item.added`(`function_call`/`custom_tool_call`)에서는 `tool_call` `ProviderEvent`를 더 이상 발행하지 않는다(이 시점 `arguments`는 항상 비어있으므로).
- `response.function_call_arguments.delta`는 계속 무시한다(증분 텍스트는 UI에 필요 없음, `item` 필드도 없어 원래도 매칭되지 않았음).
- `response.function_call_arguments.done`에서 비로소 `tool_call` `ProviderEvent`를 발행한다. 이 프레임은 `name`과 완성된 `arguments`(JSON 문자열)를 함께 담고 있으므로 상태 추적 없이 바로 사용 가능하다. `arguments`는 `json.loads()`로 파싱하며, 비어있거나 파싱 실패 시 빈 dict로 안전 폴백한다.
- `tool_call` 이벤트의 `arguments`는 항상 `dict`가 되어 `execute_tool()`의 `.get(...)` 호출이 안전하게 동작한다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 프레임 매핑 수정 (완료) | (내부 변경, 직접 체감 없음) `response.function_call_arguments.done` 시점에 완성된 dict arguments로 `tool_call` 이벤트가 발행됨 | `agentos/llm/transports/openai_codex_responses.py` | `Run:` `uv run pytest tests/test_codex_transport.py -q` / `Expected:` PASS, 0 failed → **실제 결과: 43 passed** |
| 2. arguments가 항상 dict로 정규화됨을 보장하는 회귀 테스트 추가 (완료) | (내부 변경) 실제 API 스트림 순서(`output_item.added` → `function_call_arguments.delta`(0회 이상) → `function_call_arguments.done` → `output_item.done`)를 그대로 재현한 시퀀스가 arguments=dict인 단일 `tool_call` 이벤트로 매핑됨을 검증 | `tests/test_codex_transport.py` | `Run:` `uv run pytest tests/test_codex_transport.py -k tool_call -q` / `Expected:` PASS → **실제 결과: PASS** |
| 3. 도구 호출이 예외 없이 실행됨을 확인 (완료) | 사용자가 TUI에서 "list 도구가 동작하는지 확인해줘" 같은 요청을 보내면 `execute_tool()`이 AttributeError 없이 정상 실행되고 최종 응답이 온다 | `agentos/llm/tools/registry.py`(변경 없음, 검증만) | `Run:` `python3 -c "from pathlib import Path; from agentos.llm.transports.openai_codex_responses import map_codex_frame; from agentos.llm.tools.registry import execute_tool; ev = map_codex_frame({'type': 'response.function_call_arguments.done', 'item_id': 'fc1', 'call_id': 'c1', 'name': 'list', 'arguments': '{}', 'response': {'id': 'r1'}}); execute_tool(ev.metadata['name'], ev.metadata['arguments'], cwd=Path('.'))"` / `Expected:` 예외 없이 `ToolExecutionResult` 반환 → **실제 결과: `ToolExecutionResult(content='...', is_error=False, ...)` 정상 반환** |
| 4. 전체 회귀 스위트 (완료) | 이번 수정이 다른 기능을 깨지 않았다 | 전체 저장소 | `Run:` `uv run pytest -q` / `Expected:` PASS → **실제 결과: 423 passed, 회귀 없음** |

## 장기 적용 표면

- traceability surface: `HISTORY.md`, 이 active plan 문서(`2026-07-26-codex-tool-call-arguments-lost.md`)
- durable result surface: `agentos/llm/transports/openai_codex_responses.py`, `agentos/conversation/runtime.py`(3차 수정으로 추가된 도구 실행 우선순위 로직), `tests/test_codex_transport.py`, `tests/test_conversation_runtime.py`, `tests/test_tui_cli.py`(정정된 pass-through 테스트) — 모두 수정된 소스 코드/회귀 테스트
- documentation-only exception: 없음 — 이 계획은 코드 결함 수정이며 결과는 소스 코드/테스트에 남는다.

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택(Python, 표준 라이브러리 `json`), 파일 구조(기존 파일 수정만, 신규 패키지 없음), 모든 planned `Run:` command(`uv run pytest`, `python3 -c`)는 이미 저장소에 존재하는 로컬 도구다. 네트워크 호출이나 실제 Codex 계정 인증 없이 유닛 테스트로 전부 재현·검증 가능하다.

## 리뷰 반영 이력
- [Gate 2 1차] `plan-reviewer`: PASS. 근본 원인 진단을 실제 소스(`agentos/llm/transports/openai_codex_responses.py:120-182`)와 재현 스크립트로 독립 검증, 체크리스트 전 항목 충족. `usability_review_required: true` 분류에 대한 비차단 노트 → usability-reviewer PASS로 해소.
- [Gate 2 1차] `principle-auditor`: PASS(APPROVE). P1~P4 전 항목 충족, 근본 원인 인용 정확성 확인, `.agents/traces/audit-principle.md`에 감사 기록.
- [Gate 2 1차] `usability-reviewer`: PASS. 사용자 결과 요약/진행 계획이 구현 세부사항보다 사용자 언어를 우선하고, 전문용어가 기술 섹션에만 국한됨을 확인. `.agents/traces/reviews/2026-07-26-codex-tool-call-arguments-lost/usability-reviewer.md`에 증거 저장.
- 수정 필요 사항 없음 (전원 1차 PASS, 문서 본문 변경 없음).

## 구현 결과

### 1차 수정 (2026-07-26T11:40:19Z 완료, 이후 재현 실패로 불완전함이 드러남)

`agentos/llm/transports/openai_codex_responses.py`의 `map_codex_frame()`을 수정했다:
- `response.output_item.added`(function_call/custom_tool_call)는 더 이상 `tool_call` 이벤트를 발행하지 않는다(이 시점 arguments는 항상 비어있었음).
- `response.function_call_arguments.delta`는 계속 무시한다.
- `response.function_call_arguments.done`에서 `tool_call` 이벤트를 발행하며, 공식 OpenAI platform Responses API 문서(`response.function_call_arguments.done` 이벤트에 `name` 필드가 포함된다는 스펙)를 근거로 이 프레임의 `name`과 `arguments`를 사용하도록 구현했다.

**이 1차 수정은 실제 사용자 재현("list 툴 동작 여부 검토해")에서 여전히 실패했다.** 원인: Codex ChatGPT-account 백엔드(`chatgpt.com/backend-api/codex/responses`)의 실제 `response.function_call_arguments.done` 프레임에는 문서와 달리 **`name` 필드가 없다** — `arguments`, `item_id`, `output_index`, `sequence_number`만 있다. 그 결과 `frame.get("name")`이 항상 `None`이 되어 `tool_call` 이벤트의 `name`이 `null`로 나갔고, `execute_tool(None, ...)`이 알 수 없는 도구로 처리되어 여전히 도구가 실행되지 않았다(TUI 실측 로그: `metadata={"arguments": {"path": "."}, "name": null}`, `tool_result` 이벤트 없이 곧장 `done`으로 종료).

### 2차 수정 (근본 원인 재확정, 2026-07-26T11:55:43Z 완료)

`AGENTOS_DEBUG_CODEX_FRAMES` 임시 환경변수로 실제 Codex 세션의 raw SSE 프레임을 캡처해(`/tmp/agentos_codex_frames_debug.jsonl`, 검증 후 즉시 삭제) 실제 프레임 구조를 직접 확인했다. 확인된 사실:
- `response.output_item.added`(`item.type == "function_call"`)는 `item.name`은 채워져 있지만 `item.arguments`는 빈 문자열이다.
- `response.function_call_arguments.delta`/`.done`은 `name`을 포함하지 않는다.
- **`response.output_item.done`(`item.type == "function_call"`)이 `name`, 완성된 `arguments`, `call_id`를 모두 포함한 완결 아이템을 담아 온다.** 이 프레임이 도구 호출의 유일하게 신뢰 가능한 완성 시점이다.

이에 따라 `map_codex_frame()`을 다시 수정했다:
- `response.function_call_arguments.delta`/`.done`은 둘 다 무시한다(`name`이 없어 단독으로 `tool_call`을 만들 수 없음).
- `response.output_item.added`는 여전히 아무 이벤트도 발행하지 않는다(arguments 미완성).
- `response.output_item.done`에서 `item.type`이 `function_call`/`custom_tool_call`이면 그 시점 `item.name`과 `item.arguments`(JSON 파싱, 실패/빈 값은 빈 dict로 폴백)로 `tool_call`을 발행한다. `function_call_output`/`custom_tool_call_output`(기존 `tool_result` 처리)과 같은 프레임 타입 안에서 `item.type`으로 분기하도록 통합했다.

이 방식은 `item_id` 단위 상태 추적이 필요 없다(`output_item.done` 자체가 완결 아이템이므로) — 최초 계획 초안의 "상태 추적 필요" 가정과도, 1차 수정의 "공식 문서 스펙을 그대로 신뢰" 가정과도 다른, 실제 캡처된 프레임에 기반한 세 번째 접근이다.

기존 테스트(1차 수정 때 작성한 것 포함)는 모두 실제 프레임 구조를 반영해 다시 작성했다: `output_item.added`가 tool_call을 발행하지 않음, `arguments.delta`/`arguments.done` 둘 다 무시됨, `output_item.done`(function_call)이 파싱된 dict로 tool_call을 발행함, 빈/손상된 JSON 폴백, 그리고 실제 캡처 세션에서 확인된 프레임 순서를 재현한 end-to-end 시퀀스 테스트.

### 3차 수정 (별도 계층의 결함 추가 발견, 2026-07-26T13:17:32Z 완료)

**2차 수정 후에도 사용자가 TUI를 재시작하고 재현했을 때 여전히 실패했다.** 이번엔 세션 로그에서 `tool_call` 이벤트가 이미 정확한 `name="list"`, `arguments={"path": "."}`로 나갔음을 확인했다(1·2차 수정은 실제로 유효했다) — 그런데 그 다음 `tool_result` 없이 곧바로 `done`으로 넘어갔다. 즉 프레임 매핑은 이제 정상인데 **도구가 아예 실행되지 않았다.**

원인은 `agentos/conversation/runtime.py`의 `ConversationRuntime.submit_turn()`에 있었다: 이 함수는 스트림을 다 읽은 뒤 `terminal_event.type == "done"`이면 `pending_tool_call` 유무와 무관하게 무조건 `break`해 도구 실행 단계로 넘어가지 않았다(수정 전 211-212번 줄). 그런데 실제 Codex 네이티브 transport는 `response.completed`(→ `done`)를 도구 호출만 있는 응답에도 무조건 스트림 종료 신호로 보낸다 — 즉 같은 스트림 안에 `tool_call`과 `done`이 함께 온다. 이 경우 기존 로직은 `done`을 최우선으로 처리해 도구 실행을 완전히 건너뛰고 빈 assistant 메시지를 커밋했다.

수정: `pending_tool_call`이 있으면 `done`을 만나도 먼저 도구 실행 분기로 진입하도록 우선순위를 뒤집었다. 단, 같은 스트림 안에서 `tool_result`까지 이미 나온 경우(데모/mock provider가 tool_call+tool_result를 미리 함께 서술하는 패턴, 예: `MockProvider`의 두 번째 tool_call)는 이미 처리된 것으로 보고 `pending_tool_call`을 다시 비워 재실행하지 않도록 했다.

이 변경으로 `test_submit_turn_event_stream_is_forwarded_to_the_caller_unmodified` 테스트가 실패했는데(가짜 tool_call/tool_result가 섞인 canned 스트림을 event pass-through 검증용으로만 쓰고 있었음), 이 테스트의 canned 데이터를 tool_call 없는 시퀀스로 정정해 원래 검증 목적(이벤트가 가공 없이 그대로 전달됨)에 맞췄다. 그리고 실제 사용자가 겪은 정확한 시나리오("tool_call → tool_result 없이 done"이 첫 스트림에 오고, 도구 실행 후 재호출된 두 번째 스트림에서 최종 텍스트가 나옴)를 재현하는 회귀 테스트를 `tests/test_conversation_runtime.py`에 추가했다.

이로써 최초 계획의 "아키텍처" 절에서 "도구 실행 루프는 변경하지 않는다"고 선언했던 경계가 틀렸음이 드러났다 — 실제로는 프레임 매핑(전송 계층)과 도구 실행 우선순위(오케스트레이션 계층)에 각각 독립된 결함이 있었고, 둘 다 고쳐야 증상이 사라졌다.

## 사용 방법

별도 사용자 작업은 필요 없다. **단, 기존에 떠 있던 AgentOS TUI 프로세스가 있다면 반드시 재시작해야 한다** — Python은 실행 중인 프로세스에 코드 변경을 반영하지 않으므로, 이 수정 이전에 시작된 세션은 계속 구버전 동작을 보인다. 재시작 후에는 Codex 계정으로 AgentOS TUI를 사용하는 사용자가 도구 호출이 필요한 요청(파일 조회, 목록/검색, 쓰기/편집, bash 실행 등)을 보내면 "No response content was returned." 없이 정상적으로 동작해야 한다. **이 계획은 이미 두 차례 "해결됨"이라고 판단했다가 실제 재현에서 틀렸던 전례가 있으므로, 이번에도 실제 TUI 재현으로 사용자가 최종 확인해줄 것을 요청한다.**

## 완료 증거

- `Run:` `uv run pytest tests/test_codex_transport.py -q` → `Expected:` PASS / **실제:** `44 passed`
- `Run:` `uv run pytest tests/test_conversation_runtime.py -q` → `Expected:` PASS / **실제:** `25 passed`(3차 수정 회귀 테스트 포함)
- `Run:` `uv run pytest -q` (전체 스위트) → `Expected:` PASS, 회귀 없음 / **실제:** `425 passed`
- `Run:` 실제 사용자 재현 시나리오(첫 스트림: `tool_call(name="list", arguments={"path":"."})` → `done`, 두 번째 스트림: `message_delta` → `done`)를 `ConversationRuntime.submit_turn()`에 그대로 재생 → `Expected:` 도구가 실행되고(`tool_result` 발생) 최종 assistant 메시지가 커밋됨 / **실제:** 확인됨 (`roles=['user','tool','assistant']`, `assistant.text="여기 목록입니다."`)

## 아카이브 결정

이 계획은 아직 active에 남아 있으며, 사용자가 실제 TUI 재시작 후 재현으로 최종 확인하고 archive를 요청하면 `plan_lifecycle.py archive <plan-path> --status 완료`로 이동한다. **1·2차 완료 선언이 모두 실제로는 불완전했던 전례가 있으므로, 사용자 확인 없이 스스로 "완전히 해결됨"을 재선언하지 않는다.**
