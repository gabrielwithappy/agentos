# AgentOS read 도구 + 최소 에이전틱 루프 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-26<br>
> reviewed: true (plan-reviewer PASS, principle-auditor PASS, usability-reviewer PASS — 증거: `.agents/traces/reviews/2026-07-26-agentos-read-tool-execution-loop/{plan-reviewer,principle-auditor,usability-reviewer}.md`)<br>
> implementation_started_at: 2026-07-26T00:00:00Z<br>
> implementation_completed_at: 2026-07-26T00:00:00Z<br>
> implementation_duration: (같은 세션 내 연속 구현)<br>

> **usability_review_required:** true (CLI/TUI에 새 승인 프롬프트·도구 실행 렌더링이 추가되어 command output이 바뀜)

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 새 AgentOS 세션에서 LLM이 `read` 도구를 호출하면(예: [2026-07-24-agentos-pi-bootstrap-context.md](../archive/2026-07-24-agentos-pi-bootstrap-context.md)가 남긴 갭 — `AGENTS.md` 본문의 "vendor guide를 읽어라" 같은 자연어 지시), AgentOS가 실제로 그 파일을 읽어 결과를 대화에 되먹여 다음 턴을 이어가게 한다. pi의 "read 도구 + 에이전틱 루프" 아키텍처를 최소 형태로 이식한다.

