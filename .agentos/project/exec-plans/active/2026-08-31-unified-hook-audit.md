# unified hook 동작 감사 및 수정 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-08-31<br>
> reviewed: false<br>
> user_request: 현재 동작 중인 pre-tool 및 stop hook의 동작을 점검하고, 잘못된 동작을 수정하는 계획을 하네스 에이전트와 작성한다.<br>
> active_agent: <br>
> active_session: feature/audit-unified-hooks<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>
> usability_review_required: true<br>

> **사용자 범위 승인 (2026-08-31):** 이 계획은 unified hook 감사·수정만 수행한다. 다른 활성 계획의 변경은 baseline으로 보존하며 수정하지 않는다. 현재 manifest 불일치의 소유권은 `project-init-project-documents` 계획에 두고, 이 계획은 그 manifest를 덮어쓰지 않는다.
> **의도 해석 원칙:** 사용자는 목적·범위·기대 결과만 결정한다. payload schema, runtime parity, redaction, hash, manifest 및 검증 방식은 저장소 계약과 하네스 원칙에 따라 구현자가 결정하며 사용자에게 기술 선택을 반복 질문하지 않는다.
> **계획 semantic revision:** r6 (review-failure-routing-contract)

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** pre-tool 계열과 stop hook의 실제 입력·출력 계약을 감사하고, 질문·확인 대기·실제 완료 주장을 구분하도록 필요한 최소 수정과 회귀 검증을 적용한다.

**사용자 결과 요약:**
- 사용자는 질문을 던지거나 확인을 기다리는 중에 stop hook의 완료 검증 요구로 흐름이 오인 차단되지 않는다.
- 위험한 Bash 명령과 승인되지 않은 파일 변경은 기존 안전 경계를 유지한다.
- Codex native hook과 `agentos hook bridge`가 같은 판정 결과를 내며, 실패 시 원인과 복구 방법이 테스트로 확인된다.
- 내부 계획 리뷰가 실패해도 사용자는 기술 선택을 다시 정의하지 않는다. 의도·범위가 이미 명확하면 에이전트가 계획과 구현을 수정하고 재검증한다.
- hook의 목적·안전 경계 외에 LLM, 외부 서비스, 지식 저장소 동작은 바뀌지 않는다.

**의존성 분석:**
- 외부 의존성: 없음. 검증은 저장소의 Python/Bash/pytest와 기존 hook bridge·manifest 도구만 사용한다.
- 런타임 전제: `.codex/hooks.json`은 `.agents/hooks/scripts/`를 직접 호출하고, `agentos hook bridge`는 package-owned hook bundle을 호출한다. 두 경로의 source drift를 검증 대상으로 삼는다.
- vendor 범위: 이번 계획은 현재 실행 가능한 Codex native와 `agentos hook bridge codex` parity를 고정한다. Claude/Antigravity adapter의 동작 변경은 하지 않으며, 후속 별도 계획 없이는 unified-hook 전체 vendor parity를 주장하지 않는다.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, Intent Sheet, Gate 2 review artifacts, `HISTORY.md`, lifecycle board
- Durable Result Surface: `.agents/hooks/scripts/`, `.agents/hooks/adapters/`, `.codex/hooks.json`, `agentos/commands/setup.py`, `agentos/commands/vendor_hook.py`, hook regression tests, manifest metadata
- `.agents/hooks/README.md` is also in scope for source-path provenance correction.
- 계약 감사 결과 저장 위치: `.agents/traces/research/2026-08-31-unified-hook-audit-contract.md`와 `tests/test_unified_hooks.py`; 동시 변경 중인 skill/knowledge projection은 이 계획의 소유 범위가 아니며 별도 계획의 결과로 취급한다.
- bundle canonical source: `.agents/hooks/scripts/`; wheel force-include provenance는 `pyproject.toml`과 `agentos/terminal/hooks_bundle.py`가 소유하고, checksum/parity assertion은 `tests/test_unified_hooks.py::test_bundle_provenance`가 소유한다.

**진행 상태:** Gate 2 1차 리뷰 FAIL 반영 중, 재리뷰 대기

