# Claude(Anthropic) OAuth LLM Provider 추가 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (Gate 2 3종 PASS, 증거: `.agents/traces/reviews/2026-07-27-claude-oauth-provider/{plan-reviewer,principle-auditor,usability-reviewer}.md`)<br>
> implementation_started_at: 2026-07-27T06:18:26Z<br>
> implementation_completed_at: 2026-07-27T06:34:28Z<br>
> implementation_duration: 약 16분<br>

> **usability_review_required:** true<br>
> usability_review_reason: 이 계획은 `agentos llm login --provider claude`, `agentos run --provider claude`, TUI의 provider 선택/로그인 안내 문구를 추가해 사용자가 직접 상호작용하는 로그인 흐름과 에러 메시지를 새로 만든다.<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

## 실행 방식 계약

> `contract_version: 1`<br>
> `execution_mode: local-agent`<br>
> `executor:` 현재 세션 에이전트 (Claude Code)<br>
> `handoff_required: false`<br>
> `verification_owner:` 현재 세션 에이전트<br>
> `return_evidence:` 각 Task의 `Run`/`Expected` 출력, pytest 결과<br>

**목표:**
- AgentOS에 Google이 아닌 **Anthropic Claude를 OAuth 기반 계정 로그인으로 사용하는 새 LLM provider**(`claude`)를 추가한다. API 키 대신 Claude Pro/Max 구독 계정으로 로그인해 대화형 세션(`agentos run`, `agentos tui`)에서 Claude 모델을 사용할 수 있게 한다.

**사용자 결과 요약:**
- 최종 결과: 사용자가 `agentos llm login --provider claude`로 브라우저(또는 디바이스 코드) 로그인을 완료하면, `agentos run --provider claude` 또는 `agentos --provider claude`로 Claude 모델과 대화하고, 기존 read/list/glob/grep/write/edit/bash 7개 도구를 Claude에게도 그대로 쓸 수 있다.
- 대상 독자: Claude Pro/Max 구독을 이미 보유한 AgentOS 사용자.
- 일상 사용의 변화: 이전에는 `codex`(ChatGPT 계정)와 `mock`만 provider로 선택 가능했다. 이후에는 `claude`도 동일한 방식(`--provider claude`)으로 선택 가능해지고, `/status`·`/login` 등 기존 TUI 슬래시 명령이 그대로 동작한다.
- 바뀌지 않는 경계: `codex`/`codex-cli`/`mock`의 동작, 인증 저장 스키마(`AuthFileStore`/`auth.json`), 기존 도구 실행/승인 정책, TUI 레이아웃.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등):
  - Anthropic의 OAuth 엔드포인트(`https://claude.ai/oauth/authorize`, `https://platform.claude.com/v1/oauth/token`) 및 Messages API(`https://api.anthropic.com/v1/messages`)에 대한 네트워크 접근.
  - **client_id 재사용에 대한 의도적 판단** — 아래 "위임 방식과 리스크" 절 참고. 신규 등록이나 사용자 제공 값이 아니라, Anthropic이 공식 Claude Code CLI에 발급한 공개 client_id를 그대로 재사용한다.
  - 사용자는 Claude Pro/Max 구독 계정(또는 API 콘솔 계정 중 OAuth 로그인이 허용된 계정)이 있어야 실제 로그인을 완료할 수 있다. 로그인 UI 자체는 계정 없이도 뜨지만, 실사용 검증(실제 브라우저 로그인 성공)은 사용자 계정이 필요해 이 세션에서 자동화할 수 없다.

**의존성 게이트:**

| name | type | required | preflight Run/Expected | fallback | failure_behavior |
|---|---|---|---|---|---|
| Anthropic OAuth authorize/token 엔드포인트 (`claude.ai/oauth/authorize`, `platform.claude.com/v1/oauth/token`) | network | 실사용 로그인 시 필수, 단위 구현/검증 시 불필요 | `Run:` `curl -sI --max-time 10 https://claude.ai/oauth/authorize` / `Expected:` HTTP 응답(리다이렉트 3xx 또는 4xx 포함, DNS/TLS 실패 아님)으로 엔드포인트 도달 가능성만 확인. 이 preflight는 Task 1 착수 직전 1회 실행하며, 인증 자체를 수행하지 않는다. | 구현·단위 테스트는 `HttpTransport` fake로 전부 수행하며 실네트워크 없이 Task 1-4 전부 완료 가능 | preflight 실패(DNS/TLS/timeout) 시 Task 1 착수를 중단하지 않되, 계획 진행 상태에 "엔드포인트 도달성 미확인" 경고를 기록하고 사용자에게 네트워크 환경을 알린다(`NEEDS_CONTEXT`) |
| Anthropic Messages API (`api.anthropic.com/v1/messages`) | network | 실사용 대화 시 필수, 단위 구현/검증 시 불필요 | `Run:` `curl -sI --max-time 10 https://api.anthropic.com/v1/messages` / `Expected:` HTTP 응답(401/405 등 포함, DNS/TLS 실패 아님) | 구현·단위 테스트는 fake SSE client로 전부 수행 | 동일하게 `NEEDS_CONTEXT` — 실사용 검증(실제 로그인·실제 대화)은 사용자 계정이 필요해 이 세션에서 완결할 수 없음을 계획 완료 조건에서 별도로 명시(아래 "완료 신호" 참고) |

