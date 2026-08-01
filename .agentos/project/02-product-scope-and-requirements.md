# 제품 범위 및 요구사항

목적: Define user outcomes, requirement scope, acceptance, 추적성, and 비목표.
주요 독자: 프로젝트 오너, 계획 에이전트, 구현 에이전트, 리뷰어/운영자.
가능하게 하는 결정: requirement inclusion, scope-change decision, acceptance 준비 상태, supporting-doc trigger.
에이전트 핵심 정보: requirement IDs, user outcomes, acceptance criteria, 추적성, 비목표, unresolved questions.
현재 증거 / 최신성: update whenever requirement, acceptance, or user priority changes.

## 사용자 결과

- 주요 사용자: AgentOS를 처음 접하는 개발자 및 기여자, 그리고 여러 vendor coding-agent를 넘나들며 한 프로젝트를 운영하는 개발자.
- 사용자 워크플로우 (vendor-neutral project work harness): AgentOS에서 작업 계약 확인 → 원본 vendor CLI에서 handoff bundle로 작업 수행 → AgentOS에 declared verification 결과 기록. 기존 독립 CLI 워크플로우(독립 설치 -> `agentos setup` -> `agentos` 대화형 세션 또는 `agentos run --once` 자동화 -> `agentos doctor`로 복구/진단)는 이 harness 위에서 계속 제공된다.
- 원하는 결과: source checkout이나 별도 프론트엔드 없이 일관된 AgentOS command, 대화형 입력, session, hook 관리와 복구 안내를 사용한다. 동시에 Work Contract, Context Compiler, lifecycle/evidence, Verification Runner, vendor adapter 상태를 AgentOS에서 확인하고, 실제 코딩 대화와 vendor 고유 기능은 원본 vendor CLI에서 수행한다.
- 피해야 할 실패 상태: 현재 디렉터리에 따라 명령이 달라지거나, hook 실패·입력 취소·provider 오류에서 사용자가 다음 행동을 알 수 없는 상태. 또는 vendor CLI를 교체했을 때 프로젝트 작업 계약이나 완료 근거가 사라지는 상태.

## 제품 방향: vendor-neutral project work harness

- REQ-HARNESS-001 (must, 현재): AgentOS control plane은 Work Contract, Context Compiler, lifecycle/evidence ledger, Verification Runner, vendor adapter 상태, Control TUI를 소유한다. 근거: `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md`. 이 상위 requirement는 아래 REQ-HARNESS-001-a~f로 세분화되며, 각 하위 requirement는 독립적으로 계획·구현·검증한다.
- 비목표: AgentOS가 Codex·Claude·OpenCode의 실제 대화, tool loop, provider session, model/plugin 기능을 복제하는 common chat runtime을 만들지 않는다. provider credential/tool ownership은 각 vendor CLI가 소유하며 AgentOS는 이를 대신 소유하지 않는다.

### REQ-HARNESS-001 세분화

Work Contract 정의: 별도 파일/스키마/저장소를 새로 만드는 것이 아니라, 기존 `.agentos/project/exec-plans/**` 계획 포맷을 확장하는 것이다. exec-plan은 이미 목표·acceptance·Run/Expected 검증 계약을 담고 있으며, 이 계약은 "누가 실행하는가"와 독립적으로 성립한다(Run/Expected는 실행자와 무관한 검증 계약이다). REQ-HARNESS-001-a는 여기에 `execution_mode`, `executor`, `delegation` 필드를 추가해 "누가 이 작업을 실제로 구현하는가"를 명시적으로 선언하는 확장이다. `execution_mode`는 3가지 값을 가진다: `local-agent`(현재 세션이 직접 구현), `vendor-handoff`(Codex CLI/Claude Code CLI 등 외부 CLI에 사용자가 수동으로 handoff bundle을 전달), `structured-bridge`(안정된 machine-readable interface가 명시적으로 확인됐을 때만 자동 연동, `03-system-contract.md`의 optional structured bridge와 동일 개념). 프로세스 분리는 필수가 아니라 책임 분리다 — 같은 프로세스가 control plane(계약 정의)과 executor(구현) 역할을 동시에 수행해도 된다. 단, planner와 executor가 동일 프로세스/세션인 경우 그 세션이 자기 자신에게 `vendor-handoff`를 수행하는 self-handoff는 금지한다(순환적이며 무의미하다) — 이 경우 `execution_mode: local-agent`를 사용한다.