**검증 계약:** `tests/test_unified_hooks.py`가 모든 hook fixture와 verifier의 단일 소유 파일이다. 모든 subprocess 결과는 `{"decision": str|None, "reason": str, "exit_code": int, "stdout": str, "stderr": str, "timed_out": bool}` schema로 정규화하며 `cwd=repo root`, timeout은 10초, timeout 시 process-group을 terminate 후 kill한다.

**고정 fixture와 출력 oracle:** `test_question_waiting_message_is_not_completion` 입력은 `완료 기준 확인을 기다립니다.`, `test_completion_claim_without_fresh_verification_blocks` 입력은 `구현을 완료했습니다.`, `test_negated_completion_does_not_block` 입력은 `아직 완료하지 않았습니다.`이다. 모든 user-facing 문자열은 `reason`, `permissionDecisionReason`, `additionalContext`, stdout, stderr 각각에서 `<original-command>`, `do-not-print`, `TOKEN=`, `missing=`, `invalid=`를 포함하지 않아야 하며, block reason은 아래 matrix의 고정 문장 중 하나여야 한다.

고정 block 문장은 다음과 같다: 위험 명령은 `위험한 명령이라 실행하지 않았습니다. 안전한 대체 명령을 사용하거나 승인된 운영 절차를 확인한 뒤 다시 시도하세요.`; 정렬 실패는 `현재 변경이 승인된 계획과 맞지 않습니다. 계획 검토 상태를 확인한 뒤 다시 시도하세요.`; Bash 실패는 `명령이 실패했습니다. 출력 내용을 확인하고 원인을 고친 뒤 검증을 다시 실행하세요.`; loop lock은 `자동 실행이 아직 잠겨 있습니다. 상태를 확인하고 안전하게 중단한 뒤 다시 시도하세요.`; 리뷰 누락은 `계획 검토가 아직 유효하지 않습니다. 검토 확인 명령을 실행한 뒤 다시 시도하세요.`; dirty 검증은 `변경이 남아 있어 완료 여부를 확인할 수 없습니다. 관련 검증을 실행한 뒤 결과를 보고하세요.`이다.

**아키텍처:**
- 기존 unified hook SSOT와 vendor별 얇은 adapter 구조를 유지한다.
- 먼저 각 hook의 payload·판정·출력 계약을 고정하고, 그 다음 stop hook의 문맥 오탐과 pre-tool 경계 불일치처럼 검증으로 입증된 결함만 수정한다.
- `.codex/hooks.json`과 `.agents/hooks/adapters/codex/hooks.json`의 native command도 `agentos hook bridge codex <event>`를 호출하게 하여 native와 bridge가 같은 package-owned runtime을 사용하도록 통일한다. canonical source는 `.agents/hooks/scripts/`이고 wheel force-include는 그 source의 배포 수단이다.
- 수정 후 동일 fixture를 native config command, bridge CLI, clean wheel install에 넣어 비교하고, manifest mismatch는 승인된 baseline으로만 검사한다.

**기술 스택:** Python 3, Bash, JSON, pytest, AgentOS hook bridge, sync-manifest

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | hook 감사 계획 초안 작성 완료 |
| 완료됨 | 문제 재현: dirty worktree에서 `완료 기준 확인을 기다립니다.`가 stop hook의 완료 주장으로 오인됨 |
| 현재 위치 | Gate 2의 `plan-reviewer`, `principle-auditor`, `usability-reviewer` 독립 리뷰 대기 |
| 다음 단계 | 리뷰 PASS/CLEAN 및 artifact 생성 후 구현 실행 |
| 완료 신호 | 질문 오탐·위험 명령·bridge/native 동등성 회귀 검증과 manifest/public suite PASS |

## 세션 중단 대비 체크포인트

