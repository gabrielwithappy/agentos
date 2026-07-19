# CLI/LLM/VS Code 인증 경계 조사 노트

- Expansion Trigger: LLM 구독 account-login 채택 여부를 결정하기 전에 참조 구현의 인증, credential 보관, provider 호출 경계를 분리해 기록할 필요가 생김.
- parent root doc: `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`
- reason for creation: active plan의 Task 0 근거 고정 산출물.
- owner: project owner / implementation agent
- freshness rule: Refresh when provider authentication policy, VS Code extension source ownership, credential boundary, or LLM transport verification evidence changes.
- status: 현재
- source evidence: local reference source paths under `/home/gabriel/agent/prj-agent/agentos-workspace/references/` and current AgentOS CLI source.
- links back to: `.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md`, `03-system-contract.md`, `04-safety-risk-verification.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, reviewer authority, or human approval requirements.

## 조사 목적

AgentOS가 API key 직접 입력이 아니라 구독 account-login 기반 LLM 연결을 채택할 수 있는지 판단하기 위해, 현재 CLI scaffold와 참조 구현의 인증 경계를 비교한다. 이 문서는 구현 승인이 아니며 provider 계정, OAuth client, credential store, billing, 또는 실제 모델 호출을 생성하지 않는다.

## 현재 AgentOS 경계

- `agentos/commands/run.py`는 `Prompt.ask` 기반의 대화형 입력 scaffold만 갖고 있다.
- 현재 source checkout의 `vscode-extension-mvp/`에는 `src/agentos-runner.ts`가 없으므로 VS Code source credential ownership은 이 계획에서 구현 근거로 삼지 않는다.
- `agentos/` source에는 `AGENTOS_LLM_API_KEY` 기반 credential path가 없다.

## auth_strategy_evidence

| Evidence path | 확인한 경계 | AgentOS 적용 판단 |
|---|---|---|
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/codex/sdk/python/src/openai_codex/_login.py` | browser/device-code style login lifecycle can be separated from turn execution. | account-login adapter 검토 근거로 사용한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/codex/codex-rs/app-server/src/main.rs` | app-server/session source can keep IDE integration separate from model runtime. | VS Code path는 후속 bridge plan에서 별도 검증한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/leaked-claude-code/cli/print.ts` | structured output and diagnostic surfaces need redaction boundaries. | raw stderr/stdout forwarding 금지 근거로 사용한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/leaked-claude-code/bridge/bridgeApi.ts` | IDE bridge capability should be allowlisted. | Webview는 secret/token을 직접 보유하지 않는 원칙을 둔다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/opencodex/src/oauth/login-cli.ts` | provider login can be a CLI-owned lifecycle. | provider별 login/status/logout 명령 분리 근거로 사용한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/AionUi/packages/desktop/src/preload/main.ts` | renderer/preload/main boundary limits secret and process access. | VS Code Webview와 Extension Host 사이의 메시지 검증 근거로 사용한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/docs/01-system-architecture.md` | CLI/app layer, agent loop, AI integration layer, and TUI are separated. | AgentOS도 CLI/VS Code surface와 LLM runtime surface를 분리한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/docs/02-agent-core-design.md` | Agent loop sends messages plus tool schemas to an AIProvider and consumes streamed text/tool calls. | `agentos run --json`은 provider-independent turn contract만 소비하게 한다. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/docs/03-ai-integration-layer.md` | `pi-ai` uses provider adapters, model definitions, payload normalization, stream parsing, and auth resolution. | AgentOS first implementation should copy the shape, not the TypeScript runtime: `types`, `session`, `mock provider`, `redaction`, normalized JSONL events. |
| `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/docs/04-cli-tui-design.md` | CLI injects tools into agent core and TUI renders stream events separately. | VS Code/Webview should render sanitized events, not own provider credentials or raw provider output. |

## 결정 입력

다음 값은 이 문서에서 확정하지 않는다.

- provider
- subscription entitlement policy
- billing owner
- official provider document URL and checked date
- OAuth/device-code scope, redirect URI, refresh, revocation, and token storage owner
- allowed model policy

이 값들은 `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`에서 오너 승인 근거와 함께 기록되어야 한다.

## 보안 경계

- API key adapter, API key import, and API key storage are excluded from the proposed AgentOS path.
- UI, JSONL event, logs, stdout, stderr, DOM, console, and test artifacts must not contain raw token, raw key, raw environment, or raw provider stderr.
- Future implementation plans must use synthetic sentinel values for secret regression tests; real secrets must not be used in tests.
- Provider calls, OAuth client registration, credential persistence, and billing-affecting actions require a separate approved implementation plan.

## Pi 구조 채택 판단

Pi docs 기준으로 빠르게 채택할 부분은 provider-independent LLM interface, normalized stream event, and mock/faux provider test shape이다. 직접 가져오지 않을 부분은 TypeScript/Bun runtime, broad provider registry, model catalog, API-key-first auth resolution, and TUI implementation이다.

AgentOS의 후속 MVP는 Python/Typer 구조를 유지하면서 다음 최소 표면만 만든다.

- `agentos/llm/types.py`
- `agentos/llm/session.py`
- `agentos/llm/redaction.py`
- `agentos/llm/providers/mock.py`
- `agentos/commands/llm.py`
- focused tests for mock login/status/logout, `run --json`, normalized events, and secret redaction.