구현 순서: Work Contract(001-a)가 다른 모든 control plane 구성요소의 데이터 기반이므로 가장 먼저 계획한다. lifecycle/evidence ledger(001-b)와 vendor adapter 상태(001-e)는 Work Contract 존재를 전제하지 않고도 독립적으로 착수 가능하다. Context Compiler(001-c, `vendor-handoff`/`structured-bridge` 모드에서만 필요)와 Verification Runner(001-d)는 Work Contract의 `execution_mode`/`executor` 필드가 확정된 뒤에만 의미 있게 정의할 수 있다. Control TUI(001-f)는 나머지 구성요소의 상태를 보여주는 표면이므로 최소 하나 이상의 하위 구성요소가 구현된 뒤 착수한다.

범위 경계: REQ-HARNESS-001-a는 `writing-plans` 스킬(`.agents/skills/harness/writing-plans/**`, TEMPLATE.md 포함)의 실행 계약을 바꾸는 작업이므로, 이번 문서 전환 계획(`2026-07-26-project-work-harness-document-pivot`)과는 별도의 독립 실행 계획("writing-plans의 executor-neutral execution contract 도입" 등)에서 다룬다. `.agents/skills/**` 변경은 AGENTS.md의 구조적 변경 감지·`authorized_architects` 승인·manifest sync 규칙이 적용되며, 이 문서 전환 계획의 비목표("harness asset 구조 변경 없음")를 넘어선다. 목표는 "위임형으로 전면 교체"가 아니라 exec-plan을 실행자 중립적으로 만드는 것이다. 기존 exec-plan은 `local-agent`를 기본값으로 계속 지원한다(기존 완료 계획은 암묵적으로 모두 `local-agent`).

| ID | requirement | Priority | acceptance | 추적성 | Evidence link / 검증 근거 | status |
|---|---|---|---|---|---|---|
| REQ-HARNESS-001-a | Work Contract 필드 확장(execution_mode/executor/delegation) | must | (1) `writing-plans` 템플릿에 `execution_mode`(`local-agent`\|`vendor-handoff`\|`structured-bridge`), `executor`, handoff/evidence 반환 계약 필드가 추가됨. (2) 기본값은 `local-agent`이고 기존 직접 구현 계획과 호환됨. (3) `vendor-handoff`일 때 AgentOS가 만드는 최소 handoff bundle과 외부 실행 결과 수집 방식이 정의됨. (4) planner=executor인 세션의 self-handoff 금지 규칙이 명문화됨. (5) Gate 2, plan hash, lifecycle/closeout 증거가 실행 모드와 무관하게 유지됨이 검증됨. (6) `.agents/skills/**` 변경에 필요한 manifest sync, 리뷰, 하네스 회귀 테스트가 통과함 | `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md` | (별도 구현 계획에서 정함) | 계획 필요 |
| REQ-HARNESS-001-b | lifecycle/evidence ledger | must | 계획의 상태 전이(reviewed, 구현 시작/완료, closeout)와 검증 evidence(Run/Expected 결과)가 append-only 방식으로 기록되고 재구성 가능함이 검증됨 | `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md` | (별도 구현 계획에서 정함) | 계획 필요 |
| REQ-HARNESS-001-c | Context Compiler (`vendor-handoff`/`structured-bridge` 전용) | must | `execution_mode`가 `vendor-handoff` 또는 `structured-bridge`인 계획에서, Work Contract와 승인된 최소 문맥으로부터 handoff bundle을 결정론적으로 생성하고, raw secret/전체 저장소 텍스트를 포함하지 않으며, harness 자체 실행 지시(스킬 호출, Gate 규칙 등)가 vendor 세션에 명령으로 오인되지 않도록 데이터/지시 경계가 명시됨이 검증됨 | `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md` | (별도 구현 계획에서 정함) | 계획 필요 |
| REQ-HARNESS-001-d | Verification Runner | must | declared verification 명령(Run/Expected)을 실행자(local-agent/vendor-handoff/structured-bridge 중 어느 것이든)와 무관하게 실행·기록하며, vendor 자체 usage/tool loop를 모방하지 않음이 검증됨 | `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md` | (별도 구현 계획에서 정함) | 계획 필요 |
| REQ-HARNESS-001-e | vendor adapter 상태 | must | 각 vendor(Codex/Claude/OpenCode 등)의 structured bridge 지원 여부와 capability 확인 상태를 선언적으로 기록하고, 미확인 상태에서는 "bridge unavailable; native handoff continues"로 fail-closed 표시됨이 검증됨 | `04-safety-risk-verification.md`, `05-agent-operating-contract.md` | (별도 구현 계획에서 정함) | 계획 필요 |
| REQ-HARNESS-001-f | Control TUI | must | 사용자가 터미널에서 Work Contract 상태, 검증 결과, vendor adapter 상태를 확인할 수 있는 화면이 기존 AgentOS TUI 셸 위에 추가되고, 기존 대화형 세션/hook/session 기능과 회귀 없이 공존함이 검증됨 | `03-system-contract.md` | (별도 구현 계획에서 정함) | 계획 필요 |