- 현재 완료 범위: hook 계획의 범위·fixture·출력 matrix 초안과 기존 Gate 2 FAIL 근거를 확인했다.
- 미완료 작업: Task 0–4의 exact fixtures/commands 보강, 구현 전 Gate 2 재리뷰, 승인 후 hook 수정과 fresh verification.
- 다음 세션 첫 작업: preflight와 test fixture scaffold를 실행하고 native/bridge source ownership을 확인한다.
- 아직 안 한 검증: 신규 hook regression, clean wheel parity, process-group timeout, 대상 plan-bound reviewer/architect approval, public suite.
- 관련 HISTORY checkpoint: [LOOP_STOP] unified-hook-audit-scope-blocker; public verifier baseline은 별도 소유로 유지한다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 계약·재현 고정 | 각 hook이 어떤 입력에서 허용/차단되는지 확인 가능 | hook scripts, adapters, bridge, 기존 테스트 | `python3 -m pytest -q` focused hook tests; Expected: exit 0 |
| 2. stop 판정 수정 | 질문·확인 대기 응답이 완료 주장으로 오인되지 않음 | `stop_review_gate.py`, stop regression tests | 질문/완료/검증 문장 fixture 테스트; Expected: 의도별 JSON decision 일치 |
| 3. pre-tool 경계 검증 | 위험 Bash와 파일 변경 승인 경계가 유지됨 | `check-careful.sh`, `check-alignment.py`, pre-tool tests | 허용·위험·경계 fixture; Expected: 위험 입력 block, 허용 입력 pass |
| 4. 경로·배포 무결성 | native Codex와 `agentos hook bridge` 판정이 일치하고 설치 후에도 유지됨 | `.codex/hooks.json`, `setup.py`, `vendor_hook.py`, manifest | bridge/native contract, sync-manifest, public suite; Expected: PASS |

## 리뷰 반영 이력
- Gate 2 리뷰 전. 리뷰어 artifact가 생성되기 전에는 `reviewed: true`로 변경하지 않는다.
- 사용자에게 보이는 hook reason/error text가 바뀔 수 있으므로 `usability-reviewer` PASS를 별도로 요구한다.
- 사용자 피드백 반영: 내부 기술 리뷰 실패를 사용자 의도 질문으로 되돌리지 않고, 구현자 수정·재검증 루프로 라우팅하는 Task 5를 추가했다.

## Task 0: 보호 경계·재현·의존성 확인

**사용자에게 보이는 마일스톤:** 변경 전 현재 hook의 판정과 실행 경계가 재현 가능한 기준으로 고정된다.

- [ ] **Step 0.1: 계획 리뷰에 필요한 보호 경계를 확인한다.**
  - `.agents/_version.json`의 `authorized_architects`를 확인한다.
  - `.agents/agents/harness/plan-reviewer.md`, `principle-auditor.md`, `usability-reviewer.md`에 독립 리뷰를 요청한다.
  - Run: `test -f .agents/_version.json && test -f .agents/skills/harness/writing-plans/scripts/review_artifacts.py && rg -q '^reviewed: false' .agentos/project/exec-plans/active/2026-08-31-unified-hook-audit.md`
  - Expected: exit 0; target plan remains reviewed false and unrelated artifacts are not accepted.
- [ ] **Step 0.2: 외부 의존성과 런타임 전제를 preflight한다.**
  - Run: `python3 --version && bash --version | head -1 && python3 -m pytest --version && test -f .codex/hooks.json && test -x .agents/hooks/scripts/check-careful.sh`
  - Expected: 각 명령 exit 0; external dependency 없음.
- [ ] **Step 0.3: 현재 오탐을 최소 재현한다.**
  - Run: `printf '%s' '{"cwd":"'"$(pwd)"'","last_assistant_message":"완료 기준 확인을 기다립니다."}' | python3 .agents/hooks/scripts/stop_review_gate.py`
  - Expected: exit 0; stdout parses as JSON and baseline decision is recorded without claiming the fix.
- [ ] **Step 0.4: 현재 동시 변경 범위를 분리한다.**
  - Run: `git status --short && git diff --name-only -- .agents/hooks agentos/commands/setup.py agentos/commands/vendor_hook.py agentos/terminal/hooks_bundle.py tests`
  - Expected: 훅 계획 소유 파일과 skill/knowledge projection 변경이 별도 목록으로 기록되고, 후자 파일은 이 계획에서 수정하지 않는다.

## Task 1: pre-tool 및 stop hook 계약 감사