**위임 방식과 리스크 (사용자 승인 완료):**
- 레퍼런스 프로젝트 `pi`(`packages/ai/src/auth/oauth/anthropic.ts`)는 Anthropic이 공식 Claude Code CLI용으로 발급한 client_id(`9d1c250a-e61b-44d9-88ed-5944d1962f5e`, base64 인코딩되어 소스에 저장됨)와 `claude.ai/oauth/authorize` / `platform.claude.com/v1/oauth/token` 엔드포인트를 그대로 재사용한다. 이 client_id는 client_secret이 없는 **공개(public) OAuth 클라이언트** 값으로, PKCE만으로 인증하며 그 자체가 비밀정보는 아니다.
- 단, 이 client_id로 얻은 OAuth 토큰을 Messages API에 쓸 때는 Anthropic 서버가 "공식 Claude Code CLI 요청"으로 인식하도록 `anthropic-beta: claude-code-20250219,oauth-2025-04-20`, `user-agent: claude-cli/<version>`, `x-app: cli` 헤더를 함께 보내야만 요청이 통과한다(`pi`의 `packages/ai/src/api/anthropic-messages.ts:873-894`). 이는 서드파티 도구가 Claude Code 전용 자격증명 발급 경로를 그대로 활용하는 것이므로, 비밀 유출이나 보안 취약점이 아니라 **Anthropic 서비스 약관/정책상 회색지대**다. 사용자에게 이 트레이드오프를 설명했고, `pi`와 동일한 방식으로 진행하기로 승인받았다(2026-07-27 대화 기록).
- 이 판단에 따르는 리스크: Anthropic이 향후 User-Agent/헤더 조합 검사를 강화하거나 서드파티의 이 패턴을 차단하면, 이 provider는 예고 없이 동작을 멈출 수 있다. 이는 코드 결함이 아니라 외부 서비스 정책 리스크이므로, 문서(`docs/cli-reference.md`)에 이 경계를 명시한다.
- **정책 차단과 일반 인증 만료를 구분하는 사용자 신호(usability-reviewer 지적 반영):** 이 리스크가 실제로 발생했을 때, 사용자가 "내 구독이 만료됐나?"와 "Anthropic이 이 통합 자체를 막았나?"를 구분하지 못하면 반복 재로그인으로 시간을 낭비하거나 AgentOS를 오작동으로 오인하게 된다. Anthropic은 이 위장 패턴을 위한 공식 에러 타입을 문서화하지 않았으므로, **판별 규칙은 사용 가능한 단 하나의 신호 — Messages API 에러 응답의 `error.type` 필드 — 만으로 지금 확정한다(principle-auditor 2차 지적 반영, 반복 요청 패턴에 기반한 휴리스틱은 이 계획에서 완전히 제거한다):**
  - `error.type == "authentication_error"`(Anthropic Messages API가 공식 문서화한 표준 인증 실패 타입, 만료/폐기된 토큰에 해당) → `code="token_expired"`, 메시지 "Claude 로그인이 만료되었습니다. 다시 로그인하세요." + `RECOVERY_LOGIN = "Run: agentos llm login --provider claude"`.
  - 그 외 모든 4xx 에러(`error.type`이 `authentication_error`가 아닌 401/403, 또는 `error.type` 자체가 없는 401/403 — 위장 헤더 조합이 거부될 때 Anthropic이 실제로 어떤 `error.type`을 반환할지 사전에 알 수 없으므로, "표준 인증 실패로 명시적으로 확인되지 않은 모든 401/403"을 보수적으로 이 분류에 넣는다) → `code="claude_integration_blocked"`, 메시지 "Claude 로그인 연동이 Anthropic 정책 변경으로 차단되었을 수 있습니다(알려진 리스크). 재로그인으로 해결되지 않으면 AgentOS 업데이트를 확인하세요." + recovery "Check for an AgentOS update; this is a documented policy risk, not a bug you caused."
  - 이 규칙은 **단일 에러 응답 하나만으로 즉시 판별 가능**하다 — 여러 요청에 걸친 상태나 재시도 횟수 추적이 전혀 필요 없다. `classify_auth_failure(error_type: str | None, status_code: int) -> str`은 이 두 갈래 조건문 하나로 구현되며, Task 1에서 이 정확한 규칙 그대로 작성하고 그 자리에서 두 케이스(각각의 입력값 조합)를 단정하는 단위 테스트로 완결한다(Task 3으로 미루지 않는다).
  - 이 분류가 실제 Anthropic 서버 동작과 다를 수 있다는 점(추측에 기반한 보수적 규칙)은 문서(Task 5)에도 명시한다 — 오분류가 있어도 사용자가 받는 두 문구 모두 안전한 재로그인 시도를 막지 않으므로(어느 쪽이든 재로그인이 먼저 시도할 수 있는 합리적 행동), 이 보수적 판별 규칙의 실패 비용은 낮다.
- client_id/엔드포인트는 `AGENTOS_CLAUDE_CLIENT_ID` 등 환경변수로 오버라이드 가능하게 만든다(기존 `AGENTOS_CODEX_CLIENT_ID`/`AGENTOS_CODEX_ISSUER` 패턴과 동일).

**장기 적용 표면:**
- Traceability Surface: 이 계획 문서, `HISTORY.md`, `.agents/traces/reviews/2026-07-27-claude-oauth-provider/`.
- Durable Result Surface: `agentos/llm/auth/anthropic_claude.py`(신규), `agentos/llm/providers/claude_native.py`(신규), `agentos/llm/transports/anthropic_messages.py`(신규), `agentos/llm/transports/base.py`(Claude 전용 request 빌더 추가), `agentos/llm/registry.py`, `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py`, `docs/cli-reference.md`, `tests/`.

**진행 상태:** 계획 초안 작성 완료. hermes-agent(`/references/pi`) 참고 조사 완료, `add-llm-provider` 스킬(`/references/pi/.pi/skills/add-llm-provider.md`) 체크리스트를 AgentOS 파일 구조에 매핑 완료. Gate 2 리뷰 대기.

**아키텍처:**
- 새 provider `claude`는 기존 `codex`(`CodexNativeProvider`)와 동일한 3계층 구조(`auth` → `transport` → `provider`)를 따른다.
  - `agentos/llm/auth/anthropic_claude.py`: PKCE 기반 브라우저 로그인 흐름(로컬 콜백 서버), 토큰 교환/갱신, `AuthFileStore` 영속화. `agentos/llm/auth/openai_codex.py`의 함수 시그니처·에러 계층(`AuthError`/`StateMismatchError`/`BrowserLaunchFailedError`/`CallbackTimeoutError`)을 그대로 재사용하는 패턴으로 작성한다.
  - `agentos/llm/transports/anthropic_messages.py`: Claude Messages API(`/v1/messages`, SSE 스트리밍)를 호출하는 transport. `TransportRequest`/`ProviderEvent`(`agentos/llm/transports/base.py`)의 provider-agnostic 계약을 그대로 따르되, Claude Messages 전용 request body(`system` 파라미터 분리, `messages` role은 `user`/`assistant`만, tool 결과는 `tool_result` content block)를 만드는 별도 빌더 `build_claude_transport_request()`를 추가한다. Codex의 `previous_response_id` 연속 개념이 Claude에는 없으므로(매 턴 전체 히스토리 재전송), `ProviderCapabilities(context_aware=True, supports_continuation=False)`로 선언한다.
  - **`ProviderEvent`의 Claude 멀티블록 스트림 표현(principle-auditor 지적 반영):** Claude Messages SSE는 `content_block_start`(인덱스 지정, `type: "text"` 또는 `"tool_use"`) → 해당 인덱스의 `content_block_delta` 여러 건 → `content_block_stop`을 블록별로 인터리브해서 보낸다(텍스트 블록과 tool_use 블록이 같은 응답 안에서 여러 개, 순서 섞여 도착 가능). `ProviderEvent`(`agentos/llm/transports/base.py:52-65`)는 필드를 추가하지 않고 그대로 둔다 — 대신 `anthropic_messages.py` 내부에서만 인덱스별 블록 상태(`dict[int, {"type": str, "text_buffer": str, "tool_json_buffer": str}]`)를 누적하는 로컬 상태 머신을 두고, 블록이 완결(`content_block_stop`)되거나 텍스트 델타가 도착하는 시점에만 이미 존재하는 `ProviderEvent(type="message_delta", text=...)` 또는 `ProviderEvent(type="tool_call", metadata={"name":..., "arguments":..., "call_id":...})`를 방출한다. 이 방식은 `codex`가 쓰는 `ProviderEvent`/`TransportRequest` 공유 계약을 필드 추가 없이(non-breaking) 그대로 재사용하며, `codex` transport의 동작에는 전혀 영향을 주지 않는다. 이 설계 결정과 그 이유(계약 불변, 상태 머신은 transport 내부에 격리)를 Task 2에서 구현하고 격리된 회귀 테스트로 고정한다(아래 Task 2 참고) — Milestone 5의 전체 회귀 테스트까지 기다리지 않고 Task 2 시점에 `tests/test_codex_transport.py`(기존 codex 계약 무변경 확인)를 함께 재실행해 공유 파일 변경의 부작용을 그 자리에서 게이트한다.
  - `agentos/llm/providers/claude_native.py`: `CodexNativeProvider`와 동일한 `LLMProvider` 프로토콜(`status`/`login`/`logout`/`stream_once`/`stream_context`/`capabilities`)을 구현하는 `ClaudeNativeProvider`.
  - Tool 스키마 변환: 기존 `agentos/llm/tools/registry.py`의 OpenAI 스타일 스키마(`name`/`description`/`parameters`)를 Claude 스타일(`name`/`description`/`input_schema`)로 변환하는 얇은 매핑 함수를 transport 계층에 추가한다(도구 정의 자체는 provider-neutral하게 유지).
