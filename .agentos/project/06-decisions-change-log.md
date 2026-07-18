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
| 2026-07-18 | AgentOS 일반 대화형 REPL(채팅) 인터페이스 개발 중단 및 워크플로우 엔진으로의 집중 결정 | [0002-agentos-repl-deprecation.md](reference/decisions/0002-agentos-repl-deprecation.md) |

## 변경 관리

| Change | Scope impact | Schedule impact | Resource impact | Decision/status |
|---|---|---|---|---|
| AHA CLI 잔재 제거 및 파이썬 CLI로의 완전 이관 (REQ-003 추가) | 코드 및 카탈로그 문서 대폭 수정 포함 | 즉시 완료 | 없음 | 승인 및 구현 완료 |

## 지원 문서

evidence를 root authority로 만들지 않고도 남겨야 할 때만 review, experiment, 종결, decision record, handoff supporting doc을 만든다. `00-project-index.md`에 등록한다.

- Use `reference/decisions/` for ADR-style records with context, options considered, decision, consequences, owner, evidence, review notes, and closeout packs when needed.

supporting docs는 root project 문서, active execution plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, human approval 요구사항을 override하지 않는다.
