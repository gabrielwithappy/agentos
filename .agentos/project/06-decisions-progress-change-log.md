# 결정·진행·변경 로그

목적: Record accepted decisions, scope change, progress, 검증 근거, and handoff state.
주요 독자: 프로젝트 오너, 리뷰어/운영자, 구현 에이전트, 후속 핸드오프 에이전트.
가능하게 하는 결정: continue/stop decision, change acceptance, handoff 준비 상태, closeout evidence.
에이전트 핵심 정보: decision log, progress ledger, change impact, fresh 검증 근거, unresolved follow-up.
현재 증거 / 최신성: update when ownership, decision, scope, progress, verification, blocker, or handoff state changes.

## 결정 로그

| Date | decision | rationale | evidence | owner | reference/decisions/ |
|---|---|---|---|---|---|
| YYYY-MM-DD |  |  |  |  |  |

## 변경 관리

| Change | Scope impact | Schedule impact | Resource impact | Decision/status |
|---|---|---|---|---|
|  |  |  |  | 초안 |

## 진행 원장

| Date | plan= | increment | status | changed paths | artifact= | verification= | next safe action |
|---|---|---|---|---|---|---|---|
| YYYY-MM-DD |  |  | 초안 |  |  |  |  |

## 최신 검증 근거

Fresh verification evidence belongs here.

- focused command:
- full command:
- result:
- artifact=:
- verification=:
- evidence path:

## 핸드오프 상태

- 현재 state:
- completed:
- 중단됨:
- next safe action:
- 후속 핸드오프 에이전트 note:

## 지원 문서

evidence를 root authority로 만들지 않고도 남겨야 할 때만 review, experiment, 종결, decision record, handoff supporting doc을 만든다. `00-project-index.md`에 등록한다.

- Use `reference/decisions/` for ADR-style records with context, options considered, decision, consequences, owner, evidence, review notes, and closeout packs when needed.

supporting docs는 root project 문서, active execution plan, `AGENTS.md`, vendor guides, protected-path rules, reviewer authority, human approval 요구사항을 override하지 않는다.
