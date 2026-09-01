# Intent Sheet: writing-plans 리뷰 경계 정렬

**날짜:** 2026-09-01
**요청자 의도 요약:** 기존 active 계획을 정리한 뒤, 반복적인 메타 리뷰 없이 구조적으로 명확한 실행 계획을 만들도록 writing-plans 계약과 검증기를 고친다.

## 가설

> 기능 Task, 사전 Gate 2, protected 승인, 구현 후 closeout을 서로 다른 lifecycle 단계로 고정하고 이를 자동 검증하면, reviewer feedback이 같은 계획의 Gate 증명을 계속 확장하는 문제가 사라질 것이다.

## Plan Quality Gate

- [ ] Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py tests/test_cryptographic_hook.py`
  Expected: exit 0; canonical usability metadata, review/approval/closeout 경계, artifact signing semantics의 회귀 사례가 모두 PASS.
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: `PASS` manifest integrity.
- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && python3 -m pytest -q tests/test_setup_bootstrap.py tests/test_unified_hooks.py`
  Expected: exit 0; lifecycle registry와 hook bundle contract가 정렬된 verifier에서 PASS.

## 범위 제약 (Scope Fence)

- 포함: `writing-plans` 문서·template·artifact validator·서명 스크립트의 역할 문구·해당 회귀 테스트·동일 해시 경계를 복제한 hook 검증기·reviewer의 메타 경계 문구.
- 제외: 새로운 reviewer service, 외부 API/MCP, raw secret 출력, 기존 archive 계획의 재작성, active 계획 자동 삭제, runtime의 독립 reviewer 호출 메커니즘 신설.

## 기술 스택 제약

- Python 표준 라이브러리, pytest, 기존 Bash manifest/lifecycle 도구만 사용한다.

## Worktree Decision

- 필요 여부: 불필요.
- 이유: 현재 feature branch가 이 변경 전용이며 병렬 작업을 수행하지 않는다.
- ownership: `plan/2026-08-31-pre-plan-decision-gate-split-2` 한 브랜치·한 작업자.

## 우선순위

- 프로덕션 수준의 안정성과 회귀 방지 우선.
