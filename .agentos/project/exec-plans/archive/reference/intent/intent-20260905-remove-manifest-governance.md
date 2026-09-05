# Intent Sheet: manifest 거버넌스 기능 제거

**날짜:** 2026-09-05  
**요청자 의도 요약:** 계획과 리뷰에 과도하게 결합된 manifest 기능과 전용 권한 게이트를 제거하고, 지속 가능한 일반 계획 리뷰만 유지한다.

## 가설

> `sync-manifest`, `_version.json` 자산 목록, `harness-architect` 승인 경로를 제거하면 계획 범위와 무관한 manifest·권한·Gate 2 차단이 사라지고, `plan-reviewer`와 `principle-auditor` 중심의 단순한 리뷰 흐름으로도 실행 가능성과 원칙 정합성을 유지할 수 있다.

## Plan Quality Gate

> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"

- [ ] Run: `if rg -n "sync-manifest|manifest update|authorized_architects|harness-architect|protected_change" AGENTS.md .agents/agents .agents/skills/harness catalog/skills/catalog.json .agentos/project/04-safety-risk-verification.md --glob '!**/archive/**' --glob '!**/traces/**'; then exit 1; else echo PASS active-manifest-reference-free; fi`  Expected: `PASS active-manifest-reference-free`
- [ ] Run: `test ! -e .agents/skills/harness/sync-manifest && test ! -e .agents/_version.json && test ! -e .agents/agents/harness/_version.json && test ! -e .agents/skills/harness/_version.json && echo PASS manifest-assets-removed`  Expected: `PASS manifest-assets-removed`
- [ ] Run: `pytest .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q`  Expected: 일반 `plan-reviewer`·`principle-auditor` 리뷰 계약 테스트가 모두 PASS한다.
- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh && bash scripts/verify-public-test-suite.sh`  Expected: 두 검증이 exit 0이고 public verifier가 `PASS agentos-public-suite`를 출력한다.

## 범위 제약 (Scope Fence)

- 포함: manifest 스킬·스크립트·목록 파일 삭제, `harness-architect` 전용 권한·승인 경로 삭제, 계획 리뷰에서 protected manifest 게이트 제거, 관련 catalog·문서·테스트·현재 active plan 참조 정리.
- 제외: archive 계획과 `HISTORY.md`의 과거 검증 기록 삭제·재작성, 일반 `plan-reviewer`·`principle-auditor` Gate 2 자체 제거, 제품 런타임 기능 변경, 외부 서비스·credential 변경.

## 기술 스택 제약

- Markdown, JSON, Bash, Python pytest, 기존 `plan_lifecycle.py`만 사용한다.
- 새 manifest·상태 저장소·권한 시스템을 추가하지 않는다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 전용 feature branch에서 단일 소유자가 순차적으로 수행한다.
- ownership: `chore/remove-manifest-governance`

## 우선순위

- 최소 운영 규칙과 재현 가능한 검증을 우선한다. 삭제 후 일반 계획 리뷰가 독립적으로 작동하는지 확인한 뒤에만 완료로 판단한다.