### REQ-HARNESS-002: 전역 설치 기능의 프로젝트 반영

배경: 현재 `AGENTS.md`/`CLAUDE.md`는 cwd부터 조상 디렉터리까지 탐색해 어느 프로젝트에서든 발견되지만(`agentos/conversation/bootstrap.py:discover_context_files`), 스킬(`SKILL.md`)은 `AGENTOS_HOME/core/.agents/skills/`라는 고정 전역 경로에서만 검색되고(`agentos/terminal/sessions.py`), 그 경로조차 `agentos skill install <path>`로 스킬 하나씩 수동 복사해야만 채워진다(`agentos/commands/skill.py`) — 프로젝트별로 자동 반영되는 경로가 없다. `0005-agentos-independent-interactive-cli.md`가 이미 "project-local 규칙은 신뢰 승인 없이는 실행하지 않는다"는 원칙을 세워두었으나, 이를 실현하는 명시적 반영 명령이 없다.

- REQ-HARNESS-002 (must, 계획 필요): AgentOS 기능(스킬 등 `AGENTOS_HOME`에 설치된 자원)은 설치 후 OS 자원처럼 어느 프로젝트에서든 전역으로 일관되게 사용 가능해야 하며, 사용자가 명시적 명령(예: `agentos project init`)으로 특정 프로젝트에 전역 기능을 반영(오버라이드/추가)할 수 있어야 한다. 반영은 opt-in이며, 명시적 반영 명령 없이는 project-local 자원이 전역 동작을 바꾸지 않는다.
- 비목표: 이 requirement는 REQ-HARNESS-001-a~f(대상 프로젝트의 Work Contract/실행 계약)와 다른 층위다 — AgentOS 자신의 기능(스킬, 설정)을 전역과 프로젝트 사이에 어떻게 배치·전파하는지를 다루며, 대상 프로젝트의 작업 계약 내용과는 무관하다.

| ID | requirement | Priority | acceptance | 추적성 | Evidence link / 검증 근거 | status |
|---|---|---|---|---|---|---|
| REQ-HARNESS-002-a | 전역 스킬의 프로젝트 무관 일관 조회 | must | 스킬 조회 경로가 cwd와 무관하게 항상 같은 `AGENTOS_HOME` 스킬 집합을 반환함이 검증됨(현재 동작 유지, 회귀 확인) | `agentos/terminal/sessions.py`, `agentos/conversation/bootstrap.py` | `tests/test_conversation_bootstrap.py`, `tests/test_project_command.py` | 현재 |
| REQ-HARNESS-002-b | `agentos project init` 반영 명령 | must | 사용자가 이 명령으로 현재 프로젝트에 전역 스킬/설정을 명시적으로 반영(복사 또는 참조)할 수 있고, 명령을 실행하지 않으면 project-local 반영이 발생하지 않음이 검증됨 | `reference/decisions/0005-agentos-independent-interactive-cli.md` | `tests/test_project_command.py`; `scripts/verify-cli-isolated-install.sh` | 현재 |
| REQ-HARNESS-002-c | 전역 스킬 설치/동기화 경로 정합 | must | `agentos skill install`이 개별 스킬 단위 수동 복사 외에, 전역 스킬 디렉터리와 설치 소스 간 stale 상태를 사용자가 확인할 수 있는 수단(예: 버전/해시 비교)이 존재함이 검증됨 | `agentos/commands/skill.py` | `agentos skill status`; `tests/test_project_command.py` | 현재 |

