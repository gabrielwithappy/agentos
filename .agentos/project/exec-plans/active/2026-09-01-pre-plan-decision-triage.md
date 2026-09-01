# 계획 전 결정 triage 계약 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-09-01<br>
> reviewed: false<br>
> user_request: 계획 작성 전에 명확성 상태와 material ambiguity를 판정하는 최소 계약을 독립 구현한다.<br>
> active_agent: Codex<br>
> active_session: pre-plan-decision-triage-r1<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

**목표:** 네 가지 판정 상태와 secret-safe 결과 schema를 고정한다.

**사용자 결과:** 같은 입력은 같은 상태로 판정되고, material ambiguity일 때만 다음 단계가 이해 가능한 한 질문으로 제한된다.

**진행 상태:** 초안 / Gate 2 리뷰 대기

**아키텍처:** 이 계획은 triage agent contract와 순수 evaluator만 소유한다. intent/writing 연결과 사용자 안내 문서는 후속 계획에 남긴다.

**기술 스택:** Markdown, JSON fixture, pytest

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 없음 |
| 현재 위치 | 계약·테스트 범위 고정 |
| 다음 단계 | 독립 Gate 2 리뷰 후 구현 |
| 완료 신호 | focused pytest PASS와 세 reviewer PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | clear/minor_gap/material_ambiguity/invalid_answer의 일관된 판정. |
| 누구를 위한 것인가? | 계획 작성 흐름과 그 테스트를 유지하는 개발자·리뷰어. |
| 일상 사용에서 무엇이 달라지는가? | 구현 표면을 묻는 대신 결정이 필요한 내용만 질문된다. |
| 무엇은 바뀌지 않는가? | 기존 intent Q1–Q4와 protected approval은 이 계획에서 바꾸지 않는다. |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, plan-specific Gate 2 traces
- durable result surface: `.agents/agents/harness/pre-plan-decision-reviewer.md`, `tests/test_pre_plan_decision_reviewer.py`
- documentation-only exception: 없음

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 판정 schema | 네 상태와 질문 수가 고정됨 | agent contract, evaluator test | `pytest -k schema` → PASS |
| 질문 안전성 | 질문 하나·pending record·secret redaction이 고정됨 | same contract/test | `pytest -k question` → PASS |

## 파일 구조

- 생성: `.agents/agents/harness/pre-plan-decision-reviewer.md`
- 생성: `tests/test_pre_plan_decision_triage.py`
- 수정: `.agents/agents/harness/_version.json`, `catalog/agents/catalog.json`
- 제외: `.agents/skills/harness/**`, `docs/**`, `.agentos/project/**` (부모 계획과 후속 자식 소유)

## 의존성 분석

- 외부 의존성: 없음
- 보호 경로: `.agents/agents/**`와 catalog 변경은 authorized architect 승인 및 manifest update/check가 필요하다.

## Task 1: canonical triage 계약

**파일:** `.agents/agents/harness/pre-plan-decision-reviewer.md`

- [ ] **Step 1.1: 상태·필드·질문 형식을 정의한다.**
  - Run: `test -f .agents/agents/harness/pre-plan-decision-reviewer.md && grep -q 'material_ambiguity' .agents/agents/harness/pre-plan-decision-reviewer.md`
  - Expected: exit 0 and contract includes all four states, one-question rule, pending boundary, and prompt/data precedence.

## Task 2: evaluator 회귀 테스트

**파일:** `tests/test_pre_plan_decision_triage.py`

- [ ] **Step 2.1: 상태·질문 수·secret-safe 경계를 테스트한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_decision_triage.py`
  - Expected: exit 0; clear/minor_gap have zero questions and allow planning, material_ambiguity has exactly one question and no plan, invalid_answer preserves facts, and no secret/env value appears.

## Task 3: protected closeout

- [ ] **Step 3.1: Gate 2와 manifest를 이 계획에 귀속해 검증한다.**
  - Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-01-pre-plan-decision-triage.md && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: `PASS gate2-review-check` and manifest `PASS`; 구현은 독립 reviewer 3종과 authorized architect approval 이후에만 허용된다.

## 아카이브 결정

구현·검증 후에도 사용자의 명시적 archive 요청 전까지 active 유지.
