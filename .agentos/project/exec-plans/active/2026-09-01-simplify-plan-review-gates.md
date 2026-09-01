# 계획 리뷰 게이트 단순화 및 반복 block 제거 구현 계획

> **상태:** 중단됨 — stop/PostToolUse 훅 삭제로 원래 구현 대상이 제거됨<br>
> **작성일:** 2026-09-01<br>
> reviewed: false<br>
> **usability_review_required:** true<br>
> **protected_change:** true<br>
> user_request: 계획 리뷰가 반복적으로 block 되는 근본 원인을 제거하고, 복잡하고 과도하게 강제되는 리뷰 구조를 최소 안전 게이트로 단순화한다.<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: (agentos dashboard sync-plan 실행 시 자동 기록됨)<br>

> **에이전트 작업자용:** 이 문서는 정책·훅·리뷰 lifecycle을 바꾸는 계획이다. Gate 2 합의와 protected architect 승인이 끝나기 전에는 구현 Task를 실행하지 않는다.

**목표:** 무관한 계획의 stale review evidence가 현재 세션을 막지 않게 하고, 변경 위험에 맞는 최소 reviewer만 요구하도록 계획 리뷰를 단순화한다.

**사용자 결과:** 사용자는 초안 계획을 저장하고 필요한 reviewer만 거쳐 실행 대기로 전환할 수 있으며, block 시에는 대상 계획과 다음 복구 명령을 명확히 알 수 있다.

**진행 상태:** 2026-09-02에 stop/PostToolUse 훅이 제거되어 이 계획의 Task 1은 더 이상 실행하지 않는다. 이 문서는 명시적 archive 결정 전까지 변경 이력으로만 보존한다.

**아키텍처:** 계획 작성은 `reviewed: false` 상태로 자유롭게 진행한다. 계획 실행 직전에 대상 계획 하나의 semantic review evidence만 검사하고, 일반 계획·user-facing 계획·protected harness 계획의 reviewer 요구를 분리한다. Stop 훅은 전역 plan registry 감시자가 아니라 현재 completion 흐름의 안전 보조자로 남긴다.

**기술 스택:** Python 3, Bash, Markdown, pytest, 기존 AgentOS harness lifecycle scripts

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 초안 / 리뷰 대기 |
| 완료됨 | AGENTS 규칙, 최근 LOOP_STOP/RCA, Stop 훅, validator, template, reviewer 계약 조사 |
| 현재 위치 | 독립 Gate 2 리뷰와 protected architect 확인 전 |
| 다음 단계 | 최소 reviewer 정책과 전역 block 범위를 구현하고 회귀 검증 |
| 완료 신호 | 대상 plan만 검사하는 focused tests, public verifier, manifest check가 모두 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 작은 계획은 한 명의 독립 reviewer로 실행 대기 전환되고, 복잡한 reviewer는 실제 위험이 있을 때만 추가된다. |
| 누구를 위한 것인가? | 계획을 작성·리뷰·실행하는 개발자와 하네스 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 다른 계획의 오래된 evidence 때문에 현재 작업이 멈추지 않으며, 오류 메시지가 대상 plan과 복구 행동을 가리킨다. |
| 무엇은 바뀌지 않는가? | 작성자 자기승인 금지, protected `.agents/` 변경의 구조 감사·manifest, secret/prompt 경계, 실행 전 유효성 검사는 유지한다. |

## 사용자 작업 흐름과 복구

1. 계획을 `reviewed: false`로 저장한다.
2. 일반 계획은 `plan-reviewer`, user-facing 변경은 여기에 `usability-reviewer`, `.agents/`·보안·핵심 runtime 변경은 여기에 `principle-auditor`를 추가한다.
3. `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan <plan-path> --json`으로 필요한 reviewer와 원인을 확인한다. parser는 header의 `protected_change`와 `usability_review_required`를 읽고, protected path가 선언되거나 감지되면 `principle-auditor`를 누락할 수 없도록 fail-closed로 동작한다.
4. `FAIL missing=...`이면 표시된 reviewer만 재요청하고, `semantic-snapshot-mismatch`이면 계획 본문을 확정한 뒤 해당 reviewer만 재검토한다.
5. reviewer가 모두 PASS이면 `python3 .agents/skills/harness/writing-plans/scripts/request_review.py <plan-path>`를 실행한다. protected 변경이면 architect 승인과 manifest check를 추가한다.
6. 성공 신호는 `PASS gate2-review-check reviewers=...`이며, 그 뒤에만 `reviewed: true`로 전환한다.