**사용자에게 보이는 마일스톤:** hook별 입력·출력·차단 기준과 native/bridge 경로 차이가 문서와 테스트에서 명확해진다.

- [ ] **Step 1.1: pre-bash, pre-write, post-bash, stop의 payload와 출력 계약을 표로 정리한다.**
  - 대상: `.agents/hooks/scripts/check-careful.sh`, `check-alignment.py`, `post_tool_use_review.py`, `stop_review_gate.py`, `.codex/hooks.json`, `.agents/hooks/adapters/codex/hooks.json`, `agentos/commands/vendor_hook.py`.
  - Run: `test -f .agents/traces/research/2026-08-31-unified-hook-audit-contract.md && rg -q 'pre-bash|pre-write|post-bash|stop|decision|exit_code|fail-open|fail-closed' .agents/traces/research/2026-08-31-unified-hook-audit-contract.md`
  - Expected: exit 0; contract file contains all four events and parsed result fields.
- [ ] **Step 1.2: 기존 테스트와 package-owned bridge의 drift를 확인한다.**
  - Run: `python3 -m pytest -q tests/test_setup_bootstrap.py tests/test_cryptographic_hook.py`
  - Expected: exit 0; baseline focused suite passes and source-to-bundle provenance is recorded.
- [ ] **Step 1.3: prompt/data boundary와 secret·환경변수 노출 여부를 점검한다.**
  - 선행: Task 2.2에서 생성할 테스트 scaffold의 소유권을 예약하되, 구현 순서는 Task 2.2 → Task 1.3으로 실행한다.
  - Run: `HOOK_SENTINEL=do-not-print python3 -m pytest -q tests/test_unified_hooks.py::test_secret_redaction tests/test_unified_hooks.py::test_environment_allowlist tests/test_unified_hooks.py::test_prompt_boundary tests/test_unified_hooks.py::test_malformed_and_oversize_payload tests/test_unified_hooks.py::test_timeout_cleans_process_group`
  - Expected: `test_secret_redaction`, `test_environment_allowlist`, `test_prompt_boundary`, `test_malformed_and_oversize_payload`, `test_timeout_cleans_process_group`가 native stdout/stderr, bridge stdout/stderr, JSON reason, `.agents/traces/` artifact를 각각 수집해 sentinel·비허용 환경변수가 하나도 없음을 assertion하고, malformed/oversize payload 및 payload 내 지시문·Markdown이 hook decision을 우회하지 않음을 검증함.

## Task 2: stop hook 오탐 수정 및 회귀 테스트

**사용자에게 보이는 마일스톤:** 질문·확인 대기·미완료 상태는 stop hook이 실제 완료 주장으로 오인하지 않는다.

- [ ] **Step 2.1: 완료 판정 계약을 문맥 오탐 없이 최소 변경한다.**
  - 대상: `.agents/hooks/scripts/stop_review_gate.py` 및 package hook bundle source/생성 경로.
  - 제약: `완료 기준`, `완료 여부`, `검증을 기다리는 중`, 질문형·부정형 표현을 완료 주장으로 취급하지 않도록 하되, 실제 완료 주장에 대한 fresh verification 요구는 유지한다.
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py -k 'question_waiting or completion_claim or negated_completion'`
  - Expected: 질문·대기·부정 fixture는 `continue`, 실제 완료 주장+검증 부재 fixture는 `decision: block`; 완료 단어가 포함된 질문은 완료 주장으로 분류하지 않음.
- [ ] **Step 2.2: stop hook regression tests를 추가한다.**
  - 대상: 신규 `tests/test_unified_hooks.py`.
  - Run: `test -f tests/test_unified_hooks.py && python3 -m pytest -q tests/test_unified_hooks.py --collect-only`
  - Expected: exit 0 and at least 6 named stop/recovery tests are collected before Task 1.3 runs.
  - Assertion contract: `test_question_waiting_message_is_not_completion`, `test_completion_claim_without_fresh_verification_blocks`, `test_negated_completion_does_not_block`, `test_stop_hook_active_short_circuits`, `test_invalid_reviewed_plan_has_recovery`, `test_loop_lock_has_recovery`가 dirty/clean worktree와 stop payload를 고정한다.
- [ ] **Step 2.3: hook reason이 사용자에게 이해 가능하고 복구 가능하도록 확인한다.**
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py::test_reason_recovery_matrix tests/test_unified_hooks.py::test_no_secret_in_reason`
  - Expected: 위험 명령·정렬 실패·Bash 실패·loop lock·리뷰 증거 누락·dirty-worktree 검증 차단 각각에 사용자 언어의 원인, 안전한 다음 행동/명령, 성공 신호가 있고 원문 command/secret이 없다. `.agents/traces/audit-usability-review.md`가 PASS여야 한다.

