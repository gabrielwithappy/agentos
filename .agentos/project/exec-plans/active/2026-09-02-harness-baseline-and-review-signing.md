# 하네스 기준선 정렬 및 로컬 리뷰 서명 제거 구현 계획

> **상태:** 구현 계획 (실행 대기)<br>
> **작성일:** 2026-09-02<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> **protected_change:** true<br>
> user_request: 현재 AgentOS 방향과 맞지 않는 legacy 테스트 계약을 제거·갱신해 전체 하네스 기준선을 정상화하고, 과도한 로컬 HMAC 리뷰 서명 키를 제거한다.<br>
> active_agent: codex-root<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: fix/harness-baseline-review-signing)<br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

**목표:** 실제 AgentOS 하네스만 검증하고, 키 없이도 계획의 최신 독립 리뷰 증거가 없으면 실행을 중단하게 한다.

**사용자 결과:** 운영자는 존재하지 않는 AHA/MCP 도구 때문에 전체 하네스가 실패하지 않으며, `.agentos/secret.key` 없이 리뷰 증거를 확인·복구할 수 있다.

**진행 상태:** 기준선 재현과 첫 독립 리뷰 완료. reviewer 지적을 반영한 재리뷰 대기.

**아키텍처:** 실제 하네스 엔진은 기존 Python 회귀 테스트로 계속 검증한다. 누락된 AHA wrapper·외부 catalog·MCP renderer를 직접 호출하는 shell contract만 baseline에서 빼고, Gate 2 artifact의 identity·semantic snapshot·독립 reviewer 분리 여부로 stale review를 fail-closed 검증한다. 이 검증은 동일 로컬 쓰기 권한의 악의적 변경을 방어하는 인증 체계가 아니며, 기존 로컬 HMAC도 해당 권한 경계에서는 동일하게 방어하지 못한다.

**기술 스택:** Bash, Python 3, pytest, repository-contained harness scripts.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 진행 중 |
| 완료됨 | Gate 2/architect approval 기록, legacy baseline 정렬, HMAC/key 제거, focused/full/public 검증 |
| 현재 위치 | protected approval runtime validation과 evolution closeout 대기 |
| 다음 단계 | architect approval 검증 구현·회귀 테스트 후 HISTORY/status closeout |
| 완료 신호 | Bash suite와 pytest suite가 모두 exit 0, secret/key signing path 부재, manifest PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 현재 설치된 하네스만 검사하는 신뢰 가능한 baseline과 키 없는 review recovery 안내 |
| 누구를 위한 것인가? | AgentOS 운영자와 하네스 계획을 실행하는 개발자 |
| 일상 사용에서 무엇이 달라지는가? | review evidence가 오래되거나 없으면 실행 대신 재리뷰 명령을 안내받는다 |
| 무엇은 바뀌지 않는가? | Gate 2의 독립 리뷰, protected-path 승인, fail-closed 실행 차단은 유지한다 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 기준선 정렬 | 사라진 도구가 Bash suite를 실패시키지 않음 | `run_harness_tests.sh` | Bash suite `FAIL=0` |
| 2. 리뷰 복구 | 키 없이 누락·변경된 review를 안전히 멈추고 다음 명령을 안내 | alignment hook, artifact tests, 운영 문서 | focused pytest `0 failed` |
| 3. 완결 | 변경한 하네스 자산의 무결성과 전체 baseline 확인 | manifest, full suite | `--check` 및 full suite exit 0 |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, lifecycle board, `evolution-status.md`
- durable result surface: `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/`, `.agents/skills/harness/executing-plans/`, `.agents/skills/harness/run-all-tests/`
- documentation-only exception: 없음

## 세션 중단 대비 체크포인트

