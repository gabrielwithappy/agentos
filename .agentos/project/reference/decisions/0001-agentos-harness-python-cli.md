# 0001 - AgentOS Harness Python CLI 전환

- Expansion Trigger:
- parent root doc: `06-decisions-change-log.md`
- reason for creation: ADR
- owner: User / Agent
- freshness rule: Refresh when a decision is accepted, review evidence changes, or long-lived architecture context is revised.
- status: 현재
- source evidence: 사용자 피드백
- links back to: `06-decisions-change-log.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, or reviewer authority

## 결정 (Decision)
`agentos harness` 구현 시 쉘 스크립트 대신 파이썬으로 핵심 기능 완전 이관(Method B) 결정.

## 근거 (Rationale)
크로스 플랫폼 호환성 확보 및 IDE 슬래시 커맨드 트렌드에 맞춰 불필요한 레거시 상태 확인 기능 제거 목적.