## Task 3: pre-tool 경계와 vendor bridge 동등성 고정

**사용자에게 보이는 마일스톤:** 위험 명령 차단과 파일 변경 정렬 검사는 유지되며, native와 bridge 사용자가 다른 결과를 받지 않는다.

- [ ] **Step 3.1: 허용·위험·경계 입력 fixture를 pre-tool hook에 추가한다.**
  - 대상: `check-careful.sh`, `check-alignment.py`, `post_tool_use_review.py` 및 관련 테스트.
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py -k 'dangerous or allowed or boundary'`
  - Expected: 현재 threat boundary(직접 `rm -rf`, `DROP TABLE`, 강제 push/reset hard 등)는 block, 정상 명령은 허용, 분리 옵션·shell indirection은 범위를 fixture에 명시하고 승인 없이 탐지 범위를 확대하지 않으며, 실패 Bash는 retry guidance를 반환함.
- [ ] **Step 3.2: native `.codex/hooks.json`과 `agentos hook bridge codex {event}`의 결과를 비교한다.**
  - 선행: Step 3.2a에서 runtime contract와 adapter command를 고정한다.
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py::test_native_and_bridge_parity`
  - Expected: test helper가 Python tempfile 아래 wheel/venv를 생성·설치·정리하고 native config, bridge CLI, clean install 세 경로를 동일 fixture로 실행한다. 세 경로가 decision, secret-safe reason, exit code, malformed/64KiB 초과 payload, timeout 및 environment allowlist에서 동일하며 contract evidence를 기록한다.
- [ ] **Step 3.2a: source/provenance와 대칭 runtime 계약을 고정한다.**
  - 대상: `.agents/hooks/scripts/`를 canonical source로 선언하고 `pyproject.toml`의 four `force-include` mappings, `agentos/terminal/hooks_bundle.py::bundle_script`, `agentos/commands/vendor_hook.py`의 process-group terminate/kill semantics를 bundle/install 책임으로 고정한다. `.agents/hooks/README.md`의 stale source path를 `.agents/hooks/scripts/`로 수정하고 native adapter command는 bridge CLI를 호출하도록 수정한다.
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py::test_bundle_provenance tests/test_unified_hooks.py::test_runtime_contract_is_symmetric`
  - Expected: native와 bridge 모두 64 KiB payload 상한, 10초 timeout, 동일 환경 allowlist, malformed input 처리, stdout/stderr redaction과 exit-code 규칙을 공유하며 source·installed·clean-install 경로가 동일 fixture 결과를 낸다.
- [ ] **Step 3.3: setup/install 및 package bundle 반영을 검증한다.**
  - Run: `python3 -m pytest -q tests/test_setup_bootstrap.py tests/test_cryptographic_hook.py`
  - Expected: 설치된 hook 설정과 package-owned script가 수정된 계약을 가리키며 exit 0.
- [ ] **Step 3.4: 사용자-facing reason/recovery matrix를 계약표와 테스트에 고정한다.**
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py -k "recovery_matrix"`
  - Expected: 각 차단 이벤트가 내부 용어만 출력하지 않고 안전한 다음 명령과 성공 신호를 안내하며, 위험 명령 원문과 환경변수는 출력하지 않는다.

## Task 4: 보호 경로 반영 및 최종 검증

**사용자에게 보이는 마일스톤:** 수정된 hook이 AgentOS의 보호 경계·manifest·public test suite에 정식 반영된다.