- 등록: `agentos/llm/registry.py`의 `build_default_registry()`에 `registry.register("claude", ClaudeNativeProvider)` 한 줄 추가. `agentos/llm/session.py`, `agentos/commands/llm.py`는 이미 provider-agnostic이라 수정 불필요.
- CLI/TUI 배선: `agentos/terminal/interaction.py`(`if provider in ("codex", "codex-cli")` 분기에 `"claude"` 추가하거나 provider별 기본 모델 조회 함수로 일반화), `agentos/terminal/tui/app.py`의 `_AVAILABLE_PROVIDERS = ("mock", "codex")`에 `"claude"` 추가, `_default_model_for_provider()`에 Claude 기본 모델 매핑 추가.
- 범위 밖: `claude-cli`(설치된 Claude Code CLI 프로세스에 위임하는 보조 경로 — 사용자가 이번 요청에서 제외하기로 결정), API 키 방식 인증(순수 OAuth만), Vertex AI/Bedrock 경유 Claude, 이미지/파일 업로드 입력.

**기술 스택:** Python 3, `urllib`(HTTP), `http.server`(로컬 OAuth 콜백), pytest.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Gate 2 리뷰(3차, 전원 PASS) 완료 후 Task 1-5 구현·검증 완료 |
| 완료됨 | Gate 2 리뷰 3종 PASS, Task 1-5 구현, 전체 테스트 스위트 496 passed(회귀 없음), `git diff --check` 통과, 문서 정책 리스크 문구 반영 확인 |
| 현재 위치 | 구현·검증 완료. 실제 브라우저 로그인 최종 확인 대기 |
| 다음 단계 | 사용자가 실제 Claude 계정으로 `agentos llm login --provider claude` 로그인 및 대화를 시도해 최종 확인 |
| 완료 신호 | 아래 Task별 `Run`/`Expected` 전부 PASS(확인됨) + 전체 테스트 스위트 회귀 없음(확인됨) + 사용자가 실제 브라우저 로그인으로 최종 확인(자동화 불가 영역, 미확인) |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Claude OAuth 로그인 흐름 | `agentos llm login --provider claude` 실행 시 브라우저 로그인 URL이 뜨고, 로그인 완료 후 `agentos llm status --provider claude`가 인증됨을 보고한다 | `agentos/llm/auth/anthropic_claude.py`, `agentos/llm/auth/store.py`(재사용, 수정 없음) | `Run:` `uv run pytest -q tests/test_claude_oauth.py` / `Expected:` PASS — PKCE 생성, 콜백 서버, 토큰 교환/갱신, 로그아웃, redaction(원문 토큰이 에러/로그에 노출되지 않음)을 모두 fake transport로 검증 |
| 2. Claude Messages API 스트리밍 transport | 로그인 후 실제 대화 요청을 보내면 Claude 응답이 스트리밍으로 표시된다 | `agentos/llm/transports/anthropic_messages.py`, `agentos/llm/transports/base.py`(Claude request 빌더 추가) | `Run:` `uv run pytest -q tests/test_claude_transport.py` / `Expected:` PASS — SSE 프레임 매핑(`message_start`/`content_block_delta`/`content_block_start` tool_use/`message_delta` usage/`message_stop`/`error`)을 fake SSE 클라이언트로 검증 |
| 3. `ClaudeNativeProvider` + registry 등록 | `agentos llm status --provider claude`, `agentos run --provider claude "hello"` 가 `UnsupportedProviderError` 없이 동작한다 | `agentos/llm/providers/claude_native.py`, `agentos/llm/registry.py` | `Run:` `uv run pytest -q tests/test_claude_provider.py tests/test_llm_core.py` / `Expected:` PASS — `supported_providers()`에 `"claude"` 포함, `stream_context`/`stream_once`가 `LLMEvent` 정규 이벤트를 생성함을 검증 |
| 4. Tool 스키마 변환 | Claude 세션에서도 read/list/glob/grep/write/edit/bash 7개 도구가 정상 호출되고 승인 정책이 동일하게 적용된다 | transport 계층의 OpenAI→Claude tool 스키마 매핑 함수, `agentos/llm/tools/registry.py`(수정 없음, 그대로 재사용) | `Run:` `uv run pytest -q tests/test_claude_transport.py -k tool` / `Expected:` PASS — 7개 도구 스키마가 `input_schema` 키로 변환됨을 검증, `tool_use`/`tool_result` 왕복 시퀀스 테스트 |
| 5. CLI/TUI 배선 및 문서 | `agentos --provider claude`, TUI provider 메뉴에서 Claude 선택, `/login` 슬래시 명령이 Claude에도 동작 | `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py`, `docs/cli-reference.md` | `Run:` `uv run pytest -q tests/test_interactive_cli.py tests/test_tui_cli.py -k claude && uv run pytest -q` / `Expected:` 신규 테스트 PASS, 전체 스위트 회귀 없음 |

## 구현 단계

### Task 1: Claude OAuth 인증 흐름 (`agentos/llm/auth/anthropic_claude.py`)

**파일:**
- 신규: `agentos/llm/auth/anthropic_claude.py`
- 신규: `tests/test_claude_oauth.py`
- 수정 없음(재사용): `agentos/llm/auth/store.py`, `agentos/llm/auth/types.py`