### REQ-HARNESS-003: Gateway Core managed execution

- REQ-HARNESS-003 (must, 현재): 기존 vendor CLI 직접 사용을 보존하면서 AgentOS가 로컬 run queue, 상태, sanitized event ledger, 단일 worker, retry/cancel/prune 명령을 제공한다. Gateway는 `AGENTOS_HOME/gateway/` 아래 사용자 소유 데이터만 저장하고 credential, raw provider stderr, raw environment를 저장하지 않는다. 근거: `reference/decisions/0007-agentos-gateway-core.md`.

| ID | requirement | Priority | acceptance | 추적성 | Evidence link / 검증 근거 | status |
|---|---|---|---|---|---|---|
| REQ-HARNESS-003-a | Gateway run registry와 단일 worker | must | `agentos gateway submit/worker/status/events`가 restart-safe SQLite run registry와 단일 worker lock으로 동작하고, provider event가 sanitized ledger로 조회됨 | `agentos/gateway/`, `agentos/commands/gateway.py` | `pytest tests/test_gateway_store.py tests/test_gateway_service.py tests/test_gateway_worker.py -q`; `bash scripts/verify-gateway-core.sh` | 현재 |
| REQ-HARNESS-003-b | retry/cancel/prune 복구 흐름 | must | queued cancel, failed/interrupted retry, terminal-only preview-first prune이 검증되고 metadata policy prompt purge가 재시도 안내로 이어짐 | `docs/gateway-core.md` | `pytest tests/test_gateway_store.py tests/test_gateway_service.py -q` | 현재 |
| REQ-HARNESS-003-c | 기존 CLI/provider 경계 보존 | must | Gateway가 기존 provider registry와 `RuntimeRequest`/`InvocationEvent`를 재사용하고 direct vendor CLI와 `agentos run --once`를 대체하지 않음 | `03-system-contract.md`, `reference/decisions/0007-agentos-gateway-core.md` | `bash scripts/verify-cli-isolated-install.sh`; `bash scripts/verify-gateway-core.sh` | 현재 |

## 요구사항과 acceptance

