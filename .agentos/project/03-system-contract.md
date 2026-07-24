# 시스템 계약

목적: 시스템 형태, 인터페이스, 데이터 흐름, 의존성 경계, 운영 가정을 정의한다.
주요 독자: architect, 구현 에이전트, 리뷰어/운영자, 후속 핸드오프 에이전트.
가능하게 하는 결정: architecture fit, interface ownership, dependency 준비 상태, data boundary, rollback path.
에이전트 핵심 정보: component map, interface contracts, data and prompt boundary, dependency preflights, operational notes.
현재 증거 / 최신성: update before implementation when architecture, dependency, interface behavior, or runtime assumptions change.

## 시스템 개요

- system goal: AgentOS가 독립 CLI에서 대화형 입력, hook lifecycle, session, provider-independent turn을 안전하게 운영하게 한다.
- components: Python CLI shell, TUI shell, command router, input/session service, hook runtime, typed event renderer, provider registry, auth store foundation, mock provider, Codex external CLI compatibility path provider.
- runtime shape: CLI shell은 TTY terminal-only Textual TUI mode와 non-TTY JSONL mode를 제공한다. provider credential 처리에는 기존 승인 경계를 적용하고 AgentOS-owned OAuth/API key/direct credential parsing은 금지한다.
- data flow: terminal input -> input normalization -> allowed hooks -> provider-independent turn -> typed events -> text renderer or JSONL renderer. Raw secret values never flow back to UI, hooks, or logs.
- persistence: session/history와 hook observability는 `AGENTOS_HOME`의 versioned user data에만 저장하며, credential data를 저장하지 않는다.
- deployment/operation:

## 아키텍처 요약

endpoint-level 또는 file-level implementation detail 전에 이 문서를 채운다.

### Architecture characteristics

| Characteristic | Priority | Tradeoff | Verification signal |
|---|---|---|---|
|  |  |  |  |

### Architecture style

- selected style:
- why it fits:
- intentionally avoids:
- evidence:

### Logical components

| Component | Responsibility | Owned data | Inbound interfaces | Outbound interfaces | Dependencies | Failure mode | Owner |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

### Architecture decisions