protected 변경의 승인 경로는 `.agents/traces/reviews/2026-09-01-simplify-plan-review-gates/harness-architect-approval.json`에 기록한다. 이 artifact는 `harness-architect-approval-v1`, 정확한 `plan_path`와 semantic `plan_sha256`, `reviewer_id=harness-architect`, `decision=APPROVED`, `authorized_scope`, `approved_at`, `summary`를 포함해야 한다. 구현자는 이 파일을 만들거나 서명하지 않으며, 다음 검증이 실패하면 protected mutation과 `reviewed: true` 전환을 중단한다:

`python3 - <<'PY'\nimport json, sys\nfrom pathlib import Path\nsys.path.insert(0, '.agents/skills/harness/writing-plans/scripts')\nfrom review_artifacts import plan_hash\nplan=Path('.agentos/project/exec-plans/active/2026-09-01-simplify-plan-review-gates.md')\na=json.loads(Path('.agents/traces/reviews/2026-09-01-simplify-plan-review-gates/harness-architect-approval.json').read_text())\nassert a['schema']=='harness-architect-approval-v1' and a['plan_path']==plan.as_posix() and a['plan_sha256']==plan_hash(plan.read_text(encoding='utf-8')) and a['reviewer_id']=='harness-architect' and a['decision']=='APPROVED' and a['authorized_scope']\nprint('PASS protected-architect-approval')\nPY`

승인 누락·불일치 시에는 `harness-architect`에게 다음 정보를 포함한 review handoff를 전달한다: `plan_path`, 이 계획의 semantic hash, 그리고 `## 보호 변경 범위`의 전체 목록. architect가 승인 artifact를 발행한 뒤 위 검증 명령과 Gate 2 check를 재실행한다. architect 승인 전에는 어떤 protected 파일도 수정하지 않는다.