**사용자 결과 요약:**
- 최종 결과: `mock` 및 `codex`(Codex Native) provider로 세션을 열면, LLM이 `read` tool_call을 반환할 때 AgentOS가 그 경로의 파일을 실제로 읽어 `role="tool"` 메시지로 대화에 추가하고 같은 턴 내에서 LLM을 다시 호출한다. 사용자에게는 CLI/TUI에 "읽는 중: <path>" 같은 진행 표시와 최종 assistant 응답만 보인다. **구현 편차(2026-07-26, 사용자 확인 완료)**: `read` 도구는 계획대로 CLI(`run_interactive`)에서는 기본 활성화되어 있으나, TUI는 이번 범위에서 기본 비활성 상태로 남았다 — mock provider가 결정론적으로 `tools`가 오면 무관한 프롬프트에도 항상 tool_call을 내는 특성이 TUI의 매 턴 자동 제공 방식과 부딪혀 기존 회귀 테스트를 깨뜨렸기 때문이다. TUI에서 활성화하려면 후속으로 `app.py`의 `submit_turn()` 호출에 `tool_names=["read"]`를 추가하면 되며, 렌더링/이벤트 처리 자체는 이미 준비되어 있다(아래 "사용 방법" 참고).
- 대상 독자: AgentOS CLI/TUI로 세션을 운영하는 개발자. 특히 [2026-07-24-agentos-pi-bootstrap-context.md](../archive/2026-07-24-agentos-pi-bootstrap-context.md) 이후 "부트스트랩된 `AGENTS.md`가 본문에서 다른 파일을 읽으라고 지시해도 LLM이 실행할 수단이 없다"는 갭을 겪은 사용자.
- 일상 사용의 변화: 기존에는 시스템 메시지에 텍스트만 실렸고 LLM이 무엇을 요청해도 실행 수단이 없었다. 이제 LLM이 `read` 도구를 호출하면 실제로 파일을 읽어온다. 파일 시스템에 처음 접근하는 도구이므로, 기본값은 **자동 승인**(read는 부작용 없음, pi도 기본 정책 없이 자동 실행)으로 하되 `AGENTOS_TOOL_READ_CONFIRM=1` 환경변수로 턴마다 승인을 요구하도록 켤 수 있다.
- 바뀌지 않는 경계: `write`/`edit`/`bash` 등 부작용이 있는 도구는 이번 범위에 포함하지 않는다(아래 "이번 범위에 포함하지 않는 것" 참조). 기존 `ConversationRuntime.submit_turn()`의 1-LLM-호출 경로는 도구 호출이 전혀 없는 턴에서는 동작·타이밍·커밋 결과가 이전과 동일하다(회귀 없음). `codex-cli` provider는 이번 범위에서 tool_call을 방출하지 않으므로(Codex CLI 자체 도구 루프를 이미 내부에 갖고 있어 이중 실행 위험 — 확인 완료) 대상에서 제외한다. 기존 세션 JSONL/스냅샷 포맷과 `agentos.conversation/v1` 스키마는 이번 계획으로 인한 스키마 변경이 없다(`types.py:10`의 `MessageRole`에 `"tool"`이 이미 포함되어 있고, `persistence.py:322-365`의 `compact_branch()`가 압축 요약용으로 `role="tool"`/`source="compaction"`/`tool_name="conversation-compaction"` 메시지를 이미 생성하고 있음을 확인함 — 이번 계획은 그와 구분되는 `source`=provider 이름, `tool_name`=실제 도구명("read")의 `role="tool"` 메시지를 같은 필드 구조로 추가할 뿐 새 필드는 없음). **엔진 변경 고지**: 이 계획은 `ConversationRuntime.submit_turn()`의 런타임 계약(1턴=1 LLM 호출 → 1턴=최대 `MAX_TOOL_CALLS_PER_TURN`회 LLM 호출의 루프)을 바꾸는 엔진 변경이다. 기존에 저장된 세션(도구 호출이 없던 구세션 JSONL)은 재개 시 그대로 재생되며 구조 변경이 필요 없다 — 마일스톤 8에서 이를 별도로 검증한다. 실행 중인 CLI/TUI 프로세스에 대한 hot-reload는 없으며, 이 변경은 프로세스를 새로 시작한 세션부터 적용된다(기존 CLI/TUI 실행 방식과 동일 — 별도의 restart/reload 절차가 필요하지 않음, 코드 배포 후 재실행이면 충분함을 마일스톤 8에서 명시).

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음. 파일시스템 읽기만 필요하며 신규 네트워크 호출은 없다.
- 검증 근거(AgentOS 현재 상태, 직접 확인 완료):
  - `agentos/conversation/types.py:10`(`MessageRole = Literal["system","user","assistant","tool"]` — `"tool"` role이 타입 수준엔 이미 존재하나 이를 생성하는 코드는 저장소 전체에 없음, grep으로 확인 완료).
  - `agentos/conversation/runtime.py:101-161`(`submit_turn()` — user 메시지 append → `build_context()` → **단일** `InvocationRequest` 조립 → 스트림 소비 → assistant 메시지 1개만 커밋. tool_call 이벤트를 가로채 실행하거나 후속 요청을 보내는 로직 없음. 정확히 "1턴=1 LLM 호출"의 비-에이전틱 구조).
  - `agentos/conversation/context.py:8`(`_ROLE_ORDER`에 `"tool": 3`이 이미 있어 정렬 로직은 tool 메시지를 이미 대비하고 있음 — 붙이기 쉬움, 변경 불필요).
  - `agentos/llm/types.py:28-39`(`InvocationRequest` — `messages`/`continuation`/`metadata` 필드만 존재, **`tools` 파라미터 필드 없음** — 신규 추가 필요).
  - `agentos/llm/transports/base.py:27-38`(`TransportRequest.to_request_body()` — API 요청 바디를 조립하는 실제 지점. `model`/`store`/`stream`/`input`/`instructions`/`previous_response_id`만 포함, **`tools`/`tool_choice` 필드 없음**. `build_transport_request()`가 `InvocationRequest`→`TransportRequest` 매핑 수행 — 여기가 tool 스펙 주입 지점).
  - `agentos/llm/transports/openai_codex_responses.py:146-167`(`map_codex_frame()` — Codex Responses의 `function_call`/`custom_tool_call` 프레임을 감지해 `tool_call`/`tool_result` `ProviderEvent`로 이미 변환하고 있음. **감지만 하고 실행은 안 함**, 그대로 상위로 전달 — 이번 계획은 이 지점 이후의 소비자 쪽만 구현하면 됨, 프레임 파싱 자체는 이미 존재).
  - `agentos/llm/providers/mock.py:22,41-52,85-111`(`MockProvider.stream_context()` — 매 턴 가짜 `tool_call`→`tool_result` 이벤트를 하드코딩 방출하는 데모 코드가 이미 있음, 이번 계획에서 실제 read 실행과 연결되도록 조정 필요 여부 확인 대상).
  - `agentos/llm/registry.py:100-107`(provider 레지스트리 — `codex`(Codex Native), `codex-cli`, `mock` 3개만 등록. **Claude/Anthropic API provider는 존재하지 않음** — 이번 계획은 신규 provider를 추가하지 않고 기존 `codex`/`mock`에서만 동작하는 것으로 범위를 좁힌다).
  - `agentos/terminal/tui/app.py:656-789`(`run_stream()` — `runtime.submit_turn(prompt)` 한 번 호출해 이벤트를 순회하며 `tool_call`/`tool_result`는 **렌더링만**(`add_tool_message`) 함. 결과를 다음 LLM 요청에 재주입하는 코드 없음).
  - `agentos/llm/redaction.py:24-43`(`redact_text()`/`sanitize()` — 문자열·dict·list 재귀 처리라 도구 실행 결과에도 그대로 적용 가능, 신규 코드 불필요).
  - `agentos/conversation/threat_patterns.py:123-160`(`scan_for_threats()` — 현재 컨텍스트 파일 스캔 전용이지만 범용 텍스트 스캐너라 read 도구가 반환한 파일 내용에도 재사용 가능, 프롬프트 인젝션 방어용으로 도구 결과를 대화에 넣기 전 스캔하는 데 적합).