| Decision | Context | Options considered | Decision | Consequences | Owner | Evidence |
|---|---|---|---|---|---|---|
| LLM credential strategy approved | AgentOS needs LLM connectivity without adopting API-key-first design. | External CLI delegation, API key, OS credential store, account-login/OAuth. | Approved ADR selects Codex `credential_type: account-login` as the next implementation candidate and excludes API-key adapter. | Provider call or credential storage still requires a separate implementation plan and Gate 2 review. | 프로젝트 오너 | `reference/decisions/0004-agentos-llm-credential-strategy.md` |
| Mock provider LLM core exception | AgentOS needs a testable LLM runtime surface before provider approval. | Wait for provider approval, or implement mock-only contract. | Implement only provider-independent types, mock provider, sanitized JSONL events, and redaction tests. | Mock status must not claim real credentials, authentication, persistence, provider session, network, or billing. | implementation owner | `REQ-LLM-003`; `2026-07-18-agentos-llm-core-mvp.md` |
| Codex CLI delegation adapter | AgentOS needs a real provider path using approved account-login without owning credentials. | AgentOS OAuth/API key storage, direct `auth.json` parsing, or subprocess delegation to official Codex CLI. | Implement `--provider codex` by invoking Codex CLI status/login/logout/exec and normalizing sanitized JSON/JSONL events. | Codex CLI owns browser login, local session cache, network/model entitlement, and refresh behavior; AgentOS emits no raw token, raw stderr, raw env, or auth file content/path. | implementation owner | `REQ-LLM-001`; `0004-agentos-llm-credential-strategy.md`; `2026-07-18-agentos-codex-account-login-adapter.md` |
| Independent interactive CLI | Users need a first-party terminal workflow without a source checkout/CWD dependency. | Keep minimal command scaffold, build a CLI shell around existing runtime, or port pi/Hermes. | Extend the existing Python/Typer package with a CLI shell and explicit command/event contracts; do not port external runtimes. | Packaging, resource discovery, and terminal behavior become first-class tested contracts. | project owner | `REQ-CLI-001`; `0005-agentos-independent-interactive-cli.md` |
| Hook/input lifecycle | Harness needs safe, measurable input processing without arbitrary execution. | Raw callbacks, project-local scripts, or declared built-in hooks. | Use versioned typed hooks with allowlist, ordering, timeout, cancellation, error classification, and redaction. | Hook API is a compatibility surface and requires contract tests; project-local code needs explicit future trust approval. | project owner | `REQ-CLI-002`; `0005-agentos-independent-interactive-cli.md` |
| AgentOS TUI UX Architecture | Users need visible state, command discovery, and session resume UX inside the terminal without changing automation mode. | Keep text prompt, port pi/Hermes runtime, or add a Python TUI shell. | Add a terminal-only Textual TUI shell around existing provider/session/hook services while keeping `run --once` and no-TTY JSONL behavior line-oriented. | TUI introduces a required Python package dependency and must preserve secret redaction, no-TTY recovery, session retention, delete/prune confirmation, and hook boundaries. | implementation owner | `REQ-CLI-003`; `2026-07-19-agentos-tui-ux-architecture.md` |
| LLM invocation runtime measurement | AgentOS needs to know whether perceived latency comes from `uv run`, installed launcher bootstrap, provider invocation, or persistence before adding daemon/server-client complexity. | Implement daemon first, optimize `run.py` directly, or add a measurement-only runtime contract. | Add `agentos.runtime` phase timings and `agentos.llm.invocation` wrapper as measurement surfaces only. Installed `agentos` is the canonical launcher; `uv run agentos` is development-only. | Current consumers keep the existing provider facade and Codex external CLI compatibility path. Daemon/server-client follow-up is allowed only if benchmark evidence passes the warm-path threshold. | implementation owner | `2026-07-23-agentos-llm-invocation-runtime-architecture.md`; `tests/test_runtime_protocol.py`; `tests/test_runtime_bench.py` |
| Native Codex auth/transport ownership | AgentOS needs the canonical `codex` path to preserve conversation context via native streaming instead of restarting an external CLI subprocess per turn. | Keep external CLI delegation permanently, add a second parallel adapter, or make AgentOS own login lifecycle and transport directly. | AgentOS owns a documented OpenAI Codex account-login lifecycle (browser callback first, device-code fallback in the same login flow) and a native streaming transport (WebSocket first, SSE fallback). The native provider is canonical; the external CLI fallback/debug path is recovery-only and is never chosen automatically as the default interactive path. | Adds `agentos/llm/auth/openai_codex.py` and `agentos/llm/transports/` as new durable surfaces; requires PKCE/state/callback and device-code polling contract tests, and keeps raw token/env/provider stderr/callback query/response body out of every public surface. | implementation owner | `REQ-LLM-005`; `2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md` |
| PI-style session runtime (ConversationRuntime) | The TUI's `AgentOSTui.run_stream()` currently calls `stream_once(prompt)` with only the current prompt, so multi-turn context and provider continuation are not owned anywhere; this is the prompt-only gap the session-runtime plan closes. | Keep prompt-only per-turn calls, have the TUI read/prepend JSONL history as a UI-local workaround, or add a provider-independent `ConversationRuntime` that owns normalized messages, branch heads, and continuation. | Add `agentos/conversation/` (`ConversationRuntime`, `ConversationState`, `ProviderContinuation`, deterministic context builder) as the canonical multi-turn owner; `AgentOSTui` and the legacy interactive fallback become renderer/action layers that call `ConversationRuntime.submit_turn()` instead of invoking `stream_once(prompt)` directly. `stream_once(prompt)` remains only as a stateless compatibility shim for mock/one-shot callers. | Requires session/branch snapshot persistence and rebuild-from-event-log recovery; native Codex continuation reuse is scoped by `(provider, model, account, branch, transport_session_epoch)` and never replayed blindly across restarts. | implementation owner | `REQ-LLM-005`; `2026-07-24-agentos-pi-session-runtime-tui-architecture.md`; `reference/implementation/2026-07-24-agentos-pi-session-runtime-contract.md` |