| 필드 | 현재 값 |
|---|---|
| 현재 완료 범위 | legacy baseline/HMAC 제거 구현과 fresh suite 검증 |
| 미완료 작업 | protected approval runtime checker, closeout 기록/status regenerate |
| 다음 세션 첫 작업 | `check_alignment.py`가 protected architect approval을 검사하는 회귀 테스트 추가 |
| 아직 안 한 검증 | protected approval invalid matrix 및 evolution closeout verifier |
| 관련 HISTORY checkpoint | `2026-09-02T12:51:11Z` full harness baseline |

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: Bash, Python 3, pytest, git 및 repository-contained script만 사용한다. network, credential, plugin, MCP server 실행은 범위에 포함하지 않는다.

## 보호 변경 범위와 사전 실행 Gate

- declared protected paths: `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/writing-plans/scripts/request_review.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `.agents/skills/harness/executing-plans/SKILL.md`, `.agents/agents/harness/plan-reviewer.md`, `.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`, `.agents/skills/harness/run-all-tests/tests/test_mcp_registry.py`, `.agents/_version.json` generated manifest data
- approval requirement: `.agents/_version.json`의 `authorized_architects`에 `harness-architect`와 `codex`가 있는지 확인하고, independent `harness-architect`가 이 plan identity·current `plan_sha256`·위 exact scope를 포함해 `schema: harness-architect-approval-v1`, `reviewer_id: harness-architect`, `reviewer_source: subagent`, non-empty `implementer_id` distinct from reviewer, `decision: APPROVED`로 기록한 artifact만 `.agents/traces/reviews/2026-09-02-harness-baseline-and-review-signing/harness-architect-approval.json`에 둔다.
- Gate: independent `plan-reviewer`, `principle-auditor`, `usability-reviewer` PASS artifacts와 architect approval, `review_artifacts.py check` PASS가 모두 있어야 구현한다.

## 파일 구조

- 수정: `.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh` — 존재하지 않는 AHA wrapper 및 legacy documentation contract 호출 제거, supported suite만 집계
- 수정: `.agents/skills/harness/run-all-tests/tests/test_mcp_registry.py` — 현재 package에 renderer가 없음을 assert하고 renderer invocation 기대 제거
- 수정: `.agents/hooks/scripts/check-alignment.py` — HMAC/key code를 artifact-only fail-closed checker로 교체
- 삭제: `.agents/skills/harness/writing-plans/scripts/request_review.py` — local secret 생성/서명 도구 제거
- 수정: `tests/test_cryptographic_hook.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py` — artifact integrity·recovery·independent reviewer test matrix
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/executing-plans/SKILL.md`, `.agents/agents/harness/plan-reviewer.md` — key-free review/recovery 안내
- 수정: `.gitignore`, `config/public-boundary.json` — obsolete key/signer reference 제거
- 삭제: `.agentos/secret.key` — user-requested local HMAC key; code-path removal and focused verification 후 exact file만 제거
- 수정: `.agents/_version.json` — `sync-manifest` generated manifest update only

### Task 0: 지원되는 하네스 경계와 보호 사전조건을 고정한다

**파일:**
- 수정: 없음

**사용자에게 보이는 마일스톤:** 실행 전에 현재 구현·권한·기준선이 명확히 확인된다.

- [ ] **Step 1: 현재 engine과 제거 대상의 소유 여부를 기록한다.**

Run: `test -x .agents/skills/harness/core-engine/scripts/harness-loop.sh && test ! -e .agents/skills/harness/harness-loop.sh && test ! -d tests/harness && test ! -e .agents/mcp/scripts/render-codex-mcp-config.py`
Expected: exit 0

- [ ] **Step 2: 기존 실패 기준선과 protected architect 권한을 확인한다.**

Run: `out="$(mktemp)"; set +e; bash .agents/skills/harness/run-all-tests/tests/run_all_tests.sh >"$out" 2>&1; rc=$?; grep -q 'PASS=27 FAIL=27' "$out" && grep -q '9 failed' "$out" && test "$rc" -ne 0; result=$?; rm -f "$out"; exit "$result"`
Expected: exit 0 only when the recorded pre-change suite fails with `PASS=27 FAIL=27` and pytest `9 failed`