- [ ] `agentos/llm/auth/openai_codex.py`를 그대로 대응 복제하는 방식으로 아래 상수/함수를 만든다. 이름은 codex와 대칭되게 짓되 Anthropic 값으로 채운다:
  - `DEFAULT_AUTHORIZE_URL = "https://claude.ai/oauth/authorize"`, `DEFAULT_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"`, `CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"`(pi `anthropic.ts:29`의 base64 디코딩 값 그대로), `SCOPES = "org:create_api_key user:profile user:inference user:sessions:claude_code user:mcp_servers user:file_upload"`(pi `anthropic.ts:36-37`와 동일), `AUTH_PROVIDER_NAME = "claude"`, `CREDENTIAL_TYPE = "account-login"`.
  - `_env_authorize_url()`/`_env_token_url()`/`_env_client_id()`: `AGENTOS_CLAUDE_AUTHORIZE_URL`/`AGENTOS_CLAUDE_TOKEN_URL`/`AGENTOS_CLAUDE_CLIENT_ID` 환경변수로 오버라이드(codex의 `_env_issuer()`/`_env_client_id()`와 동일 패턴).
  - `generate_pkce()`/`generate_state()`: `openai_codex.py`의 동명 함수를 그대로 재사용(로직 동일, 이 파일에 복제할 필요 없이 `from agentos.llm.auth.openai_codex import generate_pkce, generate_state`로 import해서 쓴다 — 두 provider 모두 표준 PKCE이므로 함수 자체는 provider-neutral).
  - `HttpTransport`/`UrllibHttpTransport` 프로토콜도 `openai_codex.py`에서 import해 재사용(HTTP POST/브라우저 열기는 provider-neutral).
  - `AuthError`/`StateMismatchError`/`BrowserLaunchFailedError`/`CallbackTimeoutError` 예외 계층도 `openai_codex.py`에서 import해 재사용(메시지는 provider 이름을 담지 않으므로 그대로 공용 가능).
- [ ] `build_authorize_url(*, authorize_url, client_id, redirect_uri, state, pkce)`: codex의 `build_authorize_url()`과 동일한 시그니처로 새로 작성하되, Anthropic 파라미터 이름에 맞춘다 — `response_type=code`, `client_id`, `redirect_uri`, `scope=SCOPES`, `code_challenge`, `code_challenge_method=S256`, `state`. pi의 `anthropic.ts:239-248`은 `state`에 PKCE `verifier`를 그대로 쓰는데(별도 state 값 없음), 이 계획은 codex와 동일하게 `state`와 `verifier`를 분리된 값으로 유지한다 — Anthropic 서버가 `state`를 그대로 콜백에 반사하는 한 이 분리는 안전하며, codex 패턴과의 일관성을 우선한다.
- [ ] `prepare_browser_login()`/`complete_browser_login()`/`run_browser_login()`: codex의 동명 함수와 동일한 구조(로컬 `HTTPServer` 콜백, `PreparedBrowserLogin` dataclass)로 작성하되 콜백 경로는 `/auth/callback`, 포트는 `DEFAULT_CALLBACK_PORT = 53692`(pi `anthropic.ts:33`와 동일), fallback 포트는 `53693`으로 정한다.
- [ ] `_exchange_code_for_tokens()`: Anthropic 토큰 엔드포인트에 POST하는 함수. codex는 `grant_type=authorization_code`+`client_id`+`redirect_uri`+`code`+`code_verifier`를 보내는데, Anthropic도 pi `anthropic.ts:198-205`에서 동일한 필드(`grant_type`, `client_id`, `code`, `state`, `redirect_uri`, `code_verifier`)를 JSON body로 보낸다(codex는 이 body를 JSON으로 보내는 반면, `openai_codex.py`도 이미 JSON POST를 쓰므로 형식 차이 없음). 응답은 `access_token`/`refresh_token`/`expires_in`(Anthropic은 `id_token` 없음 — codex의 `TokenResult.id_token` 같은 JWT 클레임 파싱이 필요 없다는 차이를 명시).
- [ ] `TokenResult` dataclass: `access_token: str`, `refresh_token: str`, `expires_in: float | None = None`(codex의 `id_token`/`account_label` 필드는 Claude에 없으므로 제외 — Claude는 계정 라벨을 별도로 받지 않고, `account_label=None`으로 항상 저장한다).
- [ ] `persist_tokens(tokens, *, store: AuthFileStore) -> AuthRecord`: `AuthRecord(provider="claude", credential_type="account-login", authenticated=True, secrets={"access_token":..., "refresh_token":...}, metadata={"expires_at": time.time() + expires_in})`. codex의 `id_token` 저장은 하지 않는다(Claude 토큰에는 없음).
- [ ] `refresh_access_token(refresh_token, ...)`: `grant_type=refresh_token`+`client_id`+`refresh_token`으로 POST(pi `anthropic.ts:311-315`와 동일 필드). codex와 동일하게 `_REFRESH_LOCK`으로 동시 갱신을 직렬화한다.
- [ ] `resolve_status(store, ...)`: codex의 `resolve_status()`와 동일 구조 — 만료 전이면 `authenticated`, 만료됐고 `refresh_token`이 있으면 갱신 시도 후 재저장, 실패하면 `expired`.
- [ ] `logout(store)`: `store.delete("claude")`.
- [ ] **정책 차단 감지(위임 방식과 리스크 절에서 확정한 규칙 그대로 구현, Task 3으로 미루지 않음):** `classify_auth_failure(error_type: str | None, status_code: int) -> str` 헬퍼를 추가한다. 로직은 정확히 두 갈래다 — `if status_code in (401, 403) and error_type == "authentication_error": return "token_expired"`, `elif status_code in (401, 403): return "claude_integration_blocked"`, 그 외 상태 코드는 이 함수의 책임이 아니므로 별도 처리하지 않는다(호출자가 401/403이 아닌 응답에는 이 함수를 쓰지 않는다). 단일 에러 응답 하나(상태 코드 + `error.type` 문자열)만으로 결정되며, 여러 요청에 걸친 상태나 재시도 횟수는 전혀 필요 없다.
- [ ] `tests/test_claude_oauth.py`에 codex의 `tests/test_codex_oauth.py`와 대응하는 케이스를 작성한다: PKCE 생성, authorize URL 구성, fake transport로 브라우저 로그인 성공/state mismatch/callback timeout, 토큰 교환 실패, 토큰 갱신 성공/실패, `resolve_status()`의 만료 전/후/갱신 성공/갱신 실패, `logout()`, **`classify_auth_failure()`가 `("authentication_error", 401)` → `"token_expired"`, `(None, 401)` → `"claude_integration_blocked"`, `("some_other_type", 403)` → `"claude_integration_blocked"` 세 입력 조합을 정확히 그 값으로 반환함을 단정하는 테스트**, 그리고 **모든 `AuthError` 메시지와 `to_dict()` 출력에 원문 `access_token`/`refresh_token` 문자열이 포함되지 않음을 단정하는 redaction 테스트**(codex의 redaction 테스트 패턴을 그대로 따름 — 실제 토큰 문자열을 assert 대상 텍스트에서 `not in`으로 검증).