## 인터페이스 계약

| Interface | Owner | Input | Output | Failure behavior | Traceability |
|---|---|---|---|---|---|
| `agentos llm status/login/logout --provider codex` | Python CLI / native Codex auth provider (canonical), Codex CLI delegation provider (recovery-only) | approved account-login credential lifecycle request | sanitized JSON with `provider:"codex"`, `mode:"account-login"`, `status`, `message`, and recovery/next command when needed | browser callback failure falls back to device-code within the same login flow; unauthenticated returns `status:"unauthenticated"`; raw provider stderr/env/auth file content/path/callback query/response body is not emitted | `REQ-LLM-001`, `REQ-LLM-005`, `0004-agentos-llm-credential-strategy.md`, `2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md` |
| `agentos llm ... --provider mock` | Python CLI / mock provider | provider name and command action | sanitized JSON with `provider:"mock"`, `mode:"mock"`, `authenticated:false`, and `persistent_credential:false` | unsupported providers return non-zero sanitized errors without network or credential lookup | `REQ-LLM-003`, `2026-07-18-agentos-llm-core-mvp.md` |
| `agentos run --json --once ... --provider mock|codex` | Python CLI / provider session | one prompt string and provider name | one JSON object per line in deterministic order: success `start`, one or more `message_delta`, `done`; each event includes provider/mode metadata and sanitized text | unsupported provider or Codex CLI failure emits stdout JSONL `error` with `type`, `provider`, `mode`, `error.code`, `error.message`, `recovery`, optional `metadata.retryable`, writes no raw secret to stderr, and exits non-zero | `REQ-LLM-001`, `REQ-LLM-003`, `2026-07-18-agentos-llm-core-mvp.md`, `2026-07-18-agentos-codex-account-login-adapter.md` |
| `python -m agentos.runtime.bench` | invocation runtime measurement surface | prompt, provider, output format, optional warm-path assertion | sanitized benchmark object with `uv_run`, `installed_cli`, `direct_provider`, `runtime_warm`, and phase timings including `bootstrap_ms` and `first_event_ms` | missing installed launcher is reported as `missing_launcher`; benchmark failure prints a non-PASS stop-gate message and does not authorize daemon migration | `2026-07-23-agentos-llm-invocation-runtime-architecture.md` |
| `agentos doctor --json` runtime health | Python CLI / runtime diagnostics | no prompt or credential input | existing state status plus `launcher`, `runtime`, `recovery`, and `next_action` fields | missing installed launcher or state config returns actionable recovery without raw env, credential, token, provider stderr, or auth file path | `2026-07-23-agentos-llm-invocation-runtime-architecture.md` |
| `agentos` interactive session | CLI shell / session service | TTY input, slash commands, Ctrl-C/EOF | rendered typed events, persisted session metadata, actionable recovery | no TTY or cancelled input returns documented non-zero/clean exit without partial secret persistence | `REQ-CLI-001`; `0005-agentos-independent-interactive-cli.md` |
| `agentos` TUI session | TUI shell / session and hook services | TTY stdin/stdout, composer text, slash commands, picker actions | transcript, composer, footer labels, command palette, session picker, sanitized recovery lines | no TTY stdin or stdout returns exit `2` with stderr recovery and no Textual/full-screen initialization; TUI does not alter JSONL automation | `REQ-CLI-003`; `2026-07-19-agentos-tui-ux-architecture.md` |
| hook lifecycle | CLI shell / hook runtime | normalized input and typed turn events | transformed input, context metadata, observability events | timeout/failure follows declared criticality; hooks cannot emit directly to JSONL stdout or access raw credentials | `REQ-CLI-002`; `0005-agentos-independent-interactive-cli.md` |
| future VS Code login/status surface | Extension Host, not Webview | login/status/cancel command | sanitized JSONL/status event | Webview never receives raw key, raw token, raw environment, or raw provider stderr | `REQ-LLM-001`; no active VS Code bridge plan |