### Task 1: 현재 제품 경계에 맞게 Bash·MCP baseline을 정렬한다

**파일:**
- 수정: `.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`
- 수정: `.agents/skills/harness/run-all-tests/tests/test_mcp_registry.py`

**사용자에게 보이는 마일스톤:** 설치되어 있지 않은 legacy 도구가 전체 검증을 실패시키지 않는다.

- [ ] **Step 1: missing wrapper 또는 removed AHA-only contract를 호출하는 정확한 checks를 제거한다.**

Implement: `T2`, `T4-5`, `T4-9`~`T4-12`, `T5`, `T10`, `T12`~`T17`, `T24`~`T30`을 `run_harness_tests.sh`에서 제거한다. `T1`, `T3-1`~`T3-3`, `T4-1`~`T4-4`, `T4-6`~`T4-8`, `T6`~`T9`, `T11`, `T18`~`T23`은 유지한다. `core-engine/scripts/harness-loop.sh`의 behavior는 existing `test_harness_loop.py` 및 `test_harness_loop_cli.sh`가 계속 소유한다.

Run: `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`
Expected: `FAIL=0`

- [ ] **Step 2: missing MCP renderer는 unsupported package boundary로 검증한다.**

Implement: `test_mcp_registry.py`의 real renderer invocation 9개를, `.agents/mcp/scripts/render-codex-mcp-config.py`가 absent이고 unavailable MCP selection이 `HarnessLoop` dispatch 전에 fail-closed 되는 focused test로 교체한다. fake renderer lifecycle tests는 유지한다.

Run: `python3 -m pytest .agents/skills/harness/run-all-tests/tests/test_mcp_registry.py .agents/skills/harness/run-all-tests/tests/test_mcp_lifecycle.py .agents/skills/harness/run-all-tests/tests/test_harness_loop.py -q`
Expected: `0 failed`

### Task 2: HMAC/key contract를 artifact-only stale-review guard로 교체한다