Run: `uv run pytest -q tests/test_claude_oauth.py`
Expected: 전체 PASS. `classify_auth_failure()`의 세 입력 조합이 정확히 명시된 값을 반환함을 확인하고(이 규칙 자체가 Task 1에서 완결됨 — Task 3은 이 함수를 호출만 함), redaction 테스트가 임의의 토큰 문자열(`"sk-ant-oat-test-secret-value"` 등 테스트 전용 더미)을 만들어 `AuthError` 메시지·`AuthRecord.to_dict()` 어디에도 그 문자열이 그대로 나타나지 않음을 확인한다.

### Task 2: Claude Messages API 스트리밍 transport (`agentos/llm/transports/anthropic_messages.py`)

**파일:**
- 신규: `agentos/llm/transports/anthropic_messages.py`
- 수정: `agentos/llm/transports/base.py`(Claude 전용 request 빌더 추가, 기존 `TransportRequest`/`ProviderEvent`는 필드 변경 없음)
- 신규: `tests/test_claude_transport.py`
- 수정 없음(회귀 확인만): `tests/test_codex_transport.py`

- [ ] `agentos/llm/transports/base.py`에 `build_claude_transport_request(*, model, invocation_request, session_id=None) -> TransportRequest`를 `build_transport_request()` 옆에 추가한다. 기존 함수는 그대로 두고 손대지 않는다(codex 계약 무변경). 새 함수는 `invocation_request.messages`에서 `role="system"` 메시지를 `TransportRequest.instructions`(Claude Messages의 top-level `system` 파라미터로 매핑될 문자열)로 분리하고, 나머지는 `user`/`assistant` role 메시지로, `role="tool"` 메시지는 (call_id/name/arguments가 완전하면) 원 호출을 나타내는 `assistant` 메시지의 `tool_use` content block과 뒤따르는 `user` 메시지의 `tool_result` content block 쌍으로 변환한다(Claude Messages는 tool 호출·결과를 `role="assistant"`/`role="user"` 메시지 안의 content block으로 표현하며, Responses API처럼 최상위 `function_call`/`function_call_output` 타입이 없다 — 이 차이가 codex 대비 가장 큰 스키마 차이이므로 명시).
- [ ] `TransportRequest.to_request_body()`는 codex 전용 필드(`store`, `previous_response_id`, `input`)를 만들므로 Claude에는 재사용하지 않는다 — `anthropic_messages.py` 안에 별도 `_build_request_body(request: TransportRequest) -> dict`를 두어 Claude Messages 스키마(`model`, `system`, `messages`, `max_tokens`, `stream: true`, `tools`)로 직접 조립한다. `TransportRequest.tools`(OpenAI 스타일 `name`/`description`/`parameters`)는 `_tools_to_claude_schema()`로 `name`/`description`/`input_schema`(= 기존 `parameters` 값 그대로, 키 이름만 변경)로 변환한다.
- [ ] `CLAUDE_MESSAGES_URL = "https://api.anthropic.com/v1/messages"`(환경변수 `AGENTOS_CLAUDE_BASE_URL`로 오버라이드 가능, codex의 `AGENTOS_CODEX_BASE_URL` 패턴과 동일).
- [ ] `_headers(access_token)`: `{"content-type": "application/json", "authorization": f"Bearer {access_token}", "accept": "text/event-stream", "anthropic-beta": "claude-code-20250219,oauth-2025-04-20", "anthropic-version": "2023-06-01", "user-agent": f"claude-cli/{CLAUDE_CLI_VERSION_STRING}", "x-app": "cli"}`(pi `anthropic-messages.ts:880-890`의 OAuth 분기 헤더 그대로 — `CLAUDE_CLI_VERSION_STRING`은 임의의 고정 문자열 상수, 예: `"1.0.0"`).
- [ ] SSE 프레임 매핑 `map_claude_frame(frame, block_state) -> ProviderEvent | None`(아키텍처 절의 "ProviderEvent의 Claude 멀티블록 스트림 표현" 설명대로 인덱스별 블록 상태를 인자로 받아 갱신하며 완결 이벤트만 반환):
  - `message_start` → `ProviderEvent(type="start", metadata={"transport": "claude-messages"})`
  - `content_block_start`(`content_block.type == "text"`) → 해당 인덱스를 텍스트 블록으로 등록, 이벤트 없음(`None`)
  - `content_block_start`(`content_block.type == "tool_use"`) → 해당 인덱스를 tool_use 블록으로 등록(`id`, `name` 저장), 이벤트 없음
  - `content_block_delta`(`delta.type == "text_delta"`) → `ProviderEvent(type="message_delta", text=delta.text)`
  - `content_block_delta`(`delta.type == "input_json_delta"`) → 해당 인덱스의 `tool_json_buffer`에 `partial_json` 누적, 이벤트 없음(codex의 `arguments.delta` 무시 패턴과 동일 이유 — 완결 시점에만 파싱)
  - `content_block_stop`(해당 인덱스가 tool_use 블록) → 누적된 JSON을 파싱해 `ProviderEvent(type="tool_call", metadata={"name":.., "arguments":{...}, "call_id": tool_use_id})`
  - `message_delta`(`usage` 포함) → 최종 `usage` 값을 버퍼에 저장, 이벤트 없음(아직 `done` 아님 — Claude는 `usage`를 `message_delta`에서, 종료는 `message_stop`에서 별도로 보냄)
  - `message_stop` → `ProviderEvent(type="done", usage=buffered_usage)`
  - `error`(top-level) → `ProviderEvent(type="error", error={"code": ..., "message": redact_text(...)})` — 여기서 Task 1의 `classify_auth_failure()` 판정을 적용해 `code`를 `"token_expired"` 또는 `"claude_integration_blocked"` 중 하나로 세팅(이 매핑 로직 자체는 transport에 두고, provider 레이어의 `_error_event()`가 이 code를 그대로 전달).
- [ ] `ClaudeMessagesTransport` 클래스: codex의 `CodexNativeTransport`와 동일한 생성자 시그니처(`access_token_provider`, `sse_client`(주입 가능), `base_url`)를 갖되 WebSocket 분기는 없음(Claude Messages는 SSE만 지원, `force_sse`/`websocket_client` 파라미터 자체를 만들지 않는다 — codex 대비 단순화).
- [ ] `tests/test_claude_transport.py`: `_tools_to_claude_schema()` 단위 테스트(7개 도구 스키마 전체가 `input_schema` 키로 정확히 변환됨), `build_claude_transport_request()`의 system 분리·tool_use/tool_result round-trip 테스트, `map_claude_frame()`의 각 프레임 타입별 단위 테스트(특히 텍스트+tool_use가 인터리브된 멀티블록 시퀀스를 fake SSE로 그대로 재생해 올바른 순서의 `ProviderEvent` 리스트가 나오는지), 그리고 `error` 프레임의 두 가지 바디(단순 401 vs 정책 차단 패턴)로 `code`가 각각 다르게 나오는지 확인하는 테스트.

