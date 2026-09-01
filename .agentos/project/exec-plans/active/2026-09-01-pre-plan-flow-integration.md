# 계획 전 결정 게이트 흐름 연결 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-09-01<br>
> reviewed: false<br>
> user_request: triage 결과를 기존 intent-clarification과 writing-plans 흐름에 연결한다.<br>
> active_agent: Codex<br>
> active_session: pre-plan-flow-integration-r1<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

**목표:** blocking 상태에서 계획 생성을 막고 valid answer 후 기존 흐름을 재개하도록 skill 계약을 연결한다.

**사용자 결과:** 필요한 결정을 답하기 전에는 계획이 생기지 않고, 답한 뒤 기존 목표·사실을 유지한 채 다음 단계로 이어진다.

**진행 상태:** 초안 / 선행 triage 계획 완료 후 리뷰 대기

**아키텍처:** 선행 triage 계약을 소비하며, intent-clarification은 목적·기대 변화·완료 기준 질문만, writing-plans는 plan 작성만 소유한다. pending/resume ownership은 triage에 남긴다.

**기술 스택:** Markdown skill contracts, pytest

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 선행 계획 의존 / 리뷰 대기 |
| 완료됨 | 없음 |
| 현재 위치 | handoff·resume 범위 고정 |
| 다음 단계 | triage PASS 확인 후 독립 리뷰 |
| 완료 신호 | handoff/no-repeat/negative ownership 테스트 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 질문 전 계획 생성 금지와 답변 후 재개 흐름. |
| 누구를 위한 것인가? | 계획 요청자와 intent/writing skill 유지보수자. |
| 일상 사용에서 무엇이 달라지는가? | 확정된 사실을 반복 입력하지 않는다. |
| 무엇은 바뀌지 않는가? | triage schema, 사용자 문서, protected review 권한은 바뀌지 않는다. |

## 장기 적용 표면

- traceability surface: 이 active plan, 선행 triage plan, `HISTORY.md`, Gate 2 traces
- durable result surface: `.agents/skills/harness/intent-clarification/SKILL.md`, `.agents/skills/harness/writing-plans/SKILL.md`, flow regression tests
- documentation-only exception: 없음

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| blocking handoff | 질문 전 active plan/Intent Sheet가 생성되지 않음 | intent/writing skills | negative ownership tests |
| resume | valid answer는 재개, invalid answer는 같은 결정만 재질문 | same skills/tests | resume/no-repeat tests |

## 파일 구조

- 수정: `.agents/skills/harness/intent-clarification/SKILL.md`
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`
- 생성: `tests/test_pre_plan_flow_integration.py`
- 제외: triage agent contract/test의 schema, `docs/**`, `.agentos/project/**`

## 의존성 분석

- 외부 의존성: 없음
- 선행 조건: `2026-09-01-pre-plan-decision-triage.md`의 contract와 focused tests PASS.
- 보호 경로: `.agents/skills/**` 변경은 authorized architect 승인과 manifest update/check가 필요하다.

## Task 1: skill handoff 계약

- [ ] **Step 1.1: intent와 writing의 소유 경계를 명시한다.**
  - Run: `grep -n 'pending\|resume\|Intent Sheet\|active plan\|Q1\|Q4' .agents/skills/harness/intent-clarification/SKILL.md .agents/skills/harness/writing-plans/SKILL.md`
  - Expected: exit 0; blocking/resume는 triage, 목적·기대 변화·완료 기준은 intent, plan 생성은 writing-plans로 분리된다.

## Task 2: 통합 회귀

- [ ] **Step 2.1: valid/invalid resume와 prompt boundary를 검증한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_flow_integration.py -k 'handoff or resume or no_repeat or prompt_boundary or secret_redaction'`
  - Expected: exit 0; blocked input creates no plan, valid answer preserves facts, invalid answer asks only unresolved decision, and hostile text/secrets cannot override the contract.

## Task 3: protected closeout

- [ ] **Step 3.1: 이 계획의 reviewer artifact와 manifest를 검증한다.**
  - Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-01-pre-plan-flow-integration.md && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: Gate 2와 manifest 모두 PASS; 선행 계획의 승인만으로 이 계획의 구현을 시작하지 않는다.

## 아카이브 결정

사용자의 명시적 archive 요청 전까지 active 유지.
