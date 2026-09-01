# Intent Sheet: 핵심 변경 중심의 계획 리뷰

**날짜:** 2026-08-31
**요청자 의도 요약:** 일반 reviewer 검증에서 과도한 전체 plan hash 의존성을 제거하고, 진행 메타데이터 변경은 재리뷰하지 않으며, hash/signature는 protected-path 승인과 감사 추적에만 사용한다。

## 가설
> 질문을 통해 사용자의 의도를 확정한 Intent Sheet를 기준으로 삼고, 도구가 semantic 변경을 자동 판정하면 일반 reviewer의 불필요한 재호출과 전체 plan hash 관리 비용을 줄이면서 protected 변경의 hash/signature 안전성은 유지될 것이다。

## Plan Quality Gate
> 실행 후 아래 조건들이 터미널 명령으로 동일하게 판정되는가?
- [ ] Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests tests/test_plan_review_scope.py` Expected: scope-normalization 회귀 테스트가 모두 PASS.
- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan <fixture-plan> --json` Expected: metadata-only 변경은 기존 artifact를 valid로 유지하고 semantic 변경만 자동 분류되어 재리뷰 상태가 된다.
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash scripts/verify-public-test-suite.sh` Expected: `PASS`.

## 범위 제약 (Scope Fence)
- 포함: 일반 reviewer의 전체 plan hash 의존성 제거, 도구 기반 semantic diff 분류, metadata-only·semantic-change fixture, 기본 reviewer 유지와 추가 reviewer 조건화, reviewer focus 및 질문 gate.
- 제외: 기본 plan-reviewer·principle-auditor 제거, reviewer 독립성·승인 권한 완화, protected-path architect approval 제거, 계획의 검증 명령 생략, 자동 recursive review, 기존 active plan 구현.

## 기술 스택 제약
- Python 표준 라이브러리, pytest, 기존 JSON artifact schema와 shell verification만 사용한다.
- 현재 harness protected path 변경은 별도 architect approval과 manifest 검증을 거친다.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout의 기존 변경을 보존한 feature branch에서 계획을 준비하며, 구현 시 소유권 충돌을 별도 점검한다.
- ownership: `plan/review-scope-filter`

## 우선순위
- 완전한 구현: 토큰 절감보다 semantic review 누락 방지와 재현 가능한 PASS/FAIL을 우선한다.
- 하네스 코어 변경은 관련 전문 reviewer만 추가하되, reviewer 독립성·protected approval·manifest 검증은 유지한다.
