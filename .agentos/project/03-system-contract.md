# 시스템 계약

목적: 시스템 형태, 인터페이스, 데이터 흐름, 의존성 경계, 운영 가정을 정의한다.
주요 독자: architect, 구현 에이전트, 리뷰어/운영자, 후속 핸드오프 에이전트.
가능하게 하는 결정: architecture fit, interface ownership, dependency 준비 상태, data boundary, rollback path.
에이전트 핵심 정보: component map, interface contracts, data and prompt boundary, dependency preflights, operational notes.
현재 증거 / 최신성: update before implementation when architecture, dependency, interface behavior, or runtime assumptions change.

## 시스템 개요

- system goal: AgentOS는 vendor-neutral project work harness다. control plane은 Work Contract, Context Compiler, lifecycle/evidence ledger, Verification Runner, vendor adapter 상태를 소유하고, vendor execution plane(Codex·Claude·OpenCode 등)은 실제 대화, tool loop, provider session, 사용량, 모델/플러그인 기능을 소유한다. 두 plane 사이에는 optional structured bridge만 존재하며 안정된 machine-readable interface가 있을 때만 최소 실행 이벤트를 제공한다. 기존 독립 CLI(대화형 입력, hook lifecycle, session, provider-independent turn)는 이 control plane의 구현 표면으로 유지된다.
- 사용자 기본 여정: AgentOS에서 작업 계약 확인 → 원본 vendor CLI에서 handoff bundle로 작업 수행 → AgentOS에 declared verification 결과 기록. handoff bundle은 사용자가 원본 vendor CLI에서 수행할 작업의 승인된 최소 문맥 묶음이다.
- components: Python CLI shell, TUI shell, command router, input/session service, hook runtime, typed event renderer, provider registry, auth store foundation, mock provider, Codex native/external CLI compatibility path provider, Gateway Core run registry/service/single-worker. control plane 구성요소(Work Contract store, Context Compiler, lifecycle/evidence ledger, Verification Runner, vendor adapter status, structured bridge)는 이 구현 표면 위에 문서 수준으로 정의된다.
- runtime shape: CLI shell은 TTY terminal-only Textual TUI mode와 non-TTY JSONL mode를 제공한다. provider credential 처리에는 기존 승인 경계를 적용하고 AgentOS-owned OAuth/API key/direct credential parsing은 금지한다. structured bridge는 vendor capability가 명시적으로 확인될 때만 선택 사항으로 추가되며, 화면 파싱이나 숨은 fallback을 두지 않는다.
- data flow: terminal input -> input normalization -> allowed hooks -> provider-independent turn -> typed events -> text renderer or JSONL renderer. Raw secret values never flow back to UI, hooks, or logs.
- persistence: session/history, hook observability, and Gateway run registry/event ledger는 `AGENTOS_HOME`의 versioned user data에만 저장하며, credential data를 저장하지 않는다. AgentOS session/evidence와 vendor session은 서로 다른 소유자로 구분한다.
- global skill/project reflection: canonical skills는 `AGENTOS_HOME/core/.agents/skills`에서만 조회한다. 핵심 harness는 그 아래 `harness/` root/child tree로 관리하고 catalog는 category·source/install path metadata만 제공한다. bootstrap이 표시한 전역 skill은 read tool로 해당 regular `SKILL.md` 파일만 읽을 수 있으며 manifest, companion file, symlink, 임의 전역 경로는 읽을 수 없다. `agentos project init`은 `.agentos/agentos-project/`에 skill snapshot과 `config.toml` digest-only reference를 명시적으로 export하며, 이 export는 bootstrap input, global install source, hook configuration source가 아니다.
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
| Vendor-neutral project work harness (control/execution split) | AgentOS product docs previously treated the native Codex runtime/TUI as the canonical default, which conflicts with the goal of tracking one project's work contract, verification, and history across multiple vendor coding-agents (Codex, Claude, OpenCode). | Keep native runtime as the single canonical path, build a full common chat runtime that duplicates every vendor CLI, or split ownership into an AgentOS control plane plus vendor execution planes with an optional structured bridge. | Adopt the control/execution/bridge split: AgentOS control plane owns Work Contract, Context Compiler, lifecycle/evidence, Verification Runner, vendor adapter status, Control TUI; vendor execution plane owns real conversation, tool loop, provider session, usage, model/plugin features; structured bridge is optional and only used with a stable machine-readable interface. Native Codex runtime/TUI is not deleted or changed, but is reclassified as a non-canonical existing/advanced path that does not expand without a separate reviewed implementation plan. `0005`는 대체되지 않는다 — 독립 CLI 결정은 control plane 구현 기반으로 유지된다. | 향후 기본 UX/투자 우선순위가 이 경계를 따른다; runtime 중단·migration·credential 정책 변경은 owner 승인과 별도 reviewed implementation plan이 필요하다. | project owner | `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md` |
| Gateway Core managed execution | Users need local queued execution, state, event replay, retry, and prune without replacing direct vendor CLIs. | External queue/broker, common chat runtime duplication, or local embedded run registry that reuses provider contracts. | Add Gateway Core as a local `AGENTOS_HOME/gateway/` run registry, service, single-worker lock, and CLI group. It reuses `RuntimeRequest`, `InvocationEvent`, provider registry, and input hooks; it does not add a network listener or alternate credential store. | ADR 0006's persistent task database exclusion is superseded only for Gateway run registry data. Direct vendor CLI and `agentos run --once` remain available. | project owner | `REQ-HARNESS-003`; `reference/decisions/0007-agentos-gateway-core.md`; `docs/gateway-core.md` |