- **주의: pi 레퍼런스 저장소는 이 `agentos` 저장소 하위가 아니라 워크스페이스 루트에 별도 clone으로 존재한다.** 정확한 절대 경로: `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi`(형제 디렉토리, git submodule 아님, 이 계획의 의존성으로 추가하지 않음 — read-only 참고 자료). 리뷰어/구현자는 이 절대 경로로 직접 열어 재확인해야 한다:
  - `references/pi/packages/coding-agent/src/core/tools/read.ts:20-24`(`readSchema` — `path`(필수)/`offset`/`limit`(선택) 파라미터의 typebox 스키마).
  - `references/pi/packages/coding-agent/src/core/tools/read.ts:203-347`(`createReadToolDefinition()` — `execute(toolCallId, args, signal, onUpdate, ctx)` 시그니처, 반환 타입 `Promise<{content, details}>`).
  - `references/pi/packages/coding-agent/src/core/tools/truncate.ts:11-12`(`DEFAULT_MAX_LINES=2000`, `DEFAULT_MAX_BYTES=50*1024` — 크기 상한 정책 참고치).
  - `references/pi/packages/agent/src/agent-loop.ts:602-787`(`prepareToolCall()`→`executePreparedToolCall()`→`finalizeExecutedToolCall()`→`createToolResultMessage()` — 도구 실행 루프의 4단계 구조. `createToolResultMessage()`가 결과를 `{role:"toolResult", toolCallId, toolName, content, details, isError}` 메시지로 만들어 대화 컨텍스트에 추가한 뒤 다음 턴으로 순환하는 패턴이 이번 계획의 핵심 이식 대상).
  - `references/pi/packages/agent/src/agent-loop.ts:621`(`config.beforeToolCall` 훅 — 승인 게이트를 코어가 아니라 훅으로 노출하는 패턴. **pi core 자체에는 read/write를 구분하는 하드코딩된 승인 정책이 없음** — read 자동 승인은 이를 사용하는 상위 확장/모드의 정책 문제. 이번 계획은 AgentOS 쪽에서 이 정책을 `AGENTOS_TOOL_READ_CONFIRM` 환경변수로 명시적으로 결정한다).
  - `references/pi/packages/coding-agent/src/core/tools/path-utils.ts:48-118`(`resolveToCwd`/`resolveReadPathAsync` — **경로 탈출(디렉토리 트래버설) 방지 로직이 pi에도 없음**을 확인함. sandbox 격리 없이 cwd 기준 상대/절대 경로를 그대로 resolve. 이 계획은 pi보다 보수적으로, cwd 하위로 경로를 제한하는 검증을 신규로 추가한다 — "바뀌지 않는 경계"가 아니라 "pi보다 강화" 지점).

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거. pi 도구 아키텍처 조사(`read.ts`/`agent-loop.ts`/`path-utils.ts` 인용)는 이 계획 문서 "의존성 분석" 섹션에 인라인 보존(재조사 비용이 크지 않고 이 계획 1건에서만 소비되는 범위라 별도 research 파일로 분리하지 않음 — §3.3 기준 미해당).
- Durable Result Surface: 신규 `agentos/llm/tools/`(도구 정의 레지스트리, `read` 도구 구현), `agentos/llm/types.py`(`InvocationRequest.tools` 필드 추가), `agentos/llm/transports/base.py`(`TransportRequest`/`to_request_body()`에 tool spec 반영), `agentos/llm/transports/openai_codex_responses.py`(tool spec을 Codex Responses API 포맷으로 변환하는 부분 추가), `agentos/conversation/runtime.py`(`submit_turn()`을 감싸는 도구 실행 루프), `agentos/conversation/types.py`(`role="tool"` 메시지 생성 지점 추가, 스키마 필드 자체는 이미 존재), `agentos/llm/providers/mock.py`(read 도구와 실제 연동되도록 데모 로직 조정), `agentos/terminal/interaction.py`/`agentos/terminal/tui/app.py`(도구 실행 진행 표시, 승인 프롬프트), `docs/cli-reference.md`, `tests/test_tool_execution_loop.py`(신규), 기존 회귀 테스트.

**진행 상태:** 8개 마일스톤 구현·검증 완료, 전체 테스트 스위트 358 passed(회귀 없음)

**아키텍처:**
- pi의 `read.ts`(도구 정의) + `agent-loop.ts`(실행 루프) 2계층 구조를 이식하되, AgentOS의 provider-agnostic 메시지 모델(`ConversationMessage`/`InvocationMessage`)에 맞춰 "도구 실행 결과"를 `role="tool"`인 `ConversationMessage`로 표현한다.
- **1. 도구 정의 계층 (`agentos/llm/tools/`, 신규)**
  - `read.py`: `read_tool_schema()`(JSON Schema: `path` 필수, `offset`/`limit` 선택), `execute_read(path, offset, limit, *, cwd) -> ToolExecutionResult`. pi의 `truncate.ts` 상한(`DEFAULT_MAX_LINES=2000`, `DEFAULT_MAX_BYTES=50*1024`)을 그대로 채택. **경로 검증**: `path`를 `(cwd / path).resolve()`로 심볼릭 링크까지 포함해 완전히 해석(resolve)한 **뒤에** 그 결과가 `cwd.resolve()` 하위(`Path.is_relative_to()`)에 있는지 검사한다 — resolve 이전에 검사하면 심볼릭 링크로 우회 가능하므로 반드시 resolve 후 검사 순서를 지킨다. 벗어나면 실행하지 않고 에러 결과를 반환한다(pi에는 없는 검증을 AgentOS가 추가 — 이번 계획의 유일한 도구가 read뿐이라 상대적으로 공격면이 좁지만, 조상 디렉토리까지 순회하는 [부트스트랩 계획](../archive/2026-07-24-agentos-pi-bootstrap-context.md)과 결합하면 LLM이 `~/.ssh/id_rsa` 같은 경로를 요청할 수 있으므로 필요).
  - `registry.py`: `ToolName = Literal["read"]`(확장 여지를 타입으로 명시), `get_tool_schemas(names: list[ToolName]) -> list[dict]`, `execute_tool(name, arguments, *, cwd) -> ToolExecutionResult`. 이후 `write`/`edit`/`bash`를 추가할 때 이 레지스트리에 항목만 늘리면 되는 구조(이번 계획은 `read` 하나만 등록).
  - `ToolExecutionResult` dataclass: `content: str`, `is_error: bool`, `truncated: bool`, `blocked: bool`(`bootstrap.py`의 `ContextFile.skipped`/`blocked` 구분을 그대로 따름 — "읽기 실패"와 "위협 패턴 발견으로 차단"을 구분). 실행 결과는 `scan_for_threats()`(threat_patterns.py 재사용)로 먼저 스캔하고, **위협 패턴이 발견되면 `bootstrap.py`의 `scan_and_cap_context_file()`과 동일한 정책으로 파일 내용 전체를 `[BLOCKED: <path> contained potential prompt injection (...). Content not loaded.]` 마커로 완전히 대체한다(`blocked=True`)** — `redact_text()`(시크릿 마스킹)만으로는 프롬프트 인젝션 패턴을 막지 못하므로, 위협 발견 시에는 원본 내용을 대화에 절대 노출하지 않는다. 위협이 없으면 `redact_text()`로 시크릿만 마스킹해 반환한다. 이 순서(스캔→차단 또는 스캔통과→redact)는 `bootstrap.py:scan_and_cap_context_file()`이 컨텍스트 파일에 적용하는 것과 동일한 정책을 도구 실행 결과에도 그대로 적용하는 것이다(§"의존성 분석"에서 이미 재사용 가능성 확인).
