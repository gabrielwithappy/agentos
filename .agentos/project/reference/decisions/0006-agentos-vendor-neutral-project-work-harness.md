# 0006 - AgentOS vendor-neutral project work harness

- Expansion Trigger: 기존 product docs가 native Codex runtime/TUI를 canonical 제품 방향으로 고정하고 있어, "AgentOS는 여러 vendor coding-agent(Codex·Claude·OpenCode)를 넘나들며 한 프로젝트의 작업 계약·검증·이력을 유지하는 vendor-neutral project work harness"라는 사용자 목표와 충돌한다. 이 충돌을 root docs 전반에 흩어 기록하지 않고 한 곳에서 해소해야 한다.
- parent root doc: `01-project-charter.md`, `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`, `05-agent-operating-contract.md`, `06-decisions-change-log.md`
- reason for creation: control plane(AgentOS)과 execution plane(vendor CLI)의 제품 소유 경계, 그리고 기존 native-runtime 결정(0004/0005)과의 우선순위 관계를 root docs가 참조할 단일 근거로 고정한다.
- owner: project owner
- freshness rule: control/execution/bridge ownership, 기본 사용자 여정, native runtime의 확장 승인 조건, 또는 0004/0005와의 관계가 바뀌면 갱신한다.
- status: 현재
- source evidence: 사용자 2026-07-26 목표 지시(`vendor-neutral project work harness` 전환); 현재 `agentos/conversation/*`, `agentos/terminal/*`의 native Codex runtime/TUI 구현 상태(직접 확인 완료, 이번 ADR로 인한 코드 변경 없음); `0004-agentos-llm-credential-strategy.md`; `0005-agentos-independent-interactive-cli.md`.
- links back to: `0004-agentos-llm-credential-strategy.md`, `0005-agentos-independent-interactive-cli.md`, `06-decisions-change-log.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, reviewer authority, or human approval requirements.

## 결정

AgentOS는 vendor-neutral project work harness로서 제품 방향을 정의한다. AgentOS control plane은 프로젝트 작업 계약(Work Contract), Context Compiler, lifecycle/evidence ledger, Verification Runner, vendor adapter 상태, Control TUI를 소유한다. Codex·Claude·OpenCode 등 vendor execution plane은 실제 대화, tool loop, provider 세션, 사용량, 모델/플러그인 기능을 소유한다. 두 plane 사이에는 optional structured bridge만 존재하며, 안정된 machine-readable interface가 있을 때만 최소 실행 이벤트를 AgentOS 자동화에 제공한다. 화면 파싱이나 숨은 fallback은 두지 않는다.

사용자 기본 여정은 다음 순서로 고정한다: AgentOS에서 작업 계약과 검증 기준을 확인한다 → 원본 vendor CLI에서 handoff bundle로 실제 작업을 수행한다 → declared verification 결과를 AgentOS evidence에 기록한다. handoff bundle은 사용자가 원본 CLI에서 수행할 작업의 승인된 최소 문맥 묶음이다.

이 ADR은 향후 기본 UX와 투자 방향의 제품 책임·execution boundary에만 우선한다. `0004`의 credential/security 제약과 `0005`의 독립 CLI 결정이 승인한 기존 runtime의 운영 상태를 철회하지 않는다 — 현재 native Codex provider와 ConversationRuntime은 이 ADR로 삭제하거나 변경하지 않으며, 일반 기본 경로로 승격되지 않는 기존 구현/고급 경로로 남는다. runtime 중단, migration, credential 정책 변경은 owner 승인과 별도 reviewed implementation plan 없이는 수행하지 않는다. 과거 계획과 구현 증거(0004, 0005, 관련 active/archive plan)는 역사 기록으로 보존한다.

## 범위와 비범위

- 포함: control/execution/bridge 소유 경계, 기본 사용자 여정 3단계, native runtime의 non-canonical 재분류, 후속 확장에 필요한 승인 조건.
- 제외: provider API abstraction, API key 저장, OAuth, model catalog, usage 수집, PTY embedding, screen scraping, vendor CLI command parsing, generic workflow DSL, multi-agent scheduler, cost router, persistent task database, source code/TUI 구현 변경, 기존 session 데이터 마이그레이션.

## 0004/0005와의 관계

`0005`는 대체되지 않는다 — 독립 대화형 CLI와 hook/input lifecycle 결정은 AgentOS control plane의 Control TUI 구현 기반으로 그대로 유지된다. `0004`의 credential/security 경계(raw secret 비저장, account-login 경로, API-key adapter 제외)도 그대로 유지된다. 이 ADR은 두 결정 위에 "AgentOS가 vendor 대화 자체를 복제하지 않는다"는 상위 제품 책임 경계를 추가할 뿐이다.

## 결과와 후속 조건

후속 구현(예: Work Contract 스키마, Context Compiler, Verification Runner, structured bridge adapter)은 이 ADR을 근거로 삼는 별도 reviewed implementation plan과 Gate 2 통과 이후에만 시작한다. 이 문서 전환 자체는 어떤 runtime migration도 승인하지 않는다.
