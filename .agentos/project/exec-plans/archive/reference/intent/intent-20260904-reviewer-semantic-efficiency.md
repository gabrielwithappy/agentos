# Intent Sheet: 의미 중심 하네스 리뷰 효율화

**날짜:** 2026-09-04  
**요청자 의도 요약:** 하네스 리뷰가 문법·문체·표기 차이를 과도하게 차단하지 않으면서도 실행 가능성·안전·독립 승인에 집중하게 한다.

## 가설

> reviewer 역할별로 blocking 조건을 실제 실행·안전·복구 위험으로 한정하고 표현 고정 테스트를 구조·행동 계약으로 바꾸면, 같은 품질을 더 적은 재리뷰와 토큰으로 확보할 수 있다.

## Plan Quality Gate

- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh && echo "PASS reviewer-contract-policy"` Expected: `PASS reviewer-contract-policy`
- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_user_facing_terminology_clarity_contract.sh && bash .agents/skills/harness/run-all-tests/tests/harness/test_intent_goal_first_contract.sh && bash .agents/skills/harness/run-all-tests/tests/harness/test_dependency_gate_contract.sh && echo "PASS semantic-contract-tests"` Expected: `PASS semantic-contract-tests`
- [ ] Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py && echo "PASS review-artifact-scope-tests"` Expected: `PASS review-artifact-scope-tests`
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && echo "PASS manifest-integrity"` Expected: `PASS manifest-integrity`

## 범위 제약 (Scope Fence)

- 포함: 세 Gate 2 reviewer의 blocking 분류·역할 경계, `writing-plans`의 조건부 review routing, ordinary artifact 상태의 명확한 구분, 표현 고정 harness verifier와 PASS 표기 정규화, 해당 regression tests.
- 제외: `AGENTS.md` 원칙 변경, 프로젝트 문서·lifecycle 전면 개편, 신규 reviewer/서비스/외부 의존성, secret·prompt boundary·protected architect approval 완화, 실제 구현 계획의 Run/Expected 제거.

## 기술 스택 제약

- 기존 Markdown, Python 3, Bash, pytest와 하네스 verifier만 사용한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 단일 feature branch에서 계획과 이후 보호 경로 변경을 순차적으로 검토한다.
- ownership: `plan/reviewer-semantic-efficiency` branch의 현재 Codex 세션.

## 우선순위

- 안정성과 최소 변경 우선: 현재 semantic snapshot 및 안전 계약을 보존한 채 중복·lexical review 비용만 줄인다.