Run: `uv run pytest -q tests/test_claude_transport.py && uv run pytest -q tests/test_codex_transport.py`
Expected: `test_claude_transport.py` 전체 PASS(멀티블록 인터리브 시퀀스 테스트 포함). `test_codex_transport.py`도 기존과 동일하게 전부 PASS해 `agentos/llm/transports/base.py` 공유 파일 변경이 codex 계약을 깨지 않았음을 이 Task 시점에 바로 확인한다(principle-auditor 지적 반영 — Milestone 5까지 기다리지 않음).

### Task 3: `ClaudeNativeProvider` 구현 및 registry 등록

**파일:**
- 신규: `agentos/llm/providers/claude_native.py`
- 수정: `agentos/llm/registry.py`
- 신규: `tests/test_claude_provider.py`
- 수정: `tests/test_llm_core.py`(provider 목록 회귀)

- [ ] `ClaudeNativeProvider`를 `codex_native.py`의 `CodexNativeProvider`와 동일한 구조로 작성한다. `name = "claude"`, `mode = "account-login"`.
- [ ] `capabilities()` → `ProviderCapabilities(context_aware=True, supports_continuation=False)`(codex는 `supports_continuation=True`인 반면, Claude는 서버 측 연속 개념이 없어 매 턴 전체 replay이므로 `False` — 이 차이를 코드 주석 없이 이 계획 문서에만 남긴다).
- [ ] **사용자 대면 문구 확정(usability-reviewer 지적 반영, codex와 대칭):**
  - 미인증 상태: `"AgentOS-owned Claude sign-in is required."`
  - 로그인 완료: `"Claude sign-in completed."`
  - 표준 recovery 문구: `RECOVERY_LOGIN = "Run: agentos llm login --provider claude"`
  - 정책 차단 추정 실패 시(Task 2에서 넘어온 `error.code == "claude_integration_blocked"`): 메시지 `"Claude 로그인 연동이 Anthropic 정책 변경으로 차단되었을 수 있습니다(알려진 리스크). 재로그인으로 해결되지 않으면 AgentOS 업데이트를 확인하세요."`, recovery `"This is a documented policy risk, not a bug you caused. Check for an AgentOS update if re-login does not resolve it."` — 일반 `token_expired` 실패의 recovery(`RECOVERY_LOGIN`)와 다른 문자열임을 테스트로 고정한다.
- [ ] `login()`/`login_updates()`: codex의 `_login_steps()` 제너레이터 패턴을 그대로 따르되, Task 1의 `prepare_browser_login()`/`complete_browser_login()`(브라우저 우선, 실패 시 별도 폴백 없음 — **Claude는 codex처럼 디바이스 코드 폴백이 없다**, Anthropic이 디바이스 코드 grant를 공개 제공하지 않으므로 브라우저 로그인 실패 시 바로 `BrowserLaunchFailedError`를 사용자에게 보여주고 종료한다. 이 차이를 이 Step에 명시).
- [ ] `logout()`: Task 1의 `logout(store)` 호출.
- [ ] `stream_once()`/`stream_context()`: codex와 동일 구조로 `_authenticated_credentials()` → `Task 2의 ClaudeMessagesTransport` → `_to_llm_event()`.
- [ ] `_to_llm_event()`에서 `ProviderEvent.error`의 `code`가 `claude_integration_blocked`이면 위에서 확정한 정책 차단 문구로, 그 외에는 일반 `token_expired`/기존 codex 스타일 메시지로 `LLMEvent(error=..., recovery=...)`를 만든다.
- [ ] `agentos/llm/registry.py`의 `build_default_registry()`에 `from agentos.llm.providers.claude_native import ClaudeNativeProvider`와 `registry.register("claude", ClaudeNativeProvider)`를 추가한다.
- [ ] `tests/test_claude_provider.py`: `status()`/`login()`/`logout()`/`capabilities()`의 각 상태 전이, 정책 차단 vs 일반 만료의 서로 다른 에러 문구가 실제로 다르게 나오는 fake transport 테스트, `stream_once`/`stream_context`가 `LLMEvent` 정규 이벤트를 만드는지 확인.
- [ ] `tests/test_llm_core.py`에 `supported_providers()`가 `"claude"`를 포함하는지 확인하는 단정 1건을 추가한다(기존 `"codex"`/`"codex-cli"`/`"mock"` 단정 옆에).

Run: `uv run pytest -q tests/test_claude_provider.py tests/test_llm_core.py`
Expected: 전체 PASS. `supported_providers()`가 `("claude", "codex", "codex-cli", "mock")`(정렬 순서는 `tuple(sorted(...))`이므로 알파벳순)를 반환하고, 정책 차단 에러와 일반 만료 에러가 서로 다른 `recovery` 문자열을 갖는 것을 명시적으로 단정한다.

### Task 4: CLI/TUI 배선