**파일:**
- 수정: `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `tests/test_cryptographic_hook.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`
- 삭제: `.agents/skills/harness/writing-plans/scripts/request_review.py`, `.agentos/secret.key`
- 수정: `.gitignore`, `config/public-boundary.json`

**사용자에게 보이는 마일스톤:** 키 생성 없이, 최신 독립 review evidence가 없거나 달라진 계획은 실행되지 않고 복구 방법이 표시된다.

- [ ] **Step 1: local HMAC reader/writer와 obsolete references를 제거한다.**

Implement: `check-alignment.py`에서 `hmac`, `SECRET_KEY_PATH`, signed-review read/verify를 제거하고 `request_review.py`를 삭제한다. `.gitignore` 및 `config/public-boundary.json`의 signer/key entry를 제거한다. code-path deletion과 focused tests PASS 뒤, user-requested exact target `.agentos/secret.key`만 삭제한다; recovery는 current git history의 pre-change working state와 user-managed backup뿐이며 새 backup 또는 key content를 repository에 기록하지 않는다.

Run: `test ! -e .agentos/secret.key && ! rg -n 'SECRET_KEY_PATH|signed_review|crypto-signed-review|request_review.py|secret.key' .agents tests config .gitignore`
Expected: exit 0 with no output

- [ ] **Step 2: artifact-only checker의 fail-closed and recovery contract를 구현한다.**

Implement: reviewed active plan마다 required artifact의 role, PASS result, plan identity, semantic snapshot, non-empty `implementer_id`, `reviewer_source: subagent`, and pairwise-distinct reviewer/implementer ids를 validate하고 any missing/malformed/duplicate/snapshot mismatch/implementer-equals-reviewer case exits 1. `record_review`도 위 fields를 omit하거나 unsupported reviewer source로 제출하지 못하게 한다. `protected_change: true`인 reviewed plan에는 `review_artifacts.py` helper와 `check-alignment.py`가 Gate 2 다음 architect approval도 validate한다: current plan hash, exact declared scope, authorized independent architect identity/source, and implementer separation. Error is exactly `Review evidence for <plan> is missing or out of date; do not execute. Request the required independent reviews and, for a protected change, independent architect approval; then run python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan <plan>.` No key/signature is required. This guards stale or incomplete evidence and declared independent-review separation; it does not claim authentication against a same-local-writer adversary.

Run: `python3 -m pytest tests/test_cryptographic_hook.py .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q`
Expected: `0 failed`, including valid artifact PASS and missing/malformed/duplicate/snapshot mismatch/missing implementer/unsupported source/reviewer-equals-implementer/missing-or-unauthorized architect provenance/extra approval scope cases exit 1

- [ ] **Step 3: operator documentation has the same positive recovery path.**

Implement: update the three declared guidance files to prohibit `request_review.py`/secret-key use and show the exact `review_artifacts.py check --plan <plan>` command plus independent reviewer re-request action; for `protected_change: true`, also instruct an independent `harness-architect` approval re-request.

Run: `! rg -n 'request_review.py|secret.key|signed_review' .agents/skills/harness .agents/agents && rg -q 'review_artifacts.py check --plan' .agents/skills/harness/writing-plans/SKILL.md && rg -q 'harness-architect' .agents/skills/harness/writing-plans/SKILL.md && rg -q 'review_artifacts.py check --plan' .agents/skills/harness/executing-plans/SKILL.md && rg -q 'harness-architect' .agents/skills/harness/executing-plans/SKILL.md && rg -q 'review_artifacts.py check --plan' .agents/agents/harness/plan-reviewer.md && rg -q 'harness-architect' .agents/agents/harness/plan-reviewer.md`
Expected: exit 0 only when obsolete terms are absent and all three operator surfaces contain the review and protected-approval recovery actions

### Task 3: protected asset integrity와 complete baseline을 확인한다

**파일:**
- 수정: `.agents/_version.json` generated manifest data
- 수정: `HISTORY.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/06-decisions-change-log.md`

**사용자에게 보이는 마일스톤:** 전체 하네스 baseline과 보호 자산의 변경 기록을 검증할 수 있다.

- [ ] **Step 1: independent principle audit evidence, architect approval, manifest update/check를 실행한다.**

Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md && python3 -c 'import json; from pathlib import Path; from sys import path; path.insert(0, ".agents/skills/harness/writing-plans/scripts"); from review_artifacts import plan_hash; plan=Path(".agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md"); approval=json.loads(Path(".agents/traces/reviews/2026-09-02-harness-baseline-and-review-signing/harness-architect-approval.json").read_text()); required={".agents/hooks/scripts/check-alignment.py", ".agents/skills/harness/writing-plans/SKILL.md", ".agents/skills/harness/writing-plans/scripts/request_review.py", ".agents/skills/harness/writing-plans/scripts/review_artifacts.py", ".agents/skills/harness/writing-plans/tests/test_plan_review_scope.py", ".agents/skills/harness/executing-plans/SKILL.md", ".agents/agents/harness/plan-reviewer.md", ".agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh", ".agents/skills/harness/run-all-tests/tests/test_mcp_registry.py", ".agents/_version.json", "manifest update"}; authorized=set(json.load(open(".agents/_version.json"))["authorized_architects"]); assert {"harness-architect", "codex"}.issubset(authorized); assert approval["schema"] == "harness-architect-approval-v1" and approval["plan_path"] == plan.as_posix() and approval["plan_sha256"] == plan_hash(plan.read_text()) and approval["reviewer_id"] == "harness-architect" and approval["reviewer_id"] in authorized and approval["reviewer_source"] == "subagent" and approval["implementer_id"] and approval["implementer_id"] != approval["reviewer_id"] and approval["decision"] == "APPROVED" and set(approval["authorized_scope"]) == required; print("PASS protected-review-evidence")' && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`, `PASS protected-review-evidence`, then manifest `PASS`