block 메시지는 `대상 계획: <path> / 원인: <reason> / 다음 명령: <exact command> / 성공 신호: <expected output>` 형식으로 출력한다. 현재 계획이 없으면 전역 active plan을 차단하지 않고 대상 계획 지정 경고만 출력한다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. block 원인 재현 | 현재 plan과 무관한 stale plan이 Stop을 전역 차단하지 않는 기준이 명확해짐 | `.agents/hooks/scripts/stop_review_gate.py` 및 회귀 테스트 | `pytest ... -q` → `PASS` |
| 2. 최소 reviewer 정책 적용 | 일반/user-facing/protected 계획이 필요한 reviewer만 요구함 | `review_artifacts.py`, `request_review.py`, reviewer 계약·TEMPLATE | `pytest ... -q` → `PASS` |
| 3. lifecycle 정합성 회복 | 계획 작성·리뷰·실행·새 세션 복구가 같은 상태를 사용함 | `writing-plans/SKILL.md`, `executing-plans/SKILL.md`, lifecycle scripts | harness/public verifier → `PASS` |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, `.agents/traces/reviews/<plan>/`, `.agentos/project/exec-plans/evolution-status.md`
- durable result surface: `.agents/hooks/scripts/stop_review_gate.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, 관련 lifecycle 문서·테스트·reviewer 계약
- documentation-only exception: 없음. 훅과 validator 동작을 실제로 변경한다.
- 위 reader-first 문구와 계획 데이터는 presentation/data이며 `AGENTS.md`, vendor guide, protected-path rules, reviewer authority를 override하지 않는다.

## 범위 및 원인 분석

### 확인된 근본 원인

- Stop 훅의 `_invalid_reviewed_plan()`이 active 디렉터리의 모든 `reviewed: true` plan을 순회하여 현재 작업과 무관한 invalid evidence도 전역 block으로 만든다.
- 일반 계획에 `plan-reviewer`와 `principle-auditor`를 항상 요구하고, user-facing이면 `usability-reviewer`, 별도 Markdown audit trace, HMAC signing까지 결합한다.
- `reviewed` 상태를 header, validator, lifecycle, stop hook, loop engine이 각각 판단해 초안 저장·리뷰 대기·실행 대기의 경계가 중복된다.
- 최근 HISTORY의 `active-plan-gate2-approval-blocker`, `review-artifact-wrong-workdir`, `unified-hook-audit-scope-blocker`가 이 결합이 반복 blocker로 관측됐음을 보여준다.

### 최소화 원칙

- 보존: 대상 plan의 실행 전 validity, 독립성·작성자 분리, protected harness/security 변경의 principle audit, user-facing 변경의 usability 검토, secret/prompt 경계, manifest.
- 축소: 무관한 active plan에 대한 Stop 전역 block, 일반 계획의 상시 principle audit, 별도 audit Markdown 파일을 필수 증거로 중복 요구, 계획 초안 저장과 실행 승인 판정의 결합.
- 금지: 리뷰를 우회하는 blanket allow, self-certification, protected path 무승인 변경, raw secret·환경값 출력.

### 상태의 단일 소유권

- canonical state: active plan의 `reviewed`/lifecycle metadata와 role별 `.agents/traces/reviews/<plan-slug>/{plan-reviewer,principle-auditor,usability-reviewer}.json` 세트가 현재 판정을 소유한다. 각 파일은 `gate2-review-artifact-v1`이며 role별 누락·invalid가 하나라도 있으면 전체 gate는 invalid다.
- registry/cache: `.agents/mission/plan.json`과 `exec-plans/README.md`는 filesystem에서 재생성되는 표시용 registry이며, review 판정을 독립적으로 만들지 않는다.
- audit: HMAC/signature와 trace는 protected 변경의 감사 증거로만 사용하며 일반 plan의 실행 조건이 아니다.
- history: `HISTORY.md`와 evolution status는 사건·결정 기록이며 현재 plan validity를 override하지 않는다.
- migration: active plan만 parser metadata와 protected-path detection으로 strict하게 검사하고, archive evidence는 historical 표시로만 읽는다. `protected_change=true` 또는 declared protected path가 있으면 principle-auditor artifact가 없을 때 non-zero/invalid이며, metadata를 삭제·변조해도 protected scope 검사가 이를 다시 감지한다.

## File Structure

- 수정: `.agents/hooks/scripts/stop_review_gate.py` — 현재 completion/대상 plan 범위만 차단하고 무관한 stale plan은 진단으로 남긴다.
- 수정: `.agents/hooks/scripts/post_tool_use_review.py` — 의도적인 review 진단 실패를 세션 전역 block으로 승격하지 않는다.
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py` — reviewer 요구를 변경 유형 메타데이터로 계산하고 단일 JSON artifact 검증을 유지한다.
- 수정: `.agents/hooks/scripts/check-alignment.py` — 동일 semantic snapshot을 사용하고 archive를 현재 active gate처럼 검사하지 않는다.
- 수정: `.agents/skills/harness/writing-plans/scripts/request_review.py` — 선택 reviewer와 protected signing 경계를 정합화한다.
- 수정: `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py` — read-only 상태 확인과 명시적 registry write를 분리한다.
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/executing-plans/SKILL.md`, `.agentos/project/exec-plans/TEMPLATE.md` — 상태와 복구 흐름을 단순한 규칙으로 통일한다.
- 수정: `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, `.agents/agents/harness/usability-reviewer.md` — 각 reviewer의 적용 조건과 비차단 wording 범위를 맞춘다.
- 생성/수정: `.agents/skills/harness/writing-plans/tests/`, `.agents/skills/harness/run-all-tests/tests/` — stale plan isolation, reviewer matrix, 초안 저장, security regression을 검증한다.
- 수정: `AGENTS.md`, `HISTORY.md`, `.agentos/project/06-decisions-change-log.md`, `.agentos/project/exec-plans/evolution-status.md` — 승인된 정책 변화와 RCA를 기록한다.

