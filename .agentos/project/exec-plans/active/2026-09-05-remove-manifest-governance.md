# manifest 거버넌스 기능 제거 구현 계획

> **상태:** 리뷰 대기 (완료 후 '완료'로 변경)<br>
> **작성일:** 2026-09-05<br>
> reviewed: false (리뷰 증거 파일 생성 전까지 절대 true로 변경 불가)<br>
> **usability_review_required:** true<br>
> **protected_change:** true<br>
> user_request: 계획과 리뷰에 과도하게 결합된 manifest 기능과 전용 권한 게이트를 제거하고 일반 계획 리뷰만 유지한다.<br>
> active_agent: codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: chore/remove-manifest-governance)<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 각 단계를 해당 검증이 PASS한 뒤에만 완료로 표시한다.

**목표:** 계획·리뷰 흐름에서 `sync-manifest`, manifest 목록 파일, `harness-architect` 전용 승인 경로를 제거하고 `plan-reviewer`와 `principle-auditor` 중심의 단순한 일반 리뷰 계약으로 전환한다.

**사용자 결과 요약:** 사용자는 일반 기능 계획을 작성할 때 manifest 명령, `_version.json`, 별도 architect 승인 때문에 반복 차단되지 않으며, 계획의 실행 가능성·원칙 정합성·검증 가능성만 일반 reviewer가 판단하는 흐름을 사용한다. 과거 archive 기록은 보존하고, 제품 런타임 동작과 일반 reviewer 자체는 바뀌지 않는다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 네트워크, credential): 없음
- 내부 선행 조건: 현재 active 계획의 manifest·architect 승인 참조를 식별하고, 삭제 전 일반 reviewer 계약의 최소 검증을 고정한다.
- 구현 중 필요한 기존 명령: `pytest`, Bash, `plan_lifecycle.py`, public verifier.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, Intent Sheet, `HISTORY.md`, `.agentos/project/exec-plans/evolution-status.md`
- Durable Result Surface: `AGENTS.md`, `.agents/skills/harness/writing-plans/`, `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, catalog·검증 문서·테스트
- documentation-only exception: 없음. 계획 문서 변경은 실제 리뷰·검증 동작을 단순화하는 구현과 함께 적용한다.

**진행 상태:** 계획 초안 작성, 구현 전 Gate 2 리뷰 대기 중

**아키텍처:**
- 삭제 대상은 자산 목록 동기화 계층(`sync-manifest`, 세 `_version.json`)과 그 계층에 의존하는 `harness-architect` 권한·protected approval 경로다.
- 유지 대상은 `plan-reviewer`, `principle-auditor`, 필요한 user-facing 계획의 `usability-reviewer`, 기존 lifecycle·public verifier다.
- archive 문서는 당시의 역사적 검증 증거이므로 수정하지 않고, 현재 active 계획의 실행 불가능한 참조만 새 계약에 맞게 마이그레이션한다.

**기술 스택:** Markdown, JSON, Bash, Python 3.11+ 표준 라이브러리, pytest, 기존 lifecycle/public verifier

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | Intent Sheet와 실행 계획 초안 작성 완료; 구현하지 않음 |
| 완료됨 | `main`과 동기화된 feature branch 생성, manifest·권한·리뷰 참조 인벤토리 확인 |
| 현재 위치 | `plan-reviewer`·`principle-auditor`의 독립 Gate 2 검토 대기 |
| 다음 단계 | 현행 계약의 독립 Gate 2·usability·architect 승인과 사전 manifest 검증을 통과한 뒤 삭제·계약 정리를 구현 |
| 완료 신호 | 삭제 대상이 사라지고 일반 reviewer 테스트·하네스·public verifier가 모두 PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 삭제 범위 고정 | 어떤 manifest·권한·리뷰 게이트를 없애고 무엇을 유지하는지 확인 | Intent Sheet, 이 계획의 보호 변경 범위 | `rg` 인벤토리 PASS |
| 2. 일반 리뷰 계약으로 전환 | 계획이 manifest나 architect 승인 없이 일반 reviewer 검토를 받을 수 있음 | `review_artifacts.py`, `plan-reviewer.md`, `principle-auditor.md`, TEMPLATE/SKILL | focused reviewer tests PASS |
| 3. 잔여 참조 정리 | 사용자가 삭제된 명령·파일을 다시 안내받지 않음 | AGENTS, catalog, README, run-all-tests, active plan migration | active-surface `rg` PASS |
| 4. 전체 검증 | 삭제 후에도 일반 하네스와 public verifier가 작동함 | tests, harness verifier, public verifier | `PASS agentos-public-suite` 및 exit 0 |

## 리뷰 반영 이력

- 계획 작성 전 원칙 판단: manifest 전체 삭제는 가능하지만 일반 reviewer를 유지해야 하며, archive 기록은 보존해야 한다.
- 2026-09-05 독립 `plan-reviewer` triage FAIL 반영: 이 계획은 protected/core·checker/bootstrap·operator-facing surface를 함께 변경한다. 현행 계약의 `plan-reviewer → principle-auditor → usability-reviewer → harness-architect → plan-reviewer final` 순서와 fresh artifact를 먼저 확보한다.
- Task 0의 baseline은 계획·Intent·생성 board와 Gate 2 증거를 허용하는 명시적 planning baseline으로 검증한다. clean checkout을 허위로 주장하지 않는다.
- migration plan 자신의 과거/전환 서술은 역사적 trace로 보존하므로, active-plan dead-reference 검증은 이 계획을 제외한 active plan에 한정한다.

## 사전 실행 Gate와 closeout 경계

- 이 계획은 `.agents/` 보호 표면을 정리하므로, 삭제 전 현행 계약의 `plan-reviewer`, `principle-auditor`, `usability-reviewer`, 독립 `harness-architect` 승인과 semantic snapshot을 확보한다.
- 현행 manifest 계약은 삭제 전에 `sync-manifest --check` 및 `sync-manifest --update`로 기준 상태를 검증한다. 삭제 후에는 일반 reviewer·harness·public verifier로 새 계약을 검증하며, 삭제된 명령을 다시 호출하지 않는다.
- Task 안에 reviewer artifact self-signing이나 완료 선언을 넣지 않는다. 구현 후 closeout에서 fresh focused/full/public 검증과 lifecycle refresh를 수행한다.
- Bootstrap Safety: 삭제 후의 새 reviewer 계약을 삭제 전 사전 게이트에서 요구하지 않는다. 현재 계획 형식과 현재 reviewer 계약을 먼저 확인하고, 새 일반 계약은 구현 후 검증한다.

## 보호 변경 범위

- declared protected paths: `AGENTS.md`, `.agents/agents/README.md`, `.agents/agents/harness/harness-architect.md`, `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, `.agents/agents/harness/usability-reviewer.md`, `.agents/agents/harness/_version.json`, `.agents/_version.json`, `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/README.md`, `.agents/skills/harness/SKILL.md`, `.agents/skills/harness/_version.json`, `.agents/skills/harness/sync-manifest/**`, `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `.agents/skills/harness/run-all-tests/tests/run_all_tests.sh`, `.agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh`, `.agents/skills/harness/run-all-tests/tests/test_plan_reader_first_contract.py`, `catalog/skills/catalog.json`, `manifest update`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/exec-plans/active/2026-09-04-plan-frontmatter.md`, `.agentos/project/exec-plans/active/2026-09-04-plan-reviewer-orchestrator.md`
- required approval: 전환 전 이 계획의 독립 `plan-reviewer`·`principle-auditor`·`usability-reviewer` PASS와 현행 `harness-architect` 승인; 전환 후 active plan은 일반 reviewer 계약으로 재리뷰한다.
- migration rule: archive 계획·HISTORY·기존 trace는 historical evidence로 보존하고, active plan은 삭제된 게이트를 더 이상 요구하지 않도록 별도 semantic re-review를 거친다.

