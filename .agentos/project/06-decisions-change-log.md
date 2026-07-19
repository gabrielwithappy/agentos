# 결정·변경 로그

목적: Record accepted decisions, scope change, and handoff state.
주요 독자: 프로젝트 오너, 리뷰어/운영자, 구현 에이전트, 후속 핸드오프 에이전트.
가능하게 하는 결정: continue/stop decision, change acceptance, handoff 준비 상태, closeout evidence.
에이전트 핵심 정보: decision log, change impact, unresolved follow-up.
현재 증거 / 최신성: update when ownership, decision, scope, or handoff state changes.

## 결정 로그

| Date | decision | reference/decisions/ |
|---|---|---|
| 2026-07-17 | `agentos harness` 구현 시 쉘 스크립트 대신 파이썬으로 핵심 기능 완전 이관(Method B) 결정 | [0001-agentos-harness-python-cli.md](reference/decisions/0001-agentos-harness-python-cli.md) |
| 2026-07-18 | AgentOS 일반 대화형 REPL(채팅) 인터페이스 개발 중단 결정. 2026-07-19에 취소됨 | [0002-agentos-repl-deprecation.md](reference/decisions/0002-agentos-repl-deprecation.md) |
| 2026-07-19 | AgentOS 독립 대화형 CLI와 안전한 hook/input lifecycle을 구현 방향으로 승인 | [0005-agentos-independent-interactive-cli.md](reference/decisions/0005-agentos-independent-interactive-cli.md) |
| 2026-07-18 | LLM credential strategy approved: Codex account-login 후보를 후속 실제 provider 구현 계획의 입력으로 승인하고 API-key adapter를 1차 구현 경로에서 제외. Provider 호출, OAuth client 등록, credential persistence, 비용 발생 작업은 별도 구현 계획과 Gate 2 전까지 금지 | [0004-agentos-llm-credential-strategy.md](reference/decisions/0004-agentos-llm-credential-strategy.md) |

## 변경 관리

| Change | Scope impact | Schedule impact | Resource impact | Decision/status |
|---|---|---|---|---|
| AHA CLI 잔재 제거 및 파이썬 CLI로의 완전 이관 (REQ-003 추가) | 코드 및 카탈로그 문서 대폭 수정 포함 | 즉시 완료 | 없음 | 승인 및 구현 완료 |
| LLM credential strategy 승인 | root project docs, implementation evidence note, and ADR approval fields updated | 후속 real provider implementation plan 작성 가능 | billing owner: project owner; API-key billing path excluded | approved |
| REPL 중단 결정 취소 및 독립 CLI 방향 승인 | root docs, ADR, 후속 CLI implementation plan | 즉시 계획 작성 가능 | existing Python/Typer CLI를 기반으로 하며, provider credential safety boundary는 유지 | approved |

## 지원 문서

evidence를 root authority로 만들지 않고도 남겨야 할 때만 review, experiment, 종결, decision record, handoff supporting doc을 만든다. `00-project-index.md`에 등록한다.

- Use `reference/decisions/` for ADR-style records with context, options considered, decision, consequences, owner, evidence, review notes, and closeout packs when needed.

supporting docs는 root project 문서, active execution plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, human approval 요구사항을 override하지 않는다.

## 핸드오프 상태

- plan=.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md
- artifact=.agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md
- verification=Task 1.1 approval input is recorded in `0004-agentos-llm-credential-strategy.md`.
- next safe action=독립 대화형 CLI와 hook/input lifecycle의 file-level implementation plan을 작성하고 fresh Gate 2 review를 받는다. Codex provider adapter 확장은 credential boundary 안에서 별도 후속 범위로 유지한다.