## Task 0: 기준선과 보호 범위 고정

**파일:**
- 읽기: `AGENTS.md`, `CONTRIBUTING.md`, `.agents/_version.json`, 현재 hooks/lifecycle/test 파일
- 수정 없음

**사용자에게 보이는 마일스톤:** 어떤 plan이 block 대상인지와 기존 baseline 실패가 분리되어 기록된다.

- [ ] **Step 1: 저장소 root·브랜치·변경 파일과 architect 권한을 확인한다.**

Run: `root="$(git rev-parse --show-toplevel)"; test "$root" = "$PWD"; test "$(git branch --show-current)" = "fix/simplify-plan-review-gates"; python3 - <<'PY'\nimport json\nfrom pathlib import Path\ndata=json.loads(Path('.agents/_version.json').read_text())\nassert 'codex' in data['authorized_architects']\nprint('PASS protected-architect-authorized')\nPY`
Expected: `PASS protected-architect-authorized`

- [ ] **Step 2: 현재 focused baseline을 실행하고 실패는 기존 baseline으로 보존한다.**

Run: `set +e; bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh; rc=$?; printf 'BASELINE_EXIT=%s\\n' "$rc"; echo 'PASS baseline-captured'; exit 0`
Expected: `BASELINE_EXIT=<실측값>`과 `PASS baseline-captured`가 출력되고 원래 suite 결과가 숨겨지지 않는다.

## Task 1: 전역 hook block을 대상 plan 범위로 축소

**파일:**
- 수정: `.agents/hooks/scripts/stop_review_gate.py`
- 수정: `.agents/hooks/scripts/post_tool_use_review.py`
- 읽기 전용: `.agents/hooks/adapters/codex/hooks.json` — 대상 plan context의 canonical key를 확인한다. 이 계획에서는 변경하지 않는다.
- 생성/수정: `.agents/skills/harness/writing-plans/tests/test_stop_review_gate.py`, `.agents/skills/harness/run-all-tests/tests/harness/test_stop_review_gate_contract.sh`

**사용자에게 보이는 마일스톤:** 무관한 invalid active plan이 현재 세션을 멈추지 않고, 현재 대상 plan이 실제 실행/완료 흐름에서 invalid일 때만 복구 안내가 나온다.

- [ ] **Step 1: 현재 plan 식별 입력과 차단 조건을 구현한다.** 대상 plan context가 없으면 전역 active plan 순회를 차단 사유로 사용하지 않고 `continue` 또는 비차단 진단으로 처리한다.

Run: `pytest .agents/skills/harness/writing-plans/tests -q -k 'stop or hook'`
Expected: exit 0 및 `passed` 출력; stale unrelated plan isolation 회귀 테스트 포함.

- [ ] **Step 2: completion claim, loop lock, dirty-worktree verification 같은 기존 안전 검사를 유지한다.**

대상 plan의 변경 파일과 검증 결과가 불일치할 때만 차단하고, `docs/knowledge-agent`·`.venv/`처럼 무관한 dirty 파일은 경고만 출력한다.

Run: `pytest .agents/skills/harness/run-all-tests/tests -q -k 'hook or loop_state'`
Expected: exit 0 및 `passed` 출력.

- [ ] **Step 3: review 진단 명령의 예상 `FAIL`을 일반 Bash 실패와 분리한다.** `review_artifacts.py check`와 review 상태 조회는 context 경고로 남기되, 실제 위험한 mutation/completion 검사는 계속 차단한다.

Run: `pytest .agents/skills/harness/run-all-tests/tests -q -k 'post_tool or review_command'`
Expected: exit 0 및 `passed` 출력; review 진단 실패 fixture의 `decision`은 `block`이 아님.

## Task 2: reviewer matrix를 위험·변경 유형별 최소 게이트로 통합