## 파일 구조

- 삭제: `.agents/skills/harness/sync-manifest/` — manifest skill과 sync script
- 삭제: `.agents/_version.json`, `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json` — manifest·architect 권한 목록
- 삭제: `.agents/agents/harness/harness-architect.md` — manifest 전용 architect role
- 삭제: `catalog/agents/harness-architect/AGENT.md`, `catalog/agents/harness-architect/` — discoverable architect catalog wrapper
- 수정: `AGENTS.md` — 전역 sync-manifest 강제와 architect 승인 문구 제거
- 수정: `.agents/agents/README.md`, `.agents/skills/README.md`, `.agents/skills/harness/SKILL.md`, `catalog/agents/catalog.json`, `catalog/skills/catalog.json` — 삭제된 자산의 discovery entry 제거
- 수정: `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md` — 일반 reviewer 범위로 축소
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/executing-plans/SKILL.md`, `.agents/skills/harness/principle-auditor/SKILL.md`, `.agents/skills/harness/core-engine/harness_loop.py`, `.agents/skills/harness/core-engine/commands/harness-loop.md`, `.agents/skills/harness/brain/resources/skill-routing.md`, `.agentos/project/exec-plans/TEMPLATE.md` — manifest/protected approval 필수 조건 제거
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py` — architect approval·protected manifest scope 제거 및 일반 reviewer 테스트 유지
- 수정: `.agents/skills/harness/run-all-tests/tests/run_all_tests.sh`, `.agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh`, `.agents/skills/harness/run-all-tests/tests/test_harness_loop.py` — manifest 검사와 harness-architect 계약 제거
- 수정: `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md` — 삭제된 manifest·승인 모델을 현재 시스템 계약에서 제거
- 수정: 현재 active 계획 두 건 — 삭제된 manifest/architect 게이트를 요구하지 않도록 migration 후 semantic re-review
- 보존: `.agentos/project/exec-plans/archive/**`, `.agents/traces/**`, `HISTORY.md`의 과거 manifest 검증 기록