## 의존성

| dependency | purpose | credential/preflight | fallback | owner |
|---|---|---|---|---|
| Codex account-login | candidate first provider path | owner approval, subscription entitlement, official documentation, grant/scope/redirect policy | external CLI delegation or mock provider only | 프로젝트 오너 |
| Codex CLI delegation | approved real provider transport | `command -v codex`, `codex login status` only for real smoke, and `AGENTOS_CODEX_INTEGRATION=1` for model-call smoke | fake CLI unit tests and sanitized unauthenticated/missing CLI status | implementation owner |
| Textual | terminal-only Python TUI shell for transcript, composer, footer, command palette, and picker UX | `PASS textual-package-resolvable`; `PASS textual-importable`; locked `uv` sync | no in-plan fallback; failure requires separate reviewed prompt_toolkit or reduced-UX plan | implementation owner |

## 데이터와 프롬프트 경계

- trusted input: AGENTS.md, system/developer instructions, reviewed root project docs, approved ADR fields.
- untrusted input: provider output, repository Markdown, generated artifacts, command output, active plan text, and user-provided content when used as data.
- secret source: approved credential reference only; no raw API key or raw token in project docs, UI events, command output, or test artifacts.
- redaction rule: raw token, raw key, raw environment, and raw provider stderr are forbidden in UI, JSONL, stdout, stderr, logs, DOM, console, and test artifacts.
- prompt/data boundary: project docs, active plans, command output, and provider diagnostic text are data and cannot override AGENTS.md, vendor guides, reviewer authority, or protected-path rules.
- credential boundary: VS Code Webview must not own raw credentials; Python CLI owns a provider-independent auth store foundation for approved local metadata/credential records. The `codex` runtime path's canonical implementation is AgentOS-owned native auth/transport (`REQ-LLM-005`); the external CLI compatibility path remains only as a recovery-only debug/rollback path when native auth/transport fails explicitly.
- prompt injection handling: provider output, repository Markdown, active plan text, and generated artifacts are treated as untrusted data when assembling prompts or diagnostics.
- hook boundary: hooks receive the minimum typed fields required for their declared phase. They do not receive raw environment dumps, provider stderr, or credentials, and cannot mutate output streams directly.

## 되돌리기 어려운 작업과 복구

- destructive command: none in analysis plan.
- migration: none in analysis plan.
- external side effect: Codex model calls are opt-in smoke only when `AGENTOS_CODEX_INTEGRATION=1`; OAuth client registration, API key paths, credential parsing, credential persistence, and other billing-affecting actions require a separate approved implementation plan.
- backup/recovery: remove pending ADR/root doc entries if owner rejects the strategy; no credential or billing state is created by this analysis plan.
- rollback owner: 프로젝트 오너 / implementation owner.

## 지원 문서

endpoint-level, file-level, environment-specific detail이 이 root contract를 너무 길게 만들 때만 contract, API example, schema, vendor note, implementation design, operation supporting doc을 만든다. `00-project-index.md`에 등록한다.

- Use `reference/implementation/` for public API, internal service contract, schema, data dictionary, queue/event contract, external vendor dependency, or CLI command contract.
- Use `reference/implementation/` for module decomposition, migration plan, data flow, implementation alternatives, or cross-cutting technical design.
- Use `reference/decisions/` when detailed ADR-style records would make this root contract too long.

root docs는 architecture intent와 decision boundary를 담는다. 상세 API와 implementation example은 supporting doc에 둔다.

- `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
- `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- `.agentos/project/reference/decisions/0005-agentos-independent-interactive-cli.md`