**파일:**
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/scripts/request_review.py`
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/executing-plans/SKILL.md`, `.agentos/project/exec-plans/TEMPLATE.md`
- 생성/수정: `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `.agents/skills/harness/writing-plans/tests/test_request_review.py`, `.agents/skills/harness/run-all-tests/tests/harness/test_review_matrix_contract.sh`

**사용자에게 보이는 마일스톤:** 일반 계획은 `plan-reviewer`만, user-facing 계획은 usability reviewer를 추가하고, `.agents/` 보호 변경만 principle audit을 추가한다.

- [ ] **Step 1: `protected_change`, `usability_review_required`, 일반 plan metadata에 따른 reviewer matrix를 정의한다.** 초안은 `reviewed: false`로 저장 가능하고, 실행 승인 시에만 matrix를 검사한다.

Run: `pytest .agents/skills/harness/writing-plans/tests -q -k 'review_scope or reviewer or metadata'`
Expected: exit 0 및 `passed`; 일반/user-facing/protected 조합, `reviewed:false` 초안 저장, protected reviewer omission/tampering의 invalid/non-zero fixture가 모두 통과.

- [ ] **Step 2: 별도 Markdown audit trace를 필수 Gate 2 증거로 중복 요구하지 않고, JSON artifact의 identity/scope/revision/independence를 단일 증거로 유지한다.** protected signing은 보호 변경에만 남긴다.

Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-01-simplify-plan-review-gates.md --json`
Expected: JSON의 `valid`가 `false`이고 `missing`에 필요한 최소 reviewer만 포함되며 진단 모드는 계약된 exit 0으로 종료한다.

- [ ] **Step 3: `check-alignment.py`와 `review_artifacts.py`가 같은 semantic snapshot을 사용하고, archive plan은 historical metadata로만 표시되도록 통합한다.**

Run: `pytest .agents/skills/harness/writing-plans/tests .agents/skills/harness/run-all-tests/tests -q -k 'alignment or archive or semantic_snapshot'`
Expected: `PASS` — 두 판정 경로의 snapshot 결과와 active/archive 상태 분리가 통과.

- [ ] **Step 4: `request_review.py`의 review record와 protected signing을 별도 동작으로 명확히 하고, 일반 계획에는 HMAC signing을 요구하지 않는다.**

Run: `pytest .agents/skills/harness/writing-plans/tests .agents/skills/harness/run-all-tests/tests -q -k 'request_review or signature or protected'`
Expected: `PASS` — 일반 plan은 record/check로 완료되고 protected plan만 signing gate를 요구.

## Task 3: reviewer 문서와 복구 메시지 정합화

**파일:**
- 수정: `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, `.agents/agents/harness/usability-reviewer.md`
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`, `AGENTS.md`, `.agents/hooks/README.md`
- 수정: `.agents/skills/harness/run-all-tests/tests/harness/test_review_error_recovery_contract.sh`

**사용자에게 보이는 마일스톤:** block 메시지가 “무엇이 잘못됐는지, 어느 plan인지, 다음에 어떤 명령을 실행할지”만 안내하며 cosmetic wording을 block하지 않는다.

- [ ] **Step 1: reviewer 적용 조건·non-blocking finding·복구 명령을 문서와 오류 출력에 동일하게 반영한다.**

Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_user_facing_terminology_clarity_contract.sh && bash .agents/skills/harness/run-all-tests/tests/harness/test_safety_security_prompt_contract.sh`
Expected: `PASS` 두 계약 테스트.

- [ ] **Step 1a: plan text·tool output이 instruction이 아니라 data로 처리되고, secret sentinel과 prompt-injection 문구가 출력·artifact에 남지 않는 회귀 테스트를 추가한다.**

Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_safety_security_prompt_contract.sh && pytest .agents/skills/harness/run-all-tests/tests -q -k 'secret or redaction or prompt_boundary'`
Expected: 모든 명령이 exit 0이고 raw secret·instruction override가 없다는 `PASS` 신호가 출력된다.