## 인터페이스 계약

| Interface | Owner | Input | Output | Failure behavior | Traceability |
|---|---|---|---|---|---|
| `agentos llm status/login/logout --provider codex` | Python CLI / native Codex auth provider (canonical), Codex CLI delegation provider (recovery-only) | approved account-login credential lifecycle request | sanitized JSON with `provider:"codex"`, `mode:"account-login"`, `status`, `message`, and recovery/next command when needed | browser callback failure falls back to device-code within the same login flow; unauthenticated returns `status:"unauthenticated"`; raw provider stderr/env/auth file content/path/callback query/response body is not emitted | `REQ-LLM-001`, `REQ-LLM-005`, `0004-agentos-llm-credential-strategy.md`, `2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md` |
| `agentos llm ... --provider mock` | Python CLI / mock provider | provider name and command action | sanitized JSON with `provider:"mock"`, `mode:"mock"`, `authenticated:false`, and `persistent_credential:false` | unsupported providers return non-zero sanitized errors without network or credential lookup | `REQ-LLM-003`, `2026-07-18-agentos-llm-core-mvp.md` |
| `agentos run --json --once ... --provider mock|codex` | Python CLI / provider session | one prompt string and provider name | one JSON object per line in deterministic order: success `start`, one or more `message_delta`, `done`; each event includes provider/mode metadata and sanitized text | unsupported provider or Codex CLI failure emits stdout JSONL `error` with `type`, `provider`, `mode`, `error.code`, `error.message`, `recovery`, optional `metadata.retryable`, writes no raw secret to stderr, and exits non-zero | `REQ-LLM-001`, `REQ-LLM-003`, `2026-07-18-agentos-llm-core-mvp.md`, `2026-07-18-agentos-codex-account-login-adapter.md` |
| `agentos gateway submit/worker/status/events/retry/prune` | Gateway Core / Python CLI | prompt, provider, project cwd, record policy, run id | sanitized JSON objects or JSONL events with run status, event sequence, retry lineage, and prune preview/delete counts | missing provider or project marker exits 2 with recovery; second worker exits 2; running cancel and unsafe retry/prune are rejected; raw secret/provider stderr/env are not emitted | `REQ-HARNESS-003`; `reference/decisions/0007-agentos-gateway-core.md`; `docs/gateway-core.md` |
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
| SQLite | Gateway Core local run registry and event ledger | Python stdlib `sqlite3`; `PASS gateway-uv-runtime-ready`; `PASS gateway-isolated-install-ready` | no fallback for Gateway Core persistence; fail closed before implementation or startup | implementation owner |

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

## 계획 reviewer 운영 계약

- 일반 계획 리뷰는 핵심 실행 가능성·정합성·안전·범위·검증을 우선하며 cosmetic 문법·문체 지적은 blocking finding으로 만들지 않는다.
- 기본 `plan-reviewer`와 `principle-auditor`는 유지하고 user-facing 계획에만 `usability-reviewer`를 추가한다. 일반 reviewer validity는 전체 plan hash에 종속되지 않는다.
- 전체 plan hash/signature와 protected approval은 protected path와 감사 추적에만 사용하며, manifest update 전에는 승인 범위를 exact path로 검증한다.
- 계획 작성 질문으로 확정한 사용자 의도는 Intent Sheet에 고정하고, unresolved ambiguity가 있을 때만 사용자에게 재질문한다.

- `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md`
- `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md`
- `.agentos/project/reference/decisions/0005-agentos-independent-interactive-cli.md`