**파일:**
- 수정: `agentos/terminal/interaction.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정: `tests/test_interactive_cli.py`
- 수정: `tests/test_tui_cli.py`

- [ ] `agentos/terminal/interaction.py`의 `if provider in ("codex", "codex-cli"):` 분기(42행)에 `"claude"`를 추가할지, 아니면 provider별 기본 모델을 딕셔너리로 일반화할지는 실제 이 분기가 하는 일(`_default_model_for_provider`류 로직인지 확인 필요 — 구현 시점에 실제 라인을 다시 읽고 최소 변경으로 처리한다: 이미 `"claude"`용 별도 상수가 필요하면 `CLAUDE_DEFAULT_MODEL = "claude-sonnet-5"`를 추가).
- [ ] `agentos/terminal/tui/app.py`의 `_default_model_for_provider()`(81-84행)에 `if provider == "claude": return CLAUDE_DEFAULT_MODEL` 분기를 추가한다.
- [ ] `agentos/terminal/tui/app.py`의 `_AVAILABLE_PROVIDERS = ("mock", "codex")`(582행)에 `"claude"`를 추가해 `("mock", "codex", "claude")`로 만든다.
- [ ] `SHELL_LOGIN_RECOVERY_TEXT`(74-78행)와 유사하게 Claude용 recovery 텍스트가 필요한 화면(있다면)에도 Task 3에서 확정한 문구를 그대로 사용한다(문구를 새로 짓지 않는다).
- [ ] `tests/test_interactive_cli.py`/`tests/test_tui_cli.py`에 provider `claude` 선택 시 `_default_model_for_provider("claude")`가 올바른 기본 모델을 반환하는지, `_AVAILABLE_PROVIDERS`에 `"claude"`가 포함되는지, TUI provider 메뉴에 `claude` 옵션이 노출되는지 확인하는 테스트를 추가한다.

Run: `uv run pytest -q tests/test_interactive_cli.py tests/test_tui_cli.py -k claude`
Expected: 신규 테스트 전체 PASS.

### Task 5: 문서 반영 및 전체 회귀

**파일:**
- 수정: `docs/cli-reference.md`

- [ ] `docs/cli-reference.md`에 기존 codex provider 절과 대칭되는 `claude` provider 절을 추가한다. **완료 기준(usability-reviewer 지적 반영, 이 항목이 실제로 문서에 없으면 Task 5는 미완료로 간주한다):**
  - `agentos llm login --provider claude`/`agentos run --provider claude` 사용법.
  - **다음 문장을 반드시 포함한다**: "이 통합은 Anthropic이 공식 지원을 문서화한 대상이 아니며, Anthropic이 예고 없이 이 로그인 방식을 차단할 수 있습니다. 이 경우 재로그인으로 해결되지 않으면 AgentOS 업데이트를 확인하세요." (기존 codex 절의 "AgentOS owns native Codex auth/transport"류 신뢰 문구와 같은 톤으로 시작하지 않도록 — 이 절은 처음부터 정책 리스크를 명시하고 시작한다).
  - Task 3에서 확정한 두 에러 문구(일반 만료/정책 차단)가 실제로 사용자가 보게 될 메시지임을 설명.
- [ ] 전체 스위트와 공백 오류 검사를 fresh run한다.

Run: `uv run pytest -q && git diff --check`
Expected: 전체 테스트 통과(회귀 없음), `git diff --check` 출력 없음 및 exit 0. `grep -q "예고 없이" docs/cli-reference.md`로 정책 리스크 문구가 실제로 문서에 존재하는지 확인(문서 내용 자체를 완료 기준으로 검증 — usability-reviewer 지적 반영).

## 범위와 비목표

- 포함: `claude` OAuth native provider(auth/transport/provider 3계층), tool 스키마 변환, CLI/TUI 배선, 문서, 정책 차단과 일반 인증 만료를 구분하는 에러 처리.
- 제외: `claude-cli`(외부 CLI 프로세스 위임 — 사용자가 명시적으로 범위 제외 결정), API 키 인증, Vertex AI/Bedrock 경유 Claude, 이미지/파일 업로드 입력, 디바이스 코드 로그인 폴백(Anthropic이 공개 제공하지 않음), WebSocket transport(Claude Messages는 SSE만 지원).

## 리뷰 반영 이력
- 초안 작성 시 사용자와 두 가지 설계 결정을 확정: (1) provider CLI 이름은 `claude`, `claude-cli`(외부 프로세스 위임) 보조 경로는 이번 범위에서 제외. (2) OAuth client_id/엔드포인트는 `pi`가 쓰는 Anthropic 공식 Claude Code CLI용 공개 client_id를 그대로 재사용하고, Claude Code로 위장하는 인증 헤더 방식도 동일하게 채택 — 이 판단의 근거와 리스크를 "위임 방식과 리스크" 절에 기록.
- **1차 Gate 2 리뷰(plan-reviewer/principle-auditor/usability-reviewer) 결과: 3종 모두 FAIL.**
  - `plan-reviewer` FAIL 사유: `## 구현 단계`(Task/Step 상세 체크리스트) 섹션 전체 누락(마일스톤 표만으로는 구현자가 즉시 착수 불가), `의존성 게이트` 형식(`name`/`type`/`required`/`preflight`/`fallback`/`failure_behavior`) 미비, preflight 검증 부재, redaction 검증 구체성 부족.
  - `principle-auditor` FAIL/BLOCK 사유: 위 구조적 결함에 더해 (a) `ProviderEvent`가 Claude의 멀티블록 인터리브 스트리밍(text+tool_use)을 표현할 수 있는지 아키텍처 결정 미비, (b) 공유 파일(`transports/base.py`) 변경에 대한 격리된 회귀 게이트 부재(Milestone 5까지 기다림), (c) "Anthropic이 위장 패턴을 차단"이라는 리스크를 문서화했지만 그 리스크가 실현됐을 때 런타임에서 구분 가능한 신호(에러 코드/메시지)로 연결하지 않음.
  - `usability-reviewer` FAIL 사유: (a) 실제 로그인 성공/실패/미인증 사용자 문구가 계획에 확정되지 않아 구현자가 임의로 지음, (b) **Anthropic의 정책 차단과 일반 인증 만료를 구분하는 사용자 대면 에러 메시지·복구 안내가 계획에 없음**(가장 심각한 지적 — 위임 방식과 리스크를 사용자에게 승인받은 것과, 그 리스크가 실제로 발생했을 때 사용자가 이해 가능한 신호를 받는 것은 별개), (c) `docs/cli-reference.md` 업데이트의 완료 기준이 테스트 PASS일 뿐 문서 콘텐츠(정책 리스크 공개) 자체를 검증하지 않음.
- **2차 개정:** 위 3종 리뷰의 모든 지적을 다음과 같이 반영했다 — `## 구현 단계`(Task 1-5) 신설, `의존성 게이트` 표 추가(preflight `Run:`/`Expected:` 포함), 아키텍처 절에 `ProviderEvent` 멀티블록 표현 방식과 공유 파일 격리 회귀(Task 2 시점 `test_codex_transport.py` 동시 실행) 확정, "위임 방식과 리스크" 절에 정책 차단 vs 일반 만료를 구분하는 에러 코드(`claude_integration_blocked`/`token_expired`)와 정확한 사용자 문구 확정(Task 3), Task 5 완료 기준에 문서 콘텐츠 자체(정책 리스크 공개 문장) 검증 추가.
- **2차 Gate 2 리뷰 결과: `plan-reviewer` PASS, `usability-reviewer` PASS, `principle-auditor` FAIL/REVISE.** `principle-auditor`의 유일한 잔여 지적: (a) Task 1의 `classify_auth_failure()` 판별 규칙 자체를 "Task 3에서 확정한다"고 미루고 있어 Gate 2가 아직 존재하지 않는 로직을 승인하는 셈이었고, (b) "반복적으로 같은 코드로 거부되는 경우"라는 다중 요청 상태 기반 휴리스틱이 계획에 예산(상태 저장 위치·리셋 시점)이 전혀 없이 단일 프레임 테스트 서술과 모순되게 공존하고 있었다.
- **3차 개정(현재 버전):** `classify_auth_failure(error_type, status_code)`의 판별 규칙을 이 계획 문서 자체에서 지금 확정했다 — `status_code in (401,403)`이고 `error_type == "authentication_error"`면 `token_expired`, 그 외 401/403은 전부 보수적으로 `claude_integration_blocked`. 다중 요청 반복 패턴 휴리스틱은 완전히 제거했다(상태 추적 예산이 없었고 단일 프레임 테스트와 모순되었기 때문). 이 규칙은 단일 에러 응답 하나만으로 결정되므로 Task 1에서 세 가지 입력 조합(`("authentication_error",401)`/`(None,401)`/`("some_other_type",403)`) 단위 테스트로 그 자리에서 완결하고, Task 2/3은 이 함수를 호출·전달만 한다.
- 3차 Gate 2 리뷰 재실행 필요(아래 진행 스냅샷 참고).

