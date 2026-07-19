# 0002 - AgentOS REPL Deprecation

- Expansion Trigger:
- parent root doc: `06-decisions-change-log.md`
- reason for creation: ADR
- owner: User / Agent
- freshness rule: Refresh when a decision is accepted, review evidence changes, or long-lived architecture context is revised.
- status: 취소됨 (2026-07-19)
- source evidence: 사용자(PO) 2026-07-19 결정 변경
- links back to: `06-decisions-change-log.md`, `0005-agentos-independent-interactive-cli.md`
- does not override: root project documents, active plan, AGENTS.md, vendor guides, protected-path rules, or reviewer authority

## 취소된 결정 (Superseded Decision)
AgentOS 일반 대화형 REPL(채팅) 인터페이스 개발 중단 및 워크플로우 엔진으로의 집중 결정.

## 당시 근거 (Historical Rationale)
일반 대화형 UI는 외부 전용 프론트엔드(VSCode, Discord 등)에 위임하여 프로젝트 핵심 역량을 상태/워크플로우/가이드 인터뷰 관리에 집중.

## 취소 사유와 후속 결정

프로젝트 오너는 2026-07-19에 일반 대화형 CLI가 낮은 구현 난이도로 사용자 경험을 개선하고, 사용자 hook과 입력 관리를 통해 harness 성능을 높일 수 있다고 판단했다. 이 ADR은 역사 기록으로 보존하되 현재 구현 범위를 제한하지 않는다.

현재 권한 기준은 `0005-agentos-independent-interactive-cli.md`다. 새 CLI는 독립 설치·대화형 세션·단발 실행·구조화 출력·명시적 hook lifecycle을 다루며, credential 및 외부 provider 경계는 `0004`와 root safety contract를 계속 따른다.
