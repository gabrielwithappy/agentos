# Intent Sheet: 계획 리뷰어 오케스트레이션

**날짜:** 2026-09-04
**요청자 의도 요약:** 계획 리뷰어를 기본 조정자로 삼아 필요한 전문 reviewer만 순차 호출하고, 충돌·순환 리뷰·불필요한 재리뷰를 막는다.

## 가설

> 리뷰 순서와 최종 판정을 `plan-reviewer`가 소유하고 `principle-auditor`를 보호/구조 변경에만 조건부 호출하면, 독립 리뷰의 신뢰성을 유지하면서 과도한 리뷰와 bootstrap 순환을 줄일 수 있다.

## Plan Quality Gate

- [ ] Run: `pytest .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q` Expected: `0 failed`
- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh` Expected: `PASS` 및 `FAIL=0`
- [ ] Run: `git diff --check` Expected: exit 0

## 범위 제약 (Scope Fence)

- 포함: `plan-reviewer`의 triage/충돌 조정 계약, 기존 review artifact 검사·상태 모델, 해당 계약 테스트와 writing-plans 안내
- 제외: 새 reviewer 종류, 별도 DB/queue, 자동 reviewer 병렬 실행, 사용자 CLI 문구 변경, 기존 frontmatter 기능 구현

## 기술 스택 제약

- Python 표준 라이브러리, Markdown, pytest

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 기능 브랜치에서 단일 소유자가 순차적으로 변경한다.
- ownership: `feature/plan-reviewer-orchestrator-20260904`

## 우선순위

- 안정성과 최소 변경 우선