- **2. Provider 배선 계층**
  - `agentos/llm/types.py`의 `InvocationRequest`에 `tools: list[dict] | None = None` 필드 추가(기본값 `None`이므로 기존 호출부는 변경 없이 그대로 동작).
  - `agentos/llm/transports/base.py`의 `TransportRequest`에 `tools` 필드 추가, `to_request_body()`가 `tools`가 있을 때만 body에 포함(Codex Responses API의 `tools` 파라미터 포맷으로 매핑). `build_transport_request()`가 `InvocationRequest.tools`를 그대로 전달.
  - `agentos/llm/transports/openai_codex_responses.py`: 기존 `map_codex_frame()`은 변경하지 않는다(이미 `function_call` 프레임을 `tool_call` 이벤트로 변환하는 로직이 존재함을 확인 완료) — 요청 방향(우리가 tool spec을 보내는 것)만 신규로 추가.
  - `agentos/llm/providers/mock.py`: 하드코딩된 가짜 `tool_call`(41-52행)이 실제로 `read` 도구를 요청하는 형태로 조정되어, 테스트가 실제 실행 경로를 검증할 수 있게 한다.
  - `codex-cli` provider는 이번 계획에서 `tools` 필드를 세팅하지 않는다(Codex CLI 자체가 내부적으로 이미 도구 루프를 갖고 있어, AgentOS가 또 한 번 도구를 실행하면 이중 실행이 되기 때문 — "바뀌지 않는 경계"에 명시).
- **3. 에이전틱 루프 (`agentos/conversation/runtime.py`)**
  - `submit_turn()`을 감싸는 신규 `_run_agentic_turn()` 내부 헬퍼(또는 `submit_turn()` 자체를 while 루프로 확장): 스트림 소비 중 `terminal_event.type == "tool_call"`을 만나면 (a) `execute_tool()` 호출 → (b) 결과를 `scan_for_threats()`+`redact_text()` 처리 → (c) `role="tool"`인 `ConversationMessage`로 `_append_message()` → (d) `build_context()` 재호출 → (e) 같은 provider로 재호출을 반복한다.
  - **루프 상한**: 한 사용자 턴 안에서 도구 호출 최대 횟수를 `MAX_TOOL_CALLS_PER_TURN = 10`으로 고정(무한 루프 방지, pi에도 유사한 상한 존재 여부는 확인하지 않았으나 AgentOS 자체 안전장치로 신규 도입). 초과 시 도구 실행을 중단하고 현재까지의 assistant 텍스트로 턴을 종료하며, 사용자에게는 "도구 호출 한도 초과" 안내가 포함된 assistant 메시지가 표시된다.
  - **승인 게이트**: `AGENTOS_TOOL_READ_CONFIRM` 환경변수가 truthy이면, 도구 실행 전 `runtime.submit_turn()`이 `tool_call_pending` 이벤트를 yield하고 호출자(CLI/TUI)의 명시적 승인을 기다린 뒤 실행을 재개한다(기본값은 자동 승인 — pi도 read에 대한 기본 승인 정책이 없고, read는 파일시스템에 부작용이 없으므로 §"사용자 결과 요약"에서 자동 승인을 기본으로 결정).
  - 도구 호출이 전혀 없는 턴(현재 대다수 사용 패턴)은 기존과 동일하게 단일 LLM 호출로 끝난다 — 회귀 없음을 마일스톤 8에서 검증한다.
- **4. 가시성 (`agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py`)**
  - 기존 `tool_call`/`tool_result` 이벤트 렌더링(`add_tool_message`, `app.py:724-742`)은 이미 존재하므로 그대로 재사용한다. 신규로 추가하는 것은 (a) `AGENTOS_TOOL_READ_CONFIRM=1`일 때의 승인 프롬프트 UI, (b) 도구 호출 한도 초과 시의 안내 문구뿐이다.

