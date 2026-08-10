# Intent Sheet: Stop 훅의 계획 리뷰 초점화

**날짜:** 2026-08-10
**요청자 의도 요약:** 계획문서 review artifact의 형식 문제 때문에 세션 종료와 핵심 구현 판단이 불필요하게 막히지 않도록 Stop 훅의 책임을 줄이고, 실제 구현 시작 전에는 독립 리뷰 증거를 계속 강제한다.

## 가설

> Stop 훅을 종료 안전·검증 고지에만 집중시키고, plan review artifact의 fail-closed 검증을 실제 실행 진입점으로 옮기면 독립 리뷰의 신뢰성을 잃지 않으면서 형식적 중단과 구조적 재리뷰 시간을 줄일 수 있다.

## Plan Quality Gate

- [ ] Run: `python3 -m pytest .agents/skills/harness/run-all-tests/tests/test_stop_review_gate.py .agents/skills/harness/run-all-tests/tests/test_harness_loop.py -q` Expected: Stop 훅은 missing/invalid artifact에 warning+continue, loop 실행은 invalid artifact에 fail-closed인 회귀 테스트 PASS
- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-08-10-stop-hook-review-focus.md` Expected: `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash .agents/skills/harness/run-all-tests/tests/run_all_tests.sh` Expected: manifest integrity 및 harness suite PASS

## 범위 제약 (Scope Fence)

- 포함: Stop 훅의 reviewed-plan artifact 처리, harness loop와 executing-plans의 실행 전 artifact 검증, 관련 테스트·문서·root traceability 업데이트
- 제외: plan-reviewer/principle-auditor/usability-reviewer 체크리스트 완화, reviewer artifact schema 약화, loop lock·dirty-worktree 완료 검증 제거, 자동 reviewer 생성, 새로운 외부 서비스·DB·대시보드

## 기술 스택 제약

- Python 표준 라이브러리와 기존 `review_artifacts.py`를 재사용한다.
- Stop hook의 warning은 reviewer artifact를 만들거나 plan을 수정하지 않는다.
- protected `.agents` 변경은 authorized architect 확인, principle-auditor audit, manifest sync, full harness test 후에만 수행한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 feature branch에서 계획만 작성하며 병렬 구현을 시작하지 않는다.
- ownership: `feature/stop-hook-review-focus`

## 우선순위

- 신뢰성 유지와 불필요한 종료 차단 감소를 함께 달성하는 최소 변경을 우선한다.