- [ ] **Step 4.1: protected path 승인·구조 감사를 완료한다.**
  - `.agents/_version.json`의 `authorized_architects`에서 승인자를 확인하고, 구현자와 다른 승인자가 `.agents/traces/approvals/2026-08-31-unified-hook-audit-architect-approval.md`에 plan identity와 현재 plan hash, authorized scope(`.agents/hooks/**`, `.codex/hooks.json`, hook bundle paths), approving architect, decision, timestamp를 기록한다. stale hash 또는 승인 artifact 누락이면 `.agents/**` 수정과 manifest update를 중단한다. 독립 `principle-auditor`는 최종 변경 후 대상 plan-bound artifact를 생성한다.
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py::test_protected_approval_and_stale_hash_rejection && python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-08-31-unified-hook-audit.md`
  - Expected: 테스트가 현재 파일에서 계산한 canonical normalized `review_artifacts.plan_hash`와 approval `plan_sha256` equality, plan identity equality, `.agents/_version.json` authorized architect membership, approving architect ≠ implementer, 세 reviewer artifact의 동일 semantic snapshot, stale/missing approval hard-stop을 검증한다. 승인 artifact는 `.agents/traces/approvals/2026-08-31-unified-hook-audit-architect-approval.md`에 보존하며, 그 artifact의 `plan_sha256`가 한 글자라도 다르면 `decision=block`으로 검증한다.
- [ ] **Step 4.2: manifest 소유 범위를 확인하고 정합성을 확인한다.**
  - Run: `python3 -m pytest -q tests/test_unified_hooks.py::test_manifest_scope_is_non_gating`
  - Expected: 테스트가 hook source/config/bundle 경로가 `.agents/skills/harness/_version.json` 대상이 아님을 PASS로 입증하고, 이 계획은 skill manifest를 수정하지 않는다.
- [ ] **Step 4.2a: 최종 manifest 무결성을 확인한다.**
  - Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: exit 0 and `PASS`; unrelated dirty baseline failure is recorded separately and is not relabeled as hook success.
- [ ] **Step 4.3: focused·public 검증을 실행한다.**
  - Run: `python3 -m pytest -q tests/test_setup_bootstrap.py tests/test_cryptographic_hook.py tests/test_unified_hooks.py && bash scripts/verify-public-test-suite.sh`
  - Expected: `tests/test_unified_hooks.py` 포함 모든 명령 exit 0 및 `PASS agentos-public-suite`; baseline unrelated failure는 별도 기록하고 성공으로 숨기지 않는다.
- [ ] **Step 4.4: 구현 결과·사용 방법·fresh verification evidence를 plan에 기록하고 lifecycle을 refresh한다.**
  - Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && python3 -m pytest -q tests/test_unified_hooks.py::test_lifecycle_refresh_contract && python3 - <<'PY'
import json
from pathlib import Path
plan=Path('.agentos/project/exec-plans/active/2026-08-31-unified-hook-audit.md')
data=json.loads(Path('.agents/mission/plan.json').read_text())
assert any(x['path']==plan.as_posix() and x['status'] != '완료' for x in data['active_plans'])
assert plan.as_posix() in Path('.agentos/project/exec-plans/README.md').read_text()
assert all(token in plan.read_text() for token in ('implementation_started_at','implementation_completed_at','implementation_duration','구현 결과','사용 방법','아카이브 결정'))
PY`
  - Expected: `test_lifecycle_refresh_contract`가 active 유지·status·reviewed·implementation timestamps·구현 결과·사용 방법·완료 증거·fresh verification evidence와 mission/README 일치를 각각 assertion하고, 명시적 archive 요청 전에는 active에 남는다.

## 범위 분리: 리뷰 실패 라우팅

내부 reviewer FAIL을 사용자 의도 질문과 분리하는 `intent_ambiguity`/`technical_review_failure` 라우팅, counter, append-only trace는 unified hook 동작 범위를 벗어난다. 해당 변경은 선행 계획인 `2026-08-31-pre-plan-decision-gate-agent.md`의 intent/writing 계약으로 이동하며, 이 계획은 그 파일·테스트·문서를 수정하지 않는다. 이 계획에서는 hook이 기술 reviewer에게 사용자 질문을 출력하지 않는다는 결과만 회귀 검증한다.