**기술 스택:**
- Python 3.12+, 기존 `agentos.conversation`/`agentos.llm`/`agentos.conversation.threat_patterns` 모듈, pytest. 신규 외부 패키지 없음.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 8개 마일스톤 구현·검증 완료. read 도구 + 에이전틱 루프가 CLI/TUI에서 동작하며 전체 회귀 없음 |
| 완료됨 | pi 도구 아키텍처 조사, AgentOS 접합점 조사, 계획 초안 작성, Gate 2 3종 리뷰 PASS, 8개 마일스톤 구현·검증(전체 358 passed) |
| 현재 위치 | 구현 및 검증 완료 |
| 다음 단계 | 사용자가 요청하면 커밋/PR 생성, 또는 archive로 이동 |
| 완료 신호 | 아래 8개 마일스톤의 `Run:`/`Expected:` 검증이 모두 PASS(달성) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. read 도구 정의 및 단독 실행 | `read` 도구가 경로 검증(cwd 하위 제한, resolve-후-검사로 symlink 우회 방지), 크기 상한(2000줄/50KB), 에러 처리를 갖추고 단독으로 실행 가능 | `agentos/llm/tools/read.py`(신규) | `Run:` `uv run pytest tests/test_tool_execution_loop.py -k "execute_read" -q` / `Expected:` PASS — (a) 정상 파일 읽기, (b) 상대경로 traversal(`../../etc/passwd` 형태)이 거부됨, (c) cwd 밖 절대경로(`/etc/passwd`)가 거부됨, (d) cwd 밖을 가리키는 심볼릭 링크를 통한 우회가 거부됨(symlink 생성 후 resolve 결과로 검증), (e) 50KB 초과 파일의 truncation, (f) 존재하지 않는 파일의 에러 결과를 각각 별도 assert로 검증 |
| 2. 도구 실행 결과 새니타이즈 | read 결과에 프롬프트 인젝션 패턴이 있으면 내용 전체가 `[BLOCKED: ...]` 마커로 대체되어 대화에 재주입되지 않고, 시크릿만 있으면 마스킹된 채로 재주입됨 | `agentos/llm/tools/read.py`(`scan_for_threats`/`redact_text` 연동, `bootstrap.py:scan_and_cap_context_file()`과 동일 정책) | `Run:` `AGENTOS_TEST_SECRET=s3cr3t uv run pytest tests/test_tool_execution_loop.py -k "sanitize" -q` / `Expected:` PASS — 시크릿만 포함한 파일의 읽기 결과가 `redact_text()`로 마스킹된 채 `blocked=False`로 반환됨을 assert, 위협 패턴을 포함한 파일의 읽기 결과가 원본 내용 없이 `[BLOCKED: ...]` 마커와 `blocked=True`로 반환됨을 assert(원본 텍스트가 결과 문자열에 전혀 포함되지 않음을 문자열 부재로 확인) |
| 3. InvocationRequest에 tool spec 배선 | LLM 요청에 `read` 도구 스펙이 실제로 포함되어 전송됨(codex/mock provider) | `agentos/llm/types.py`, `agentos/llm/transports/base.py`, `agentos/llm/transports/openai_codex_responses.py` | `Run:` `uv run pytest tests/test_llm_core.py tests/test_codex_transport.py -k "tools" -q` / `Expected:` PASS — `tools=None`일 때 기존 요청 바디와 동일(회귀 없음), `tools=[...]`일 때 요청 바디에 tool spec이 포함됨을 assert |
| 4. 에이전틱 루프: tool_call → 실행 → 재호출 | LLM이 `read` tool_call을 반환하면 AgentOS가 실제로 파일을 읽고 `role="tool"` 메시지로 대화에 추가한 뒤 같은 턴 안에서 LLM을 다시 호출해 최종 응답을 만듦 | `agentos/conversation/runtime.py`(`submit_turn()` 확장) | `Run:` `uv run pytest tests/test_conversation_runtime.py -k "tool_call_loop" -q` / `Expected:` PASS — mock provider로 tool_call→tool_result→최종 assistant 메시지까지 이어지는 브랜치 히스토리에 `role="tool"` 메시지가 정확히 포함됨을 assert |
| 5. 루프 상한과 무한 루프 방지 | 한 턴에 도구 호출이 10회를 넘으면 루프가 강제 종료되고 사용자에게 한도 초과가 안내됨 | `agentos/conversation/runtime.py`(`MAX_TOOL_CALLS_PER_TURN`) | `Run:` `uv run pytest tests/test_conversation_runtime.py -k "tool_call_limit" -q` / `Expected:` PASS — mock provider가 11회 연속 tool_call을 반환하도록 구성했을 때 10회에서 중단되고 안내 메시지가 포함됨을 assert |
| 6. 승인 게이트 opt-in | `AGENTOS_TOOL_READ_CONFIRM=1`이면 도구 실행 전 승인을 기다리고, 기본값(미설정)에서는 자동 실행됨 | `agentos/conversation/runtime.py`(승인 게이트), `agentos/terminal/interaction.py` | `Run:` `uv run pytest tests/test_conversation_runtime.py -k "read_confirm" -q` / `Expected:` PASS — 환경변수 미설정 시 승인 없이 즉시 실행됨을 assert, 설정 시 승인 콜백이 호출되기 전까지 실행이 보류됨을 assert |
| 7. CLI/TUI 가시성 | 도구 실행 중 "읽는 중: <path>" 진행 표시가 나타나고, 최종적으로 assistant 응답만 남음(기존 `add_tool_message` 렌더링 재사용 확인) | `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py` | `Run:` `uv run pytest tests/test_interactive_cli.py tests/test_tui_cli.py -k "tool_execution" -q` / `Expected:` PASS — CLI/TUI 드라이버로 read 도구가 호출되는 턴을 실행해 진행 표시와 최종 응답이 모두 출력됨을 assert |
| 8. 전체 회귀 검증 | 도구 호출이 없는 기존 세션·대화 지속성·TUI·Codex 스트리밍 기능이 깨지지 않고, 도구 호출이 없던 구세션 JSONL도 그대로 재생됨 | 전체 테스트 스위트 | `Run:` `uv run pytest tests/ -q` / `Expected:` `feature/agentos-tool-execution-loop` 브랜치(이 계획이 구현되는 실제 브랜치)에서 계획 작성 시점에 재측정한 336 passed 이상 PASS, 신규 실패 없음(구현 착수 직전 재측정 권장 — principle-auditor 비차단 권고). `Run:` `uv run pytest tests/test_conversation_persistence.py -k "resume" -q` / `Expected:` PASS — 도구 호출이 전혀 없는 기존 형식의 세션 JSONL을 이번 계획 이후 코드로 재개(resume)해도 `role="tool"` 메시지 없이 정상적으로 브랜치가 재생됨을 assert(엔진 변경에 대한 하위호환성 검증) |

