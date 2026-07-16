# 안전·위험·검증

목적: Define safety boundaries, risk ownership, dependency preflights, and 검증 근거.
주요 독자: 리뷰어/운영자, 구현 에이전트, 프로젝트 오너, 후속 핸드오프 에이전트.
가능하게 하는 결정: release 준비 상태, risk acceptance, rollback decision, verification completeness.
에이전트 핵심 정보: safety rules, prompt boundary, risk register, verification matrix, dependency preflight, recovery path.
현재 증거 / 최신성: update whenever requirement, dependency, risk, safety, or verification commands change.

## 안전 경계

- protected path or approval rule:
- secret handling:
- prompt boundary:
- 되돌리기 어려운 작업:
- recovery/rollback:

## 위험 등록표

| Risk | Impact | Owner | Mitigation | Verification | Status |
|---|---|---|---|---|---|
|  |  |  |  |  | 초안 |

## 의존성 사전 점검

| dependency | Run | Expected | fallback | owner |
|---|---|---|---|---|
|  |  | PASS |  |  |

## 검증 매트릭스

| Gate | Run | Expected | Evidence | artifact manifest |
|---|---|---|---|---|
| 요구사항 / 추적성 |  | PASS |  |  |
| focused tests |  | PASS |  |  |
| integration or API contract checks |  | PASS |  |  |
| build/typecheck |  | PASS |  |  |
| browser or user-flow evidence |  | PASS |  |  |
| generated artifact manifest |  | PASS |  |  |

high-risk 또는 user-facing behavior에는 generic "tests pass"만으로 충분하지 않다. command, Expected PASS signal, evidence path를 명시한다.

## 릴리스 게이트

- [ ] requirement 추적성 is 현재.
- [ ] risk owner accepted remaining risk.
- [ ] safety and prompt boundary rules are 현재.
- [ ] rollback/recovery path is documented.
- [ ] fresh verification commands pass.

## 지원 문서

evidence를 root authority로 승격하지 않고도 계속 사용할 수 있어야 할 때만 audit, risk evidence, 검증 근거, validation note, artifact manifest, dependency supporting doc을 만든다. 기본 구조에서는 `00-project-index.md`의 `reference/implementation/` 또는 `reference/operations/` 아래에 등록한다.