| ID | requirement | Priority | acceptance | 추적성 | Evidence link / 검증 근거 | status |
|---|---|---|---|---|---|---|
| REQ-001 | AgentOS 설치 후 기본 확인 가이드 제공 | must | `setup.sh` 및 `verify-public-test-suite.sh` 통과 후의 명확한 상태 안내 제공 | | | 현재 |
| REQ-002 | agent-harness 기능의 점진적 마이그레이션 안내 | must | 향후 agent-harness 기능들이 AgentOS로 통합될 예정임이 가이드에 명시됨 | | | 현재 |
| REQ-003 | AHA CLI 쉘 스크립트 파이썬 이관 및 카탈로그 통일 | must | `aha` 명령어가 `agentos` 서브 커맨드로 100% 이관되고 카탈로그에서 잔재가 제거됨 | 2026-07-17-aha-cli-refactoring.md | `verify-public-test-suite.sh` 통과 | 완료 |
| REQ-LLM-001 | LLM credential strategy 승인 입력 고정 | must | provider, credential type, subscription entitlement, billing owner, official document URL/check date, grant/scope/redirect policy, allowed model policy가 ADR에 승인 근거와 함께 기록됨 | `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` | `PASS owner-subscription-auth-input-recorded` | 현재 |
| REQ-LLM-002 | API key adapter를 1차 구현 경로에서 제외 | must | ADR과 후속 handoff가 API key 입력, import, 저장, API-key adapter 구현 제외를 명시함 | `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` | `PASS subscription-implementation-scope-separated` | 현재 |
| REQ-LLM-003 | Mock-only LLM runtime contract 추가 | must | 실제 provider 호출, OAuth, API key, persistent credential store, billing 없이 mock provider와 sanitized JSONL event contract가 CLI에서 검증됨 | `.agentos/project/exec-plans/active/2026-07-18-agentos-llm-core-mvp.md` | `pytest tests/test_cli.py tests/test_llm_core.py -q`; `PASS secret-redaction-jsonl`; `PASS llm-core-docs-aligned` | 현재 |
| REQ-LLM-004 | LLM runtime core foundation 추가 | must | provider registry, provider-independent auth store foundation, and canonical external CLI compatibility path가 구현되고, native OAuth/transport는 deferred 범위로 문서화됨 | `.agentos/project/exec-plans/active/2026-07-23-agentos-pi-style-llm-runtime.md` | `pytest tests/test_auth_store.py tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py -q`; `PASS docs-llm-core-scope-aligned` | 현재 |
| REQ-LLM-005 | native Codex auth/transport 소유 | must | AgentOS가 browser callback 우선/device-code fallback login lifecycle, refresh/logout/status, WebSocket 우선/SSE fallback native streaming transport를 직접 소유하고, external CLI compatibility path는 native 실패 시에만 선택되는 recovery-only debug/rollback path로 재분류됨 | `.agentos/project/exec-plans/active/2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md` | `pytest tests/test_codex_oauth.py tests/test_codex_transport.py tests/test_codex_provider.py tests/test_auth_store.py tests/test_cli_contract.py tests/test_tui_cli.py -q`; `PASS codex-native-docs-aligned` | 현재 |
| REQ-CLI-001 | 독립 대화형 AgentOS CLI | must | isolated install 후 source checkout 밖에서도 `agentos --help`, `agentos setup`, `agentos doctor`, TTY 대화형 세션, `run --once`가 명시된 exit/output contract로 동작 | `0005-agentos-independent-interactive-cli.md` | `PASS cli-focused-suite`; `PASS agentos-cli-isolated-install`; `PASS interactive-cli-acceptance`; `PASS agentos-independent-cli-suite` | 완료 |
| REQ-CLI-002 | 안전하고 관측 가능한 hook/input lifecycle | must | hook ordering/timeout/failure/cancel/redaction이 typed event와 tests로 검증되고, hook이 JSONL stdout과 credential boundary를 침범하지 않음 | `0005-agentos-independent-interactive-cli.md` | `PASS cli-hook-registry-contract`; `PASS cli-hook-secret-regression`; `PASS interactive-cli-acceptance` | 완료 |
| REQ-CLI-003 | 시각적으로 이해 가능한 AgentOS TUI | must | TTY에서 transcript, composer, footer, command palette, session picker, recovery가 검증되고, 완료 도구 활동은 안전한 요약으로 기본 축약되며 `Ctrl+O`로 같은 transcript의 sanitized 상세를 열고 닫을 수 있다. no-TTY JSONL contract, credential boundary, existing session retention/delete/prune confirmation, and only existing AgentOS-built hooks boundary가 유지됨 | `.agentos/project/exec-plans/active/2026-07-19-agentos-tui-ux-architecture.md`, `.agentos/project/exec-plans/active/2026-07-30-tui-tool-log-density.md` | `PASS tui-tool-log-density-focused-suite`; `PASS tui-tool-log-density-redaction`; `PASS agentos-tui-focused-suite`; `PASS agentos-tui-secret-recovery-suite`; `PASS interactive-cli-acceptance`; `PASS agentos-cli-isolated-install`; `PASS installed-tui-smoke`; `PASS agentos-public-suite`; `PASS agentos-tui-docs-aligned` | 완료 |
| REQ-KNOWLEDGE-001 | 장기지식 저장·검토·publish·검색 흐름 | must | Markdown frontmatter 계약, `docs/knowledge/inbox` 검토 영역, `references`/`topics`/`decisions` publish 영역, `agentos knowledge` CLI의 inbox/publish/update/deprecate/list/search/context 명령, 경로/라인 근거 인용 출력이 검증됨. Knowledge 문서는 evidence이며 root docs, active plan, Gate 2, protected-path rules를 override하지 않음 | `.agentos/project/exec-plans/active/2026-08-01-knowledge-base-lifecycle.md`, `docs/knowledge/README.md` | `pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py -q`; `agentos knowledge --help` | 현재 |

추적성 규칙:

- Do not claim requirement completion without a source doc and 검증 근거 path.
- If the 요구사항 table becomes too large or one requirement maps to multiple implementation/test artifacts, create a registered `reference/implementation/` RTM supporting doc.