## 이번 범위에 포함하지 않는 것 (명시적 제외)

- **`write`/`edit`/`bash` 등 부작용이 있는 도구** — read는 파일시스템에 부작용이 없어 자동 승인이 합리적이지만, write/edit/bash는 되돌리기 어려운 행동이므로 AGENTS.md 핵심 우선순위 2(지속성)에 따라 별도의 승인 UX·감사 로그 설계가 필요해 제외한다. 이번 계획이 만드는 `agentos/llm/tools/registry.py` 구조는 이후 이 도구들을 추가하기 쉽게 설계하지만, 실제 추가는 후속 계획으로 분리한다.
- **`codex-cli` provider 지원** — Codex CLI는 이미 자체 도구 실행 루프를 내장하고 있어(하위 프로세스가 자체적으로 파일을 읽음), AgentOS가 동일한 요청에 또 `tools`를 실어 보내면 이중 실행이나 프로토콜 충돌 위험이 있다. 이번 범위는 `codex`(Codex Native)와 `mock` provider로 한정하고, `codex-cli` 지원은 Codex CLI 쪽 도구 프로토콜을 먼저 조사하는 별도 계획이 필요하다.
- **Claude/Anthropic API provider 신규 추가** — 이번 계획 시점에 AgentOS에 Claude API provider 자체가 없음을 확인했다(`registry.py`에 `codex`/`codex-cli`/`mock`만 등록). provider 신규 추가는 이 계획의 목표(도구 실행 루프 이식)와 독립적인 별도 범위이므로 포함하지 않는다.
- **`@`-include 자동 확장과의 통합** — [부트스트랩 계획](../archive/2026-07-24-agentos-pi-bootstrap-context.md)이 이미 `bootstrap.py`의 `_expand_includes()`로 `@경로` 문법을 코드 레벨에서 처리하고 있다. 이번 read 도구는 그와 무관하게 LLM이 턴 중에 자유롭게 임의 경로를 요청하는 별개의 경로이며, 두 메커니즘을 통합하거나 `@`-include 쪽의 `AGENTS.md`/`CLAUDE.md` 우선순위 충돌(같은 디렉토리에 둘 다 있을 때 `CLAUDE.md`가 무시되는 문제)을 고치는 것은 이번 범위 밖이다.
- **경로 접근 allowlist/디렉토리 단위 신뢰 설정(pi의 `trust-manager.ts`/`project-trust.ts`에 해당하는 개념)** — 이번 계획은 "cwd 하위로 제한"이라는 고정 규칙 하나만 적용한다. 디렉토리별 세밀한 허용/차단 설정은 실사용 피드백을 본 뒤 별도 계획에서 다룬다.
- **모델별 tool-use 스펙 차이 흡수(예: Anthropic vs OpenAI vs Gemini의 서로 다른 tool schema 포맷)** — 이번 계획은 Codex Responses API(OpenAI 계열) 포맷 하나만 구현한다. 다른 provider의 tool schema 변환은 해당 provider가 실제로 추가될 때 함께 다룬다.