- [ ] **Step 2: 보호 변경에서만 architect 승인·구조 감사·manifest sync가 필요하다는 경계를 검증한다.**

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `PASS manifest integrity` 또는 저장소가 정의한 동등한 PASS 문자열.

- [ ] **Step 3: 이 계획의 독립 reviewer artifact와 architect approval이 모두 저장된 뒤에만 실행 대기 상태로 전환한다.** `plan-reviewer`, `principle-auditor`, `usability-reviewer`의 review scope는 이 plan 하나로 제한한다.

Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-01-simplify-plan-review-gates.md --json`
Expected: `valid: true`, 세 reviewer가 각각 독립 ID를 가지며 `result`가 모두 PASS 계열이다.

## Task 4: lifecycle refresh와 전체 검증

**파일:**
- 읽기 전용: `.agents/skills/harness/core-engine/` — 이 계획의 lifecycle 정책은 writing-plans scripts가 소유하므로 core-engine 파일은 변경 범위에서 제외한다.
- 수정: `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py`, `.agents/mission/plan.json` 생성 경계
- 수정: `HISTORY.md`, `.agentos/project/06-decisions-change-log.md`, `.agentos/project/exec-plans/evolution-status.md`

**사용자에게 보이는 마일스톤:** 새 세션에서도 단순화된 reviewer 정책이 동일하게 적용되고, 변경 근거와 다음 안전한 행동이 남는다.

- [ ] **Step 1: 변경된 hook/lifecycle runtime을 reload 또는 새 프로세스에서 다시 읽도록 하고 상태를 refresh한다.** 특정 vendor runtime을 임의로 하드코딩하지 않는다.

Run: `out=$(printf '{"cwd":"%s"}\n' "$PWD" | python3 .agents/hooks/scripts/stop_review_gate.py); echo "$out"; echo "$out" | grep -q '"continue": true'; echo 'PASS hook-fresh-process-reload'`
Expected: `"continue": true`와 `PASS hook-fresh-process-reload`가 출력된다.

- [ ] **Step 2: 실제 registry/board write는 명시적 lifecycle 단계에서만 실행하고, 그 결과가 파일 목록과 일치하는지 확인한다.**

Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && git diff --check`
Expected: `PASS` registry refresh 및 `git diff --check`.