## 구현 결과

- **Task 1** — `agentos/llm/auth/anthropic_claude.py`(신규): `openai_codex.py`의 PKCE/HTTP transport/예외 계층(`AuthError`, `BrowserLaunchFailedError`, `StateMismatchError`, `CallbackTimeoutError`)과 콜백 서버 헬퍼(`_CallbackResult`, `_make_callback_handler`, `_find_free_port`)를 import해 재사용하고, Claude 전용 OAuth 상수(`CLIENT_ID`, `SCOPES`, authorize/token URL, 콜백 포트 53692/53693)와 브라우저 로그인/토큰 교환/갱신/상태 조회/로그아웃 함수를 작성했다. `classify_auth_failure(error_type, status_code)`는 계획에서 확정한 두 갈래 규칙(단일 에러 프레임만으로 판별, 다중 요청 상태 없음) 그대로 구현했다.
- **Task 2** — `agentos/llm/transports/base.py`에 `build_claude_transport_request()`를 기존 `build_transport_request()` 옆에 추가(기존 함수·codex 계약은 무변경). `agentos/llm/transports/anthropic_messages.py`(신규): `_tools_to_claude_schema()`(OpenAI `parameters` → Claude `input_schema` 키 변환), `_BlockState`(인덱스별 블록 상태를 transport 내부에만 격리해 `ProviderEvent` 공유 dataclass는 무필드 변경), `map_claude_frame()`(Claude SSE 이벤트 8종 매핑, 에러 프레임에서 `classify_auth_failure()` 적용), `ClaudeMessagesTransport`(SSE 전용, WebSocket 분기 없음 — Claude Messages가 지원하지 않으므로 codex 대비 단순화).
- **Task 3** — `agentos/llm/providers/claude_native.py`(신규): `CodexNativeProvider`와 동일한 구조의 `ClaudeNativeProvider`(`status`/`login`/`login_updates`/`logout`/`stream_once`/`stream_context`/`capabilities`). `capabilities()`는 `supports_continuation=False`로 선언(Claude Messages는 서버 측 연속 개념이 없음). 계획에서 확정한 4개 사용자 문구(미인증/로그인완료/표준 recovery/정책차단 recovery)를 그대로 구현했고, `_to_llm_event()`에서 `claude_integration_blocked`와 `token_expired`를 서로 다른 메시지·recovery로 분기한다. `agentos/llm/registry.py`의 `build_default_registry()`에 `registry.register("claude", ClaudeNativeProvider)`를 추가했다.
- **Task 4** — `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py`의 `_default_model_for_provider()`에 `"claude"` 분기(`claude-sonnet-5` 반환)를 추가하고, `AgentOSTui._AVAILABLE_PROVIDERS`에 `"claude"`를 추가해 `/model claude`로 전환 가능하게 했다. `/login`·`/logout`·`/status` 슬래시 명령은 계획 범위대로 codex 전용 동작을 그대로 유지했다(범위 밖으로 명시됨 — 기존 동작 불변경).
- **Task 5** — `docs/cli-reference.md`에 `## Native Claude Sign-In (--provider claude)` 절을 추가해 로그인 절차, 두 가지 에러 메시지(일반 만료/정책 차단)와 각각의 대응, 그리고 계획에서 요구한 정책 리스크 공개 문장("이 통합은 Anthropic이 공식 지원을 문서화한 대상이 아니며, Anthropic이 예고 없이 이 로그인 방식을 차단할 수 있습니다")을 명시했다. Provider 목록이 나오는 두 곳(`agentos run --provider`, `agentos llm status|login|logout --provider`)에도 `claude`를 추가했다.

## 사용 방법

1. `agentos llm login --provider claude`로 브라우저 로그인을 완료한다(Claude Pro/Max 구독 계정 필요).
2. `agentos llm status --provider claude --json`으로 `authenticated: true`를 확인한다.
3. `agentos run --provider claude "..."` 또는 TUI에서 `/model claude`로 전환해 Claude와 대화한다. read/list/glob/grep/write/edit/bash 7개 도구가 기존과 동일한 승인 정책으로 그대로 동작한다.
4. `agentos llm logout --provider claude`로 로그아웃한다.

## 완료 증거

- `Run:` `uv run pytest -q tests/test_claude_oauth.py` → `Expected:` PASS / **실제:** `19 passed`
- `Run:` `uv run pytest -q tests/test_claude_transport.py && uv run pytest -q tests/test_codex_transport.py` → `Expected:` 둘 다 PASS(공유 파일 회귀 없음) / **실제:** `27 passed`, `46 passed`
- `Run:` `uv run pytest -q tests/test_claude_provider.py tests/test_llm_core.py` → `Expected:` PASS / **실제:** `32 passed`
- `Run:` `uv run pytest -q tests/test_interactive_cli.py tests/test_tui_cli.py -k claude` → `Expected:` PASS / **실제:** `4 passed`
- `Run:` `uv run pytest -q` (전체 스위트) → `Expected:` 전체 PASS, 회귀 없음 / **실제:** `496 passed`
- `Run:` `git diff --check` → `Expected:` 출력 없음, exit 0 / **실제:** exit 0, 출력 없음
- `Run:` `grep -q "예고 없이" docs/cli-reference.md` → `Expected:` 매치(정책 리스크 문구가 실제 문서에 존재) / **실제:** 매치 확인됨

**자동화 불가 영역(계획에 명시된 대로):** 실제 Anthropic 계정으로 브라우저 로그인을 완료하고 실제 Claude 응답을 받는 end-to-end 검증은 사용자의 Claude Pro/Max 구독 계정이 필요해 이 세션에서 수행할 수 없다. 모든 위 검증은 fake transport/fake HTTP client로 수행되었다.

## 아카이브 결정

구현·전체 회귀·Gate 2 리뷰(3차, 전원 PASS)를 모두 완료했다. 단, 실제 브라우저 로그인으로 사용자가 최종 확인하기 전까지는 active plan으로 유지하며, 사용자가 명시적으로 archive를 요청할 때만 archive로 이동한다.