## 범위 경계

포함:

- `docs/getting-started.md` 전면 개편
- `README.md` 문맥 교정 (필요시)
- `aha` 잔재 제거를 위한 `catalog/` 마크다운 및 JSON 수정
- 독립 설치 가능한 `agentos` CLI command family와 대화형 session surface
- typed event stream, user input normalization, opt-in hook lifecycle, session/history UX
- TUI transcript, composer, footer, command palette, and session picker UX for `REQ-CLI-003`
- `README`와 `docs/getting-started.md`의 설치·대화·자동화·복구 안내

제외:

- 코어 엔진(`harness_loop.py`) 내부의 추론 로직 자체 수정
- pi의 TypeScript/Bun/TUI runtime 직접 이식, Hermes gateway/메신저/백업 등 대규모 운영 command 복제
- arbitrary third-party code hook 또는 승인 없는 project-local hook 실행
- LLM API key 입력, import, 저장, API-key adapter 구현
- provider session 호출, OAuth client 등록, credential persistence, or billing-affecting actions before a separate reviewed implementation plan (REQ-LLM-005는 이 경계 안에서 승인됨)
- TUI does not change session retention, session auto-delete behavior, delete/prune confirmation remains unchanged, or hook trust policy; it may show only existing AgentOS-built hooks and sanitized hook events.

허용된 예외:

- `REQ-LLM-003`의 mock-only LLM runtime contract는 provider credential strategy 승인 전에도 구현할 수 있다. 이 예외는 실제 provider 호출, OAuth/account-login, API key path, persistent credential store, billing-affecting behavior, or approved credential status claim을 만들 수 없다.
- `REQ-LLM-004`의 core foundation은 local-only provider registry와 auth store foundation까지 허용했다. `REQ-LLM-005` 승인 이후 `codex`의 native OAuth/transport, live token refresh, documented OpenAI Codex account-login endpoint 호출이 허용 범위에 포함된다. 승인 범위는 여전히 API key adapter, 비공식/미문서화 endpoint 추측, credential persistence 확장을 제외한다.

범위 변경 트리거:

- 추가적인 문서(예: SECURITY.md)에서도 혼동을 주는 문구가 발견될 경우

## 미해결 질문

| Question | Owner | Impact | Blocking? |
|---|---|---|---|
| 실제 Codex account-login provider adapter의 구현 파일, runtime command surface, and verification sequence는 무엇인가? | implementation owner | 후속 구현 계획 범위 결정 | Yes, for real provider implementation |
| 첫 CLI MVP의 hook 선언 형식과 session 보존 기간은 무엇인가? | implementation owner | REQ-CLI-002 API 및 migration 범위 | Yes, for CLI implementation plan |
| REQ-HARNESS-001-a의 `execution_mode`(`local-agent`\|`vendor-handoff`\|`structured-bridge`)/`executor`/`delegation` 필드를 exec-plan header(TEMPLATE.md 포함)의 어느 위치에 추가할지, 그리고 기존 완료된 exec-plan(암묵적으로 모두 `local-agent`)을 소급 표기할지는 무엇인가? | 프로젝트 오너 | 이후 001-b~f 전체 구현과 writing-plans 스킬 확장 범위 결정 | Yes, for the first harness implementation plan |
| Codex CLI와 Claude Code CLI가 REQ-HARNESS-001-e의 structured bridge에 쓸 수 있는 안정된 machine-readable output(JSON status, exit code contract 등)을 실제로 제공하는가? | implementation owner | bridge 구현 여부와 001-e/001-c 범위 결정 | Yes, for vendor adapter status implementation |

## 지원 문서

이 root doc이 너무 길어지거나 모호해질 때만 requirement brief, user stories, RTM, implementation guide, wireframe-like support note를 `reference/implementation/` 아래 supporting doc으로 만든다. supporting doc은 `00-project-index.md`에 등록되어야 한다.

- `.agentos/project/reference/implementation/2026-07-18-cli-llm-vscode-integration-analysis.md` - LLM auth_strategy_evidence and current credential gap.
- `.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md` - approved LLM credential strategy approval record.
- `.agentos/project/reference/decisions/0005-agentos-independent-interactive-cli.md` - independent interactive CLI and hook/input direction.