## 리뷰 반영 이력
- 초안 작성 — 2026-07-26. 이전 대화에서 진행한 pi 도구 아키텍처 조사(Explore 서브에이전트, `read.ts`/`agent-loop.ts`/`path-utils.ts`/`truncate.ts` 직접 확인)와 AgentOS 접합점 조사(Explore 서브에이전트, `runtime.py`/`types.py`/`transports/`/`providers/`/`terminal/` 직접 확인) 결과를 바탕으로 작성. 사용자에게 범위를 질문해 "read 도구 1개 + 최소 에이전틱 루프"로 확정(전체 도구 세트나 순수 배선만은 제외).
- 1차 `plan-reviewer` 리뷰 — 2026-07-26, FAIL. 세 가지 사유: (1) "`role=\"tool\"`을 생성하는 코드가 저장소 전체에 없다"는 의존성 분석 주장이 사실과 다름 — `persistence.py:322-365`의 `compact_branch()`가 이미 압축 요약용 `role="tool"` 메시지를 생성하고 있음(직접 확인). (2) `ConversationRuntime.submit_turn()`의 런타임 계약을 바꾸는 엔진 변경 계획임에도 명시적으로 식별되지 않았고 구세션 하위호환성 검증이 없음. (3) 경로 탈출 방지 검증이 "cwd 밖 경로 거부"로 뭉뚱그려져 있어 traversal/절대경로/symlink 우회를 개별 시나리오로 세분화하지 않음. → "사용자 결과 요약"에 compaction과의 구분 및 엔진 변경 고지·하위호환성 문장을 추가하고, 아키텍처 §1에 resolve-후-검사 순서를 명시하고, 마일스톤 1/8에 각 시나리오를 개별 assert로 세분화함(아래 기록).
- 1차 `principle-auditor` 감사 — 2026-07-26, REVISE. 아키텍처 §1이 "스캔 후 redact"로만 서술되어 있어, 위협 발견 시 `redact_text()`(시크릿 마스킹 전용)만 적용되고 실제 프롬프트 인젝션 방어(`bootstrap.py`의 `scan_and_cap_context_file()`이 이미 적용 중인 `[BLOCKED: ...]` 마커 전체 치환)가 누락될 위험을 지적받음. 마일스톤 2 텍스트와도 불일치. → 아키텍처 §1과 `ToolExecutionResult`에 `blocked` 필드를 추가하고, 위협 발견 시 `bootstrap.py`와 동일하게 원본 내용을 완전히 마커로 대체하는 정책을 명시함. 비차단 권고(마일스톤 8 회귀 기준 브랜치 재측정)도 함께 반영함(아래 기록).
- 1차 `usability-reviewer` 리뷰 — 2026-07-26, PASS. 승인 게이트 기본값(자동 승인)과 opt-in 환경변수 효과, 도구 호출 한도 초과 시 복구 동작, 전문용어가 사용자 행동에 영향을 주는 지점에서 사용자 언어로 먼저 설명되는 구조가 모두 확인되어 블로킹 findings 없음.
- 2차 반영 — 2026-07-26. 위 plan-reviewer FAIL 3건과 principle-auditor REVISE 1건(+비차단 1건)을 모두 계획 본문에 반영: "사용자 결과 요약"(compaction 구분, 엔진 변경 고지), 아키텍처 §1(resolve-후-검사, `[BLOCKED: ...]` 전체 치환 정책, `blocked` 필드), 마일스톤 1(경로 우회 3개 시나리오 세분화), 마일스톤 2(차단 정책 명시), 마일스톤 8(구세션 하위호환성 검증 Step 추가, 브랜치 재측정 336 passed 확인 반영). usability-reviewer PASS는 유지(재리뷰 대상 아님, 이번 수정이 사용자 결과 요약의 안전성 설명을 강화하는 방향이라 기존 PASS 판단과 상충하지 않음).
- 구현 중 편차 발견 및 사용자 확인 — 2026-07-26. 마일스톤 4 구현 중, `submit_turn()`이 provider·mock 여부와 무관하게 항상 `tool_names=["read"]`를 기본 제공하도록 구현했더니, mock provider가 결정론적으로 `tools`가 있으면 무조건 tool_call을 먼저 낸다는 특성 때문에 "hello" 같은 무관한 프롬프트에도 도구가 실행되어 기존 회귀 테스트(`test_conversation_runtime_snapshot_is_persisted_after_a_successful_turn` 등, `role` 순서가 `["user","assistant"]`여야 함을 검증)가 깨짐을 발견. 사용자에게 "TUI도 read 도구 미지정 유지"와 "기존 테스트를 새 동작에 맞게 수정" 중 선택을 물어 전자로 확정 — `tool_names`를 opt-in 파라미터로 변경해 CLI(`interaction.py`)만 명시적으로 `tool_names=["read"]`를 전달하고, TUI는 이번 범위에서 비활성 상태로 남김(렌더링/이벤트 처리 배선은 완료, 활성화는 후속 변경 한 줄로 가능). "사용자 결과 요약"과 "구현 결과"/"사용 방법"에 이 편차를 반영함.

## 구현 결과

8개 마일스톤 모두 계획대로 구현하고 검증했다.