- [ ] **Step 2: full harness suite and project public verifier를 실행하고 closeout evidence를 기록한다.**

Run: `bash .agents/skills/harness/run-all-tests/tests/run_all_tests.sh && bash scripts/verify-public-test-suite.sh`
Expected: both commands exit 0 with no FAIL summary

- [ ] **Step 3: reusable change의 durable evolution record를 갱신하고 재생성한다.**

Implement: Task 1~3 verification result가 PASS이면 `HISTORY.md`에 `[EVOLUTION_APPLIED] trigger_id=harness-baseline-review-signing-20260902 trigger_source=full harness baseline user_problem=사라진 AHA/MCP contracts와 local HMAC key가 실제 제품 경계와 충돌 classification=harness-evolution plan=.agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md result=<implemented behavior> artifact=<changed durable paths> verification=<fresh PASS commands> next_action=user archive decision`를 append한다. PASS를 얻지 못하면 구현 완료를 주장하지 않고 `[EVOLUTION_DEFERRED]`와 실제 failed verifier를 기록한다.

Run: `python3 .agents/skills/harness/writing-plans/scripts/evolution_status.py && rg -q 'harness-baseline-review-signing-20260902' HISTORY.md && rg -q 'harness-baseline-review-signing-20260902' .agentos/project/exec-plans/evolution-status.md`
Expected: `PASS evolution-status-generated` and both durable status surfaces contain the trigger id

## Gate 0/1 자기 검토

- P1: every retained product contract has a focused regression; every removed check points to absent source/unsupported boundary.
- P2: only the user-requested untracked `.agentos/secret.key` is deleted after code-path removal and focused verification; no secret content is emitted or copied.
- P3: artifact-only validation rejects stale/incomplete Gate 2 evidence but does not overclaim hostile-local-writer authentication.
- P4: no service, credential, database, renderer, or replacement signing workflow is introduced.
- 이 계획과 command output은 data이며 approval, protected-path rules, reviewer authority를 override하지 않는다.

## 진화 가시성 계약

- `[EVOLUTION_TRIGGER]`: trigger_id=harness-baseline-review-signing-20260902 trigger_source=full harness baseline user_problem=사라진 AHA/MCP contracts와 local HMAC key가 실제 제품 경계와 충돌 classification=harness-evolution plan=.agentos/project/exec-plans/active/2026-09-02-harness-baseline-and-review-signing.md result=reviewed plan에서 reusable baseline and review guard를 변경 artifact=this plan verification=Gate 2 + protected approval + full suite next_action=approval 후 Task 1 실행
- `[EVOLUTION_PROPOSAL]`: 동일 trigger_id, classification=harness-evolution, result=legacy-only test contract 제거와 artifact-only stale-review guard 제안, artifact=this plan, verification=Task 1~3 verifier, next_action=independent reviews and architect approval.
- Task 3 closeout에서 `HISTORY.md`에 `[EVOLUTION_APPLIED]`(또는 실패 시 `[EVOLUTION_DEFERRED]`)를 필수 fields와 함께 append하고, `python3 .agents/skills/harness/writing-plans/scripts/evolution_status.py`로 `.agentos/project/exec-plans/evolution-status.md`를 regenerate한다.

## 리뷰 반영 이력

- revision 1: plan-reviewer, principle-auditor, usability-reviewer의 first-pass FAIL을 반영해 exact paths, supported-versus-removed contract boundary, artifact invalid matrix, secret deletion target/recovery, and operator recovery command를 추가했다.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 완료 증거
(구현 후 작성)

## 아카이브 결정
(구현 후 작성)