## Task 0: 삭제 전 기준과 현재 계획 경계를 고정한다

**파일:**
- 읽기: `AGENTS.md`, `.agentos/project/00-project-index.md`, `CONTRIBUTING.md`, 현재 active 계획, manifest 관련 모든 source/test/catalog
- 수정: 이 계획의 리뷰 반영 이력과 진행 스냅샷만 필요 시 갱신

**사용자에게 보이는 마일스톤:** 삭제 대상과 보존 대상이 구현 전에 재현 가능하게 확인된다.

- [ ] **Step 0.1: 작업 브랜치와 허용된 planning baseline을 확인한다.**

Run: `test "$(git branch --show-current)" = "chore/remove-manifest-governance" && ! git status --porcelain | grep -vE '^( M|\?\?) (\.agentos/project/exec-plans/README\.md|\.agentos/project/exec-plans/active/2026-09-05-remove-manifest-governance\.md|\.agentos/project/exec-plans/archive/reference/intent/intent-20260905-remove-manifest-governance\.md|\.agents/traces/)' | grep -q . && echo PASS plan-branch-planning-baseline`
Expected: `PASS plan-branch-planning-baseline`

- [ ] **Step 0.1a: 현행 protected 계약의 manifest 기준을 검증한다.**

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: 세 명령이 모두 exit 0이며, 삭제 전 manifest 기준 상태가 기록된다.

- [ ] **Step 0.2: 현재 운영 surface의 삭제 대상 참조를 기록한다.**

Run: `rg -n "sync-manifest|manifest update|authorized_architects|harness-architect|protected_change" AGENTS.md .agents/agents .agents/skills/harness catalog/skills/catalog.json .agentos/project/03-system-contract.md .agentos/project/04-safety-risk-verification.md --glob '!**/archive/**' --glob '!**/traces/**' || true`
Expected: 구현 전 baseline 참조 목록이 출력되고, archive/HISTORY를 제외한 활성 surface가 범위에 포함된다.

## Task 1: manifest 자산과 전용 권한 source를 제거한다

**파일:**
- 삭제: `.agents/skills/harness/sync-manifest/`
- 삭제: `.agents/_version.json`, `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json`
- 삭제: `.agents/agents/harness/harness-architect.md`

**사용자에게 보이는 마일스톤:** 더 이상 manifest 명령, manifest 목록, manifest 전용 architect role이 설치·발견되지 않는다.

- [ ] **Step 1.1: manifest 자산과 권한 registry를 제거한다.**

삭제는 위에 선언된 exact path에만 적용한다. archive 기록과 unrelated `_version`·package metadata는 삭제하지 않는다.

Run: `test ! -e .agents/skills/harness/sync-manifest && test ! -e .agents/_version.json && test ! -e .agents/agents/harness/_version.json && test ! -e .agents/skills/harness/_version.json && test ! -e .agents/agents/harness/harness-architect.md && echo PASS manifest-assets-removed`
Expected: `PASS manifest-assets-removed`

## Task 2: 일반 계획 리뷰 계약으로 단순화한다

