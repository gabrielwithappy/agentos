# 0002 - AgentOS REPL Deprecation

- Expansion Trigger:
- parent root doc: `06-decisions-change-log.md`
- reason for creation: ADR
- owner: User / Agent
- freshness rule: Refresh when a decision is accepted, review evidence changes, or long-lived architecture context is revised.
- status: 현재
- source evidence: 사용자(PO) 합의 (Ouroboros 벤치마킹 반영)
- links back to: `06-decisions-change-log.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, or reviewer authority

## 결정 (Decision)
AgentOS 일반 대화형 REPL(채팅) 인터페이스 개발 중단 및 워크플로우 엔진으로의 집중 결정.

## 근거 (Rationale)
일반 대화형 UI는 외부 전용 프론트엔드(VSCode, Discord 등)에 위임하여 프로젝트 핵심 역량을 상태/워크플로우/가이드 인터뷰 관리에 집중.