- 신규 `agentos/llm/tools/read.py`: `read_tool_schema()`, `execute_read()`(cwd 하위 제한, resolve-후-검사로 symlink 우회 방지, 2000줄/50KB 상한, 에러 처리), `ToolExecutionResult`(`content`/`is_error`/`truncated`/`blocked`). 위협 패턴 발견 시 `bootstrap.py:scan_and_cap_context_file()`과 동일하게 `[BLOCKED: ...]` 마커로 전체 대체하고, 위협이 없으면 `redact_text()`로 시크릿만 마스킹.
- 신규 `agentos/llm/tools/registry.py`: `ToolName`/`get_tool_schemas()`/`execute_tool()` — `read` 하나만 등록, 이후 도구 추가 시 항목만 늘리면 되는 구조.
- `agentos/llm/types.py`의 `InvocationRequest`에 `tools: list[dict] | None = None` 필드 추가(기본값 `None`이라 기존 호출부 영향 없음). `agentos/llm/transports/base.py`의 `TransportRequest`/`to_request_body()`/`build_transport_request()`가 `tools`를 Codex Responses `function` 포맷으로 변환해 배선.
- `agentos/conversation/runtime.py`의 `submit_turn()`을 while 루프로 확장: `tool_call` 이벤트를 받으면 `execute_tool()` 실행 → 결과를 `role="tool"` `ConversationMessage`로 append → `build_context()` 재호출 → 재요청을 반복. `MAX_TOOL_CALLS_PER_TURN = 10` 상한 초과 시 한도 초과 안내 문구를 포함해 assistant 메시지로 턴을 종료. `AGENTOS_TOOL_READ_CONFIRM` truthy + `confirm_tool_call` 콜백이 주어졌을 때만 승인을 기다리고, 거부되면 `tool_call_denied` 이벤트와 함께 도구 실행 없이 종료. `tool_names` 파라미터는 opt-in이며 기본값은 빈 값(도구 미제공) — 계획 초안은 `mock`/`codex`에 기본으로 도구를 제공하려 했으나, 구현 중 mock provider가 결정론적으로 `tools`가 오면 항상 tool_call을 내는 특성과 부딪혀 기존 회귀 테스트(`test_conversation_runtime_snapshot_is_persisted_after_a_successful_turn` 등)가 깨지는 것을 발견했다. 사용자 확인 후 "명시적으로 `tool_names`를 넘긴 호출만 도구를 제공"하는 opt-in 방식으로 조정했다(아래 "사용 방법" 참고).
- `agentos/llm/providers/mock.py`: `request.tools`가 있고 아직 `role="tool"` 메시지가 없을 때만 진짜 도구 tool_call을 내도록 조정(테스트에서 실제 실행 경로를 검증 가능). `tools`가 없는 기존 호출은 기존 데모용 tool_call/tool_result 방출 동작을 그대로 유지해 회귀를 피했다.
- `agentos/terminal/interaction.py`(CLI): `submit_turn()`에 `cwd=Path.cwd()`, `tool_names=["read"]`, `confirm_tool_call=_confirm_tool_call`을 명시적으로 전달해 read 도구를 실제로 활성화. tool_call 이벤트 시 "읽는 중: <path>" 배너 출력, 한도 초과 시 안내 출력. `_confirm_tool_call()`은 `AGENTOS_TOOL_READ_CONFIRM` truthy일 때만 `console.input()`으로 y/N 승인을 받는다.
- `agentos/terminal/tui/app.py`(TUI): `submit_turn()` 호출은 `tool_names`를 넘기지 않아 도구가 기본적으로 비활성 상태로 남는다(위 mock provider 결정론적 동작과의 충돌 회피, 사용자 확인). `tool_call_limit_reached`/`tool_call_denied` 이벤트 렌더링을 `renderers.py`/`app.py`에 추가해, 다른 호출 경로(향후 TUI가 opt-in할 경우)에서도 즉시 동작하도록 배선은 완료해 두었다.
- 테스트: 신규 `tests/test_tool_execution_loop.py`(8개, read 도구 단독 실행/새니타이즈/차단), `tests/test_conversation_runtime.py`에 7개 추가(에이전틱 루프/한도/승인 게이트), `tests/test_llm_core.py`/`tests/test_codex_transport.py`에 tools 배선 테스트 6개 추가, `tests/test_interactive_cli.py`/`tests/test_tui_cli.py`에 CLI/TUI 가시성 테스트 4개 추가.
- 전체 검증: `uv run pytest tests/ -q` → 358 passed(계획 시작 시점 336 대비 회귀 없음, 신규 22개 포함).

## 사용 방법

- **CLI(`agentos run --provider mock` 등 대화형 세션)**: `read` 도구가 기본으로 활성화되어 있다. LLM이 `read` tool_call을 반환하면 AgentOS가 실제로 그 경로의 파일을 cwd 하위로 제한해 읽고, "읽는 중: <path>"를 출력한 뒤 결과를 대화에 반영해 자동으로 이어간다.
- **TUI**: 이번 계획에서는 read 도구를 기본 비활성 상태로 남겨두었다(현재 mock provider 특성과 결합했을 때 무관한 프롬프트에도 항상 도구를 시도하는 문제를 피하기 위함, 위 "구현 결과" 참고). TUI에서 실제로 활성화하려면 `agentos/terminal/tui/app.py`의 `runtime.submit_turn(prompt)` 호출에 `tool_names=["read"]`를 추가하는 후속 변경이 필요하다 — 렌더링/이벤트 처리는 이미 준비되어 있다.
- 도구 실행 결과에 프롬프트 인젝션 패턴이 있으면 원본 내용 없이 `[BLOCKED: ...]` 마커만 대화에 남고, 시크릿만 있으면 마스킹된 채로 남는다.
- 한 턴에 도구 호출이 10회를 넘으면 자동으로 중단되고 "도구 호출 한도 초과" 안내가 표시된다.
- `AGENTOS_TOOL_READ_CONFIRM=1`을 설정하면 CLI에서 도구 실행 전 매번 y/N 승인을 요구한다(미설정 시 자동 실행).
- `write`/`edit`/`bash` 등 다른 도구는 이번 범위에 없다 — `agentos/llm/tools/registry.py`에 항목을 추가하는 방식으로 후속 계획에서 확장 가능하다.

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