**파일:**
- 수정: `AGENTS.md`, `.agentos/project/exec-plans/TEMPLATE.md`, `.agents/skills/harness/writing-plans/SKILL.md`
- 수정: `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`

**사용자에게 보이는 마일스톤:** 일반 계획은 `plan-reviewer`와 `principle-auditor` 리뷰만으로 실행 가능성을 판정하고, manifest·architect approval을 요구받지 않는다.

- [ ] **Step 2.1: policy와 plan template에서 manifest·전용 architect 의무를 제거한다.**

`AGENTS.md`의 전역 sync-manifest 강제와 Skill patch 승인 흐름, TEMPLATE/SKILL·실행/loop/principle 안내의 `protected_change`·authorized architect·manifest 필수 문구를 제거하거나 일반 reviewer 규칙으로 치환한다. 일반 계획은 `plan-reviewer`와 `principle-auditor` PASS만 요구하며, `usability_review_required: true`인 user/operator-facing 계획은 독립 `usability-reviewer` PASS를 계속 요구한다. TEMPLATE과 writing-plans operator 안내에 이 조건을 명시한다.

Run: `if rg -n "sync-manifest|authorized_architects|harness-architect|manifest update|protected_change" AGENTS.md .agentos/project/exec-plans/TEMPLATE.md .agents/skills/harness/writing-plans/SKILL.md; then exit 1; else echo PASS policy-reference-free; fi`
Expected: `PASS policy-reference-free`가 출력되고, `plan-reviewer`·`principle-auditor` 일반 Gate 2 안내는 남아 있다.

- [ ] **Step 2.2: review artifact checker를 일반 reviewer 전용으로 축소한다.**

`PROTECTED_REVIEW_SCOPE`, `harness-architect-approval`, `_version.json` 권한 조회, `manifest update` pseudo-path, `protected_change`에 따른 별도 승인 분기를 제거한다. semantic snapshot, reviewer 분리, PASS/CLEAN, stale artifact 검사는 유지한다. 테스트는 non-user-facing 계획이 두 일반 reviewer만 요구하는 경우와 `usability_review_required: true` 계획이 usability evidence 없이는 FAIL하는 경우를 모두 고정한다.

Run: `pytest .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q`
Expected: 일반 reviewer 계약 테스트가 모두 PASS하고, 삭제된 architect approval fixture는 더 이상 요구되지 않는다.

## Task 3: discovery·검증·현재 active 계획의 죽은 참조를 정리한다

**파일:**
- 삭제: `catalog/agents/harness-architect/AGENT.md`, `catalog/agents/harness-architect/`
- 수정: `.agents/agents/README.md`, `.agents/skills/README.md`, `.agents/skills/harness/SKILL.md`, `catalog/agents/catalog.json`, `catalog/skills/catalog.json`
- 수정: `.agents/skills/harness/executing-plans/SKILL.md`, `.agents/skills/harness/principle-auditor/SKILL.md`, `.agents/skills/harness/core-engine/harness_loop.py`, `.agents/skills/harness/core-engine/commands/harness-loop.md`, `.agents/skills/harness/brain/resources/skill-routing.md`
- 수정: `.agents/skills/harness/run-all-tests/tests/run_all_tests.sh`, `.agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh`, `.agents/skills/harness/run-all-tests/tests/test_harness_loop.py`
- 수정: `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`
- 수정: `.agentos/project/exec-plans/active/2026-09-04-plan-frontmatter.md`, `.agentos/project/exec-plans/active/2026-09-04-plan-reviewer-orchestrator.md`
- 보존: `.agentos/project/exec-plans/archive/**`, `HISTORY.md`, `.agents/traces/**`

**사용자에게 보이는 마일스톤:** 삭제된 기능이 README·catalog·테스트·현재 계획에서 다시 요구되지 않는다.

- [ ] **Step 3.1: discovery와 catalog에서 삭제된 자산을 제거한다.**

`sync-manifest` skill과 source·catalog의 `harness-architect` entry를 제거하고, harness root 안내와 core asset 목록을 현재 구성과 맞춘다.

Run: `! rg -n "sync-manifest|harness-architect" .agents/agents/README.md .agents/skills/README.md .agents/skills/harness/SKILL.md catalog/agents/catalog.json catalog/skills/catalog.json && test ! -e catalog/agents/harness-architect && echo PASS discovery-clean`
Expected: `PASS discovery-clean`