- [ ] **Step 2a: 완료 계획 보존·명시적 archive·closeout metadata·mission/README 일치를 회귀 검증한다.**

Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_plan_lifecycle_completion_contract.sh && pytest .agents/skills/harness/run-all-tests/tests/test_plan_lifecycle.py -q`
Expected: 두 명령이 모두 exit 0이고 `PASS` 및 lifecycle 테스트 통과가 출력된다.

- [ ] **Step 3: focused suite와 public verifier를 fresh 실행한다.**

Run: `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh && bash scripts/verify-public-test-suite.sh`
Expected: 두 명령이 모두 exit 0으로 끝나고 각 verifier의 `PASS` 신호가 출력된다. 어느 하나라도 실패하면 command가 non-zero로 끝나며 완료를 주장하지 않는다.

- [ ] **Step 4: 구조 변경이면 manifest를 갱신하고 다시 확인한다.**

Run: `.agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `PASS manifest update`와 `PASS manifest integrity`.

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` 명령, runtime assumption을 검토했다. 모든 검증은 로컬 Python/Bash/pytest와 저장소 스크립트만 사용한다.

## 보호 변경 범위

- declared protected paths: `.agents/hooks/scripts/stop_review_gate.py`, `.agents/hooks/scripts/post_tool_use_review.py`, `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/scripts/request_review.py`, `.agents/skills/harness/writing-plans/scripts/plan_lifecycle.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `.agents/skills/harness/writing-plans/tests/test_request_review.py`, `.agents/skills/harness/run-all-tests/tests/test_plan_lifecycle.py`, `.agents/skills/harness/run-all-tests/tests/harness/test_plan_lifecycle_completion_contract.sh`, `.agents/skills/harness/run-all-tests/tests/harness/test_review_matrix_contract.sh`, `.agents/skills/harness/run-all-tests/tests/harness/test_review_error_recovery_contract.sh`, `.agents/skills/harness/executing-plans/SKILL.md`, `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, `.agents/agents/harness/usability-reviewer.md`, `.agentos/project/exec-plans/TEMPLATE.md`, `.agents/_version.json`(manifest 확인만), `manifest update`
- architect approval artifact: `.agents/traces/reviews/2026-09-01-simplify-plan-review-gates/harness-architect-approval.json`; schema/identity/semantic hash/완전한 declared scope/signer authorization/ISO timestamp/decision 필수
- authorized architect: `.agents/_version.json`의 `authorized_architects`에 `harness-architect`가 있어야 하며, 실제 승인 artifact의 signer·scope·hash가 모두 일치 검증된 후에만 실행
- required governance: 독립 `principle-auditor` 구조 감사, `sync-manifest --update`, `sync-manifest --check`

## 리뷰 반영 이력

- 초안: 최근 HISTORY의 반복 Gate 2 block과 현재 코드의 전역 active-plan 검사 근거를 반영했다.
- [Gate 2 1차 / plan-reviewer] 보호 승인·runtime refresh·lifecycle 테스트·실패 전파·scope가 불완전함 → 사전 Gate, fresh-process 검증, lifecycle contract test, `&&` 최종 검증, exact protected paths를 추가한다.
- [Gate 2 1차 / usability-reviewer] 복구 명령과 사용자 용어가 추상적임 → 사용자 작업 흐름, 고정 block 형식, reviewer별 재실행 명령과 성공 신호를 추가한다.
- [Gate 2 1차 / principle-auditor] 실제 CLI에 없는 `refresh --check`, 단일 SSOT·secret/prompt 회귀 검증·scope 분리가 부족함 → 구현 Task에서 실제 지원 명령을 먼저 확인하고, canonical state/migration과 redaction·prompt-injection 회귀를 필수 검증으로 구체화한다.
- Gate 2 리뷰 전에는 `reviewed: false`를 유지한다.

## Plan Quality Gate

- `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-01-simplify-plan-review-gates.md --json` → JSON `valid=true`, required reviewer 전원이 PASS 계열, identity/snapshot 일치
- protected architect 승인 검증 명령 → `PASS protected-architect-approval`; signer가 authorized architect가 아니거나 declared scope와 정확히 다르면 non-zero
- `bash .agents/skills/harness/run-all-tests/tests/harness/test_plan_lifecycle_completion_contract.sh && pytest .agents/skills/harness/run-all-tests/tests/test_plan_lifecycle.py -q` → 두 명령 exit 0 및 `PASS archive-requires-explicit-command`/`passed`; active completed plan retention, completion metadata, explicit archive-only transition 검증
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → `PASS manifest integrity`
- `bash scripts/verify-public-test-suite.sh` → `PASS agentos-public-suite`

## 세션 중단 대비 체크포인트

- 현재 완료 범위: 원인 분석, Intent Sheet, 실행 계획 초안
- 미완료 작업: 독립 Gate 2 리뷰, architect 승인, 구현·검증
- 다음 세션 첫 작업: 정확한 repository root에서 계획 reviewer matrix와 stop-hook isolation 테스트를 확인
- 아직 안 한 검증: 모든 계획 실행 검증 및 manifest update
- 관련 HISTORY checkpoint: `active-plan-gate2-approval-blocker-20260901`, `pre-plan-plan-split-20260901`

## 사전 실행 Gate와 closeout 경계

Gate 2 artifact·protected approval·signature는 reviewer runtime과 lifecycle에서만 처리한다. 기능 Task가 자기 reviewer artifact를 만들거나 스스로 승인하지 않는다. `reviewed: true`와 `구현 계획 (실행 대기)` 전이는 독립 reviewer artifact, usability PASS(필요 시), protected architect 승인, fresh manifest check 후에만 수행한다.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 아카이브 결정

(구현과 검증 완료 후 사용자가 명시적으로 archive를 요청할 때 기록)