### 사용자-facing 차단 사유·복구 matrix

| 이벤트 | 사용자에게 보이는 핵심 이유 | 안전한 다음 행동 | 성공 신호 |
|---|---|---|---|
| 위험 명령 | 위험한 명령이라 실행하지 않았습니다. | 안전한 대체 명령을 사용하거나 승인된 운영 절차를 확인한 뒤 다시 시도 | 명령이 실행되지 않고 안전한 명령이 허용됨 |
| 파일 변경 정렬 실패 | 현재 변경이 승인된 계획과 맞지 않습니다. | `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-08-31-unified-hook-audit.md` 실행 | `PASS gate2-review-check` |
| Bash 실패 | 명령이 실패했습니다. | `python3 -m pytest -q tests/test_setup_bootstrap.py tests/test_cryptographic_hook.py tests/test_unified_hooks.py` 재실행 | pytest exit 0 |
| loop lock | 자동 실행이 아직 잠겨 있습니다. | `test -f .agents/traces/harness/loop-state.md` 확인 후 안전한 중단 절차를 수행 | 사용자에게 내부 lock 값 없이 중단 완료 안내 |
| 리뷰 증거 누락/오래됨 | 계획 검토가 아직 유효하지 않습니다. | `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-08-31-unified-hook-audit.md` 실행 | `PASS gate2-review-check` |
| dirty-worktree 검증 누락 | 변경이 남아 있어 완료 여부를 확인할 수 없습니다. | `python3 -m pytest -q tests/test_unified_hooks.py` 실행 | pytest exit 0 및 fresh 결과 보고 |

명령 원문·토큰·환경변수·내부 `missing=`/`invalid=` 값은 사용자 메시지에 출력하지 않으며, 상세 진단은 secret-safe trace에만 기록한다.

### 이벤트별 실행 가능한 복구 검증

- 위험 명령: `python3 -m pytest -q tests/test_unified_hooks.py::test_dangerous_command_reason_is_redacted` → `PASS`, JSON의 `reason`과 `permissionDecisionReason`에 원문 command/token이 없고 `decision=block`.
- 파일 변경 정렬: `python3 -m pytest -q tests/test_unified_hooks.py::test_alignment_failure_has_safe_recovery` → `PASS`, 정확한 plan path를 포함한 review check 안내와 유효 review 후 continue.
- Bash 실패: `python3 -m pytest -q tests/test_unified_hooks.py::test_failed_bash_has_rerun_recovery` → `PASS`, 실패 exit code가 표시되고 지정 focused test 재실행 안내와 성공 exit code가 반환됨.
- loop lock: `python3 -m pytest -q tests/test_unified_hooks.py::test_loop_lock_has_recovery` → `PASS`, `test -f .agents/traces/harness/loop-state.md && rg -q '^execution_locked: ' .agents/traces/harness/loop-state.md` 확인과 안전한 중단 절차 안내, 내부 lock 값은 raw로 노출되지 않음.
- 리뷰 증거: `python3 -m pytest -q tests/test_unified_hooks.py::test_invalid_reviewed_plan_has_recovery` → `PASS`, 사용자가 artifact를 직접 편집하지 않고 정확한 plan path로 check하며 성공 시 `PASS gate2-review-check`.
- dirty-worktree 검증: `python3 -m pytest -q tests/test_unified_hooks.py::test_dirty_worktree_recovery` → `PASS`, 질문·대기는 `continue`, 실제 완료 주장만 focused verification 명령과 결과 보고 전 `block`.

각 검증은 고정된 result schema와 모든 user-facing field(`reason`, `permissionDecisionReason`, `additionalContext`, stdout, stderr)를 검사하며, protected artifact를 수동 편집하도록 안내하지 않는다.

## 구현 결과
(Gate 2 리뷰와 구현 후 작성)

## 사용 방법
(구현 후 실제 hook 판정과 복구 명령을 기록)

## 아카이브 결정
(모든 구현·검증·Gate 2 리뷰 완료 후, 사용자의 명시적 archive 요청 여부에 따라 기록)