- [ ] **Step 3.2: 전체 harness 실행기와 계약 테스트에서 manifest 단계를 제거한다.**

초기 manifest integrity stage와 architect-specific grep assertion을 제거하고, 실행·loop·principle·routing source 및 loop 테스트의 live governance reference도 일반 reviewer 계약으로 정리한다. `brain/bugs/**`의 historical incident 기록은 수정하지 않으며 이 live-surface 검증에서 제외한다.

Run: `! rg -n "sync-manifest|harness-architect|authorized_architects|protected_change" .agents/skills/harness/executing-plans/SKILL.md .agents/skills/harness/principle-auditor/SKILL.md .agents/skills/harness/core-engine/harness_loop.py .agents/skills/harness/core-engine/commands/harness-loop.md .agents/skills/harness/brain/resources/skill-routing.md .agents/skills/harness/run-all-tests/tests/run_all_tests.sh .agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh .agents/skills/harness/run-all-tests/tests/test_harness_loop.py && echo PASS harness-live-contract-clean`
Expected: `PASS harness-live-contract-clean`

- [ ] **Step 3.3: 현재 active 계획을 새 일반 리뷰 계약으로 마이그레이션한다.**

두 active plan에서 manifest·architect approval·`_version.json`·protected pseudo-path에 의존하는 Step과 검증을 제거한다. 각 계획의 목표·Task·검증 의미가 바뀌므로 migration 후 일반 Gate 2를 새 semantic snapshot으로 재실행한다. archive 계획은 역사 보존을 위해 건드리지 않는다.

Run: `if rg -n "sync-manifest|manifest update|authorized_architects|harness-architect|_version\.json" .agentos/project/exec-plans/active --glob '*.md' --glob '!2026-09-05-remove-manifest-governance.md'; then exit 1; else echo PASS active-plan-reference-free; fi`
Expected: `PASS active-plan-reference-free`가 출력되고, 이 migration plan을 제외한 active plan의 일반 reviewer와 lifecycle 검증 경계는 남아 있다.

## Task 4: 삭제 후 일반 리뷰·하네스·public 경계를 검증한다

**파일:**
- 검증: `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `.agents/skills/harness/run-all-tests/tests/`, `scripts/verify-public-test-suite.sh`
- 갱신: `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, `.agentos/project/exec-plans/evolution-status.md` — 공식 lifecycle 명령으로만

**사용자에게 보이는 마일스톤:** manifest 없이도 계획을 리뷰·검증하고 현재 상태를 재현할 수 있다.

- [ ] **Step 4.1: active surface에 삭제 대상 참조가 없는지 검증한다.**

Run: `if rg -n "sync-manifest|manifest update|authorized_architects|harness-architect|protected_change" AGENTS.md .agents/agents .agents/skills/harness catalog/agents/catalog.json catalog/skills/catalog.json .agentos/project/03-system-contract.md .agentos/project/04-safety-risk-verification.md .agentos/project/exec-plans/active --glob '!**/archive/**' --glob '!**/traces/**' --glob '!brain/bugs/**' --glob '!2026-09-05-remove-manifest-governance.md'; then exit 1; else echo PASS active-surface-reference-free; fi`
Expected: `PASS active-surface-reference-free`가 출력되고, 이 migration plan·archive·HISTORY·trace에만 역사적 참조가 남는다.

- [ ] **Step 4.2: 일반 reviewer와 전체 harness 계약을 검증한다.**

Run: `pytest .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q && bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`
Expected: focused reviewer tests와 full harness verifier가 모두 exit 0이다.

- [ ] **Step 4.3: public boundary와 lifecycle을 검증한다.**

Run: `bash scripts/verify-public-test-suite.sh && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && git diff --check`
Expected: `PASS agentos-public-suite`, lifecycle refresh exit 0, `git diff --check` exit 0이다.

## 의존성 분석

- 외부 서비스·API·토큰·credential은 사용하지 않는다.
- `pytest`, Bash, `python3`, 기존 public verifier와 lifecycle script만 사용한다.
- 삭제 후에는 `sync-manifest` 명령을 검증 명령으로 호출하지 않는다. 그것이 삭제 성공 조건이다.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 아카이브 결정

(구현·검증·일반 Gate 2 closeout 후 사용자가 archive 여부를 결정)
