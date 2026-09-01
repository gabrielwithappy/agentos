# 계획 전 결정 게이트 하네스 에이전트 분해 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-09-01<br>
> reviewed: false<br>
> user_request: 리뷰 실패가 반복되는 대형 계획을 구현 가능한 단위로 작게 분리한다.<br>
> active_agent: Codex<br>
> active_session: pre-plan-decision-gate-split-r1<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **범위 고정:** 이 문서는 구현을 직접 실행하지 않는다. 아래 자식 계획의 순서·경계·의존성만 관리한다.<br>

**목표:** 계획 전 결정 게이트 기능을 서로 독립적으로 리뷰·구현·검증할 수 있는 세 계획으로 분해한다.

**사용자 결과:** 각 기능 단위가 짧은 계획과 좁은 파일 소유 범위를 가지므로 한 영역의 리뷰 수정이 다른 영역의 구현을 막지 않는다.

**진행 상태:** 분해 초안 작성, 자식 계획 3개 리뷰 대기

**아키텍처:** `pre-plan-decision-reviewer`의 판정 계약을 먼저 고정하고, 기존 intent/writing 흐름 연결을 그 계약의 소비자로 분리한다. 사용자 문서·project traceability는 동작 계약과 분리된 세 번째 계획으로 둔다. 각 자식 계획은 자체 Gate 2와 protected-path 검증을 가진다.

**기술 스택:** Markdown 계획/agent contract, pytest, 기존 lifecycle·manifest 도구

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 분해 초안 / 리뷰 대기 |
| 완료됨 | 반복 리뷰 실패 원인과 기존 계획의 책임 경계 식별 |
| 현재 위치 | 자식 계획 3개 생성 및 독립 리뷰 준비 |
| 다음 단계 | 각 자식 계획을 별도로 Gate 2 리뷰하고 승인된 순서로 구현 |
| 완료 신호 | 자식 계획 3개가 각각 `reviewed: true`가 될 수 있는 독립 범위와 PASS 검증을 가짐 |

## 세션 중단 대비 체크포인트

- 현재 완료 범위: 기존 대형 계획을 핵심 계약·흐름 연결·사용자 surface의 세 책임 단위로 분해했다.
- 미완료 작업: 자식 계획 Gate 2 리뷰, 보호 경로 승인, 자식별 구현과 검증.
- 다음 세션 첫 작업: `plan_lifecycle.py refresh` 후 자식 계획 1의 Gate 2 리뷰를 시작한다.
- 아직 안 한 검증: 자식 계획별 focused test, Gate 2 artifact, manifest check, public suite.
- 관련 HISTORY checkpoint: `[LOOP_STOP] trigger_id=active-plan-gate2-approval-blocker-20260901`.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | triage, 흐름 연결, 문서화가 각각 짧은 실행 계획으로 제공된다. |
| 누구를 위한 것인가? | 계획 작성자, 리뷰어, 구현자, 프로젝트 오너. |
| 일상 사용에서 무엇이 달라지는가? | 한 자식 계획의 수정·재리뷰만 반복하고 나머지 범위는 안정적으로 유지할 수 있다. |
| 무엇은 바뀌지 않는가? | 구현 동작, reviewer authority, protected approval, secret redaction, manifest 규칙은 바뀌지 않는다. |

## 장기 적용 표면

- traceability surface: 이 부모 계획, 세 자식 active plan, `HISTORY.md`, lifecycle board, 자식별 Gate 2 traces
- durable result surface: 자식 계획이 지정하는 agent contract, skill 문서, 테스트, 사용자 문서와 project root 문서
- documentation-only exception: 이 부모 계획은 분해 조정 문서이므로 durable result는 자식 계획의 실제 변경 표면에 남는다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 핵심 판정 계약 | 명확/사소한 공백/material ambiguity 판정이 독립적으로 고정됨 | `2026-09-01-pre-plan-decision-triage.md` | 자식 계획 focused pytest + Gate 2 |
| 2. 흐름 연결 | blocking 질문 전 계획 생성 금지와 답변 후 재개가 연결됨 | `2026-09-01-pre-plan-flow-integration.md` | 자식 계획 회귀 테스트 + Gate 2 |
| 3. 문서·추적성 | 질문·재개 방법과 결과 위치를 사용자가 찾을 수 있음 | `2026-09-01-pre-plan-user-surface.md` | 자식 계획 문서 계약 + lifecycle |

## 파일 구조

- 유지·수정: 이 부모 계획(분해와 의존성만)
- 생성: `.agentos/project/exec-plans/active/2026-09-01-pre-plan-decision-triage.md`
- 생성: `.agentos/project/exec-plans/active/2026-09-01-pre-plan-flow-integration.md`
- 생성: `.agentos/project/exec-plans/active/2026-09-01-pre-plan-user-surface.md`
- 제외: `.agents/hooks/**`, unified-hook 구현, 기존 dirty baseline `docs/knowledge/`, 자식 계획에 명시되지 않은 protected path

## 의존성 분석

- 외부 의존성: 없음
- 순서: triage 계약 → flow integration → user surface. 각 계획의 단위 테스트와 Gate 2는 해당 계획 내부에서 수행한다.
- 공통 규칙: 자식 계획은 모두 `reviewed: false`로 시작하며, 독립 `plan-reviewer`·`principle-auditor`와 user-facing 변경 시 `usability-reviewer` PASS 및 필요한 authorized architect 승인을 얻기 전 구현하지 않는다.
- 검증: 자식 계획 변경 후 `plan_lifecycle.py refresh`와 `sync-manifest.sh --check`를 실행한다.

## Plan Quality Gate

- 각 자식 계획은 단일 책임, 정확한 파일 소유 범위, 단계당 하나의 행동, `Run:`/`Expected: PASS`를 가진다.
- 자식 계획 간 중복 파일 수정은 금지한다. 선행 계획의 결과는 후행 계획의 입력 계약으로만 참조한다.
- 보호 경로 변경은 자식 계획 자체의 Gate 2와 authorized architect 승인으로 닫는다.
- 이 부모 계획의 `reviewed: true` 전이는 자식 계획의 구현 완료를 의미하지 않으며, 부모는 조정 기록으로만 유지한다.

## 리뷰 반영 이력

- 2026-09-01: 기존 5 Task 대형 계획을 핵심 계약·흐름 연결·사용자 surface의 3개 자식 계획으로 분리. Gate 2/manifest는 각 자식의 소유 범위로 이동.

## 구현 결과

(부모 계획은 구현하지 않음. 자식 계획의 결과를 참조한다.)

## 사용 방법

1. `2026-09-01-pre-plan-decision-triage.md`를 먼저 리뷰·승인·구현한다.
2. 그 결과가 PASS이면 flow integration, 이후 user surface를 같은 방식으로 진행한다.
3. 각 계획의 Gate 2와 검증 증거를 계획별 review directory에 남긴다.

## 아카이브 결정

세 자식 계획의 구현·검증이 끝난 뒤에도 부모와 자식 계획은 사용자의 명시적 archive 요청 전까지 active에 둔다.
