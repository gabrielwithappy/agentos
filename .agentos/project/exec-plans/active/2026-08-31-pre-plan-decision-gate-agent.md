# 계획 전 결정 게이트 하네스 에이전트 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-09-01<br>
> reviewed: false<br>
> user_request: 활성 계획을 리뷰·수정하고 우선순위를 확인한 뒤 구현한다. 이 계획은 계획 작성 전에 material ambiguity만 질문하고 기술 리뷰 실패는 에이전트가 수정하도록 하는 기반 계약을 구현한다.<br>
> active_agent: Codex<br>
> active_session: pre-plan-decision-gate-agent-r1<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>
> **usability_review_required:** true<br>

**목표:** 계획 작성 전에 확정 사실·합리적 가정·material ambiguity를 판정하고, 답변이 필요할 때만 정확히 한 질문을 출력한 뒤 답변 후 계획 생성을 재개한다.

**사용자 결과 요약:** 사용자는 확정 내용을 반복해서 질문받지 않고, 범위·동작·완료 기준을 바꾸는 미확정 사항이 있을 때만 한 번의 이해 가능한 질문을 받으며 답변 후 같은 맥락으로 계획을 재개한다.

**사용자 결과:** 위 결과를 기존 계획 문서 호환 필드로도 고정한다.

**진행 상태:** Gate 2 재리뷰를 위한 계획 수정 중

**아키텍처:** 단일 `pre-plan-decision-reviewer` 계약이 `intent-clarification`과 `writing-plans` 사이에서 triage 결과를 만든다. 이 agent는 상태 분류와 pending/resume만 소유하고, triage가 clear가 된 뒤의 목적·기대 변화·완료 기준 질문은 기존 `intent-clarification`만 소유한다. blocking 상태에서는 active plan/완료 Intent Sheet를 만들지 않고 secret-safe pending record만 유지하며, valid answer는 confirmed facts에 append한 뒤 triage를 재실행한다.

**기술 스택:** Markdown agent contract, JSON fixture/evaluator, pytest, existing manifest/lifecycle tools

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 계획 수정 / Gate 2 재리뷰 대기 |
| 완료됨 | 기존 두 활성 계획의 독립 plan/principle/usability 리뷰에서 결함 확인 |
| 현재 위치 | triage 입출력·재개·중복 방지·보호 경계 계약을 닫는 중 |
| 다음 단계 | exact fixture/evaluator 반영 후 대상 plan-bound PASS 확보 |
| 완료 신호 | 여정 테스트, 대상 Gate 2 3종 PASS, manifest check PASS |

## 세션 중단 대비 체크포인트

- 현재 완료 범위: 활성 계획 2개를 읽고 독립 리뷰를 수집했으며 모두 기존 계획의 FAIL 사유를 확인했다.
- 미완료 작업: 이 계획의 계약·fixture·문서 수정, Gate 2 재리뷰, 승인 후 구현·검증.
- 다음 세션 첫 작업: 대상 plan hash를 계산하고 세 reviewer에게 수정본 재리뷰를 요청한다.
- 아직 안 한 검증: pre-plan pytest, protected approval/review artifact, manifest update/check, public suite.
- 관련 HISTORY checkpoint: `[LOOP_STOP] unified-hook-audit-scope-blocker` 및 `public-verifier-command-selection-20260831`.

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 필요할 때만 한 번의 결정 질문과 답변 후 자동 재개를 받는다. |
| 누구를 위한 것인가? | 계획을 요청하는 프로젝트 오너와 계획을 작성·검토하는 AgentOS 사용자. |
| 일상 사용에서 무엇이 달라지는가? | 명확한 요청은 바로 계획 흐름으로 가고 material ambiguity만 먼저 묻는다. |
| 무엇은 바뀌지 않는가? | AGENTS/vendor/project docs, reviewer authority, protected approval, security boundary는 우회되지 않는다. |

## 장기 적용 표면

- traceability surface: 이 active plan, `HISTORY.md`, lifecycle board, 대상 Gate 2 traces
- durable result surface: `.agents/agents/harness/pre-plan-decision-reviewer.md`, 두 harness skill, `tests/test_pre_plan_decision_reviewer.py`, `docs/getting-started.md`, `catalog/agents/catalog.json`, `.agents/agents/harness/_version.json`
- documentation-only exception: 없음

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. triage 계약 | 명확/모호/사소한 공백이 다르게 판정된다. | agent contract, pytest fixture | exact state/output assertions |
| 2. 재개 흐름 | valid answer 후 같은 목표로 재개되고 invalid answer는 같은 질문만 복구한다. | intent/writing skills | resume/no-repeat tests |
| 3. 사용자 안내 | 질문 조건·답변·재개·성공 신호를 이해한다. | `docs/getting-started.md` | docs contract test |
| 4. 보호 반영 | 대상 plan에 귀속된 리뷰와 manifest가 확인된다. | exact manifests/traces | hash/approval/check PASS |

## 파일 구조

- 생성: `.agents/agents/harness/pre-plan-decision-reviewer.md`, `tests/test_pre_plan_decision_reviewer.py`
- 수정: `.agents/skills/harness/intent-clarification/SKILL.md`, `.agents/skills/harness/writing-plans/SKILL.md`, `docs/getting-started.md`, `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json`, `catalog/agents/catalog.json`, `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/05-agent-operating-contract.md`, `.agentos/project/06-decisions-change-log.md`
- 생성: `.agents/traces/audit-plan-review.md`, `.agents/traces/audit-principle.md`, `.agents/traces/audit-usability-review.md`
- 생성: 대상 plan-bound Gate 2 traces와 해당 review directory의 `harness-architect-approval.json`, `signed_review.json`
- 제외: `.agents/hooks/**`, unified-hook source/test (다른 계획/소유 범위)

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: planned Run은 repository-local `python3`, `.venv/bin/pytest`, existing scripts만 사용한다.
- 동시 변경: intent/writing/docs/project docs는 dirty baseline과 겹친다. 구현 전 baseline snapshot을 기록하고 이 계획 소유 변경만 유지한다. unified-hook 계획은 이 계획 결과에 의존한다.

## Task 0: preflight와 dirty baseline 고정

**사용자에게 보이는 마일스톤:** 기존 변경을 보존한 채 이 계획의 작업 경계가 고정된다.

**파일:** 없음 (읽기 전용 검사)

- [ ] **Step 0.1: 실행 도구·브랜치·대상 파일을 확인한다.**
  - Run: `test "$(git rev-parse --abbrev-ref HEAD)" != "main" && test -x .venv/bin/pytest && test -f .agentos/project/exec-plans/TEMPLATE.md && test -f .agents/skills/harness/writing-plans/scripts/review_artifacts.py`
  - Expected: exit 0 and no mutation.
- [ ] **Step 0.2: 대상 plan baseline을 확인한다.**
  - Run: `.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib
p=Path('.agentos/project/exec-plans/active/2026-08-31-pre-plan-decision-gate-agent.md')
assert p.exists() and 'reviewed: false' in p.read_text()
print('PASS pre-plan-baseline '+hashlib.sha256(p.read_bytes()).hexdigest())
PY`
  - Expected: `PASS pre-plan-baseline <64 hex>`; implementation preserves the pre-existing dirty-file set reported by `git status --porcelain=v1`.
- [ ] **Step 0.3: 겹치는 dirty baseline과 소유권을 고정한다.**
  - Run: `git status --porcelain=v1 > /tmp/agentos-pre-plan-dirty-baseline && git diff --binary -- .agents/skills/harness/intent-clarification/SKILL.md .agents/skills/harness/writing-plans/SKILL.md docs/getting-started.md .agentos/project/02-product-scope-and-requirements.md .agentos/project/05-agent-operating-contract.md .agents/skills/harness/_version.json > /tmp/agentos-pre-plan-owned-diff && test -f /tmp/agentos-pre-plan-dirty-baseline && test -f /tmp/agentos-pre-plan-owned-diff`
  - Expected: exit 0 for clean or dirty worktrees; full dirty-file set and owned-file content baseline are captured before implementation and compared afterward; unrelated changes are not overwritten.

## Task 1: triage agent의 canonical 계약과 evaluator

**사용자에게 보이는 마일스톤:** 같은 요청이 명확/사소한 공백/material ambiguity로 일관되게 판정된다.

**파일:**
- 생성: `.agents/agents/harness/pre-plan-decision-reviewer.md`
- 생성: `tests/test_pre_plan_decision_reviewer.py`

- [ ] **Step 1.1: 네 상태와 필드 schema를 고정한다.**
  - 계약: 결과 JSON은 `state`, `confirmed_facts`, `assumptions`, `blocking_questions`, `question_count`, `plan_generation_allowed`, `pending_record`, `user_message`를 가진다. `clear`/`minor_gap`는 `question_count=0`, `plan_generation_allowed=true`; `material_ambiguity`는 `question_count=1`, `plan_generation_allowed=false`, pending record만 허용; `invalid_answer`는 confirmed facts를 보존하고 같은 결정만 재질문한다.
  - 사용자 질문 형식: `상황: ... 이유: ... 선택: A) ... B) ... (또는 짧은 자유 입력) 질문: ...?`로 고정하고 선택지는 2개 이하, `질문:` 뒤 물음표는 하나만 허용한다. 구현 표면·schema·hash 선택을 사용자에게 묻지 않는다.
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_decision_reviewer.py -k 'schema or clear_request or material_ambiguity or minor_gap or invalid_answer'`
  - Expected: `collected >= 5`, exit 0, exact state/question_count/plan_generation_allowed/pending/no-secret assertions PASS.
- [ ] **Step 1.2: one-question 출력과 재개/중복 방지를 구현한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_decision_reviewer.py -k 'one_question or resume or no_repeat or scope_preserved'`
  - Expected: `collected >= 4`, exit 0; `test_resume_confirms_retained_facts_in_same_session`, `test_one_question_output_has_no_extra_interrogative`, `test_blocking_case_creates_only_pending_record`, and reconnect coverage pass, valid answers re-triage, prior facts remain equal, unresolved decision only is re-asked, and both active plan and completed Intent Sheet are absent before clearance.

## Task 2: 기존 intent/writing 흐름에 blocking gate 연결

**사용자에게 보이는 마일스톤:** 필요한 질문 전에는 계획이 생성되지 않고 답변 후 같은 목표로 재개된다.

**파일:**
- 수정: `.agents/skills/harness/intent-clarification/SKILL.md`
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`

- [ ] **Step 2.1: triage→기존 intent Q1–Q4 handoff와 no-repeat를 연결한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_decision_reviewer.py -k 'handoff or existing_fact or prompt_boundary or secret_redaction'`
  - Expected: `collected >= 4`, exit 0; negative ownership tests prove pre-plan reviewer does not answer Q1–Q4 and intent-clarification does not own pending/resume, while hostile repository text cannot override authority and secret/env values are absent. The existing `requirement-discovery` remains requirements-only and is asserted not to create plans or approvals.
- [ ] **Step 2.2: valid/invalid answer resume 계약을 문서에 반영한다.**
  - Run: `rg -n '재개|유효한 답변|불완전|다시 묻지|active plan|Intent Sheet|blocking' .agents/skills/harness/intent-clarification/SKILL.md .agents/skills/harness/writing-plans/SKILL.md`
  - Expected: exit 0; blocked input creates no active plan/completed Intent Sheet, valid answer appends/re-triages, invalid answer preserves facts and re-asks only unresolved decision.

## Task 3: 사용자 안내와 project traceability

**사용자에게 보이는 마일스톤:** 사용자가 질문에 답하는 법과 계획 생성 성공 신호를 알 수 있다.

**파일:**
- 수정: `docs/getting-started.md`, `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/05-agent-operating-contract.md`, `.agentos/project/06-decisions-change-log.md`

- [ ] **Step 3.1: 질문·답변·재개·성공 신호를 문서화한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_decision_reviewer.py -k 'docs or user_message'`
  - Expected: `collected >= 2`, exit 0; documentation assertions cover the blocking explanation, answer/options format, valid/invalid resume, and retained-facts preview. `test_clearance_emits_success_signal_in_order` separately asserts runtime output order `확인된 목표·범위·완료 기준을 반영했습니다.` then `계획을 작성할 준비가 되었습니다.` and plan generation allowed.

## Task 4: protected path, manifest, Gate 2 closeout

**사용자에게 보이는 마일스톤:** 독립 리뷰·승인·무결성 검증 없이는 구현이 시작되지 않는다.

**파일:**
- 수정: `.agents/agents/harness/_version.json`, `catalog/agents/catalog.json`
- 생성: `.agents/traces/reviews/2026-08-31-pre-plan-decision-gate-agent/{plan-reviewer,principle-auditor,usability-reviewer}.json`, `harness-architect-approval.json`, `signed_review.json`

- [ ] **Step 4.1: 구현자와 분리된 authorized architect 승인을 확인한다.**
  - Run: `.venv/bin/python - <<'PY'
import json
from pathlib import Path
d=json.loads(Path('.agents/_version.json').read_text())
assert d.get('authorized_architects')
print('PASS authorized-architects-present')
PY`
  - Expected: `PASS authorized-architects-present`; only an authorized architect distinct from Codex may approve, using the established `harness-architect-approval-v1` artifact with current normalized hash, exact scope, approver, approved_at, and `APPROVED` decision.
- [ ] **Step 4.1a: 승인 artifact의 machine-checkable 조건을 검증한다.**
  - Run: `python3 -c "import json; from pathlib import Path; from datetime import datetime; import sys; sys.path.insert(0,'.agents/skills/harness/writing-plans/scripts'); from review_artifacts import plan_hash,PROTECTED_REVIEW_SCOPE; p=Path('.agentos/project/exec-plans/active/2026-08-31-pre-plan-decision-gate-agent.md'); d=json.loads(Path('.agents/traces/reviews/2026-08-31-pre-plan-decision-gate-agent/harness-architect-approval.json').read_text()); a=json.loads(Path('.agents/_version.json').read_text())['authorized_architects']; datetime.fromisoformat(d['approved_at'].replace('Z','+00:00')); assert d['schema']=='harness-architect-approval-v1' and d['plan_path']==p.as_posix() and d['plan_sha256']==plan_hash(p.read_text()) and d['reviewer_id'] in a and d['reviewer_id'].lower()!='codex' and d['decision']=='APPROVED' and set(PROTECTED_REVIEW_SCOPE).issubset(set(d['authorized_scope'])); print('PASS pre-plan-approval-oracle')"`
  - Expected: `PASS pre-plan-approval-oracle`; semantic hash mismatch, missing protected scope/ISO approved_at, unauthorized or case-insensitive self-approver, or non-APPROVED decision exits nonzero.
- [ ] **Step 4.2: 대상 plan-bound reviewer artifacts를 검증한다.**
  - Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-08-31-pre-plan-decision-gate-agent.md`
  - Expected: `PASS gate2-review-check` only with exact plan path, semantic revision/snapshot, reviewer provenance, timestamp, PASS/CLEAN verdict, and distinct roles.
- [ ] **Step 4.2a: cryptographic review record를 생성·검증한다.**
  - Run: `python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/2026-08-31-pre-plan-decision-gate-agent.md && test -f .agents/traces/reviews/2026-08-31-pre-plan-decision-gate-agent/signed_review.json`
  - Expected: exit 0; signed_review.json binds the current semantic plan hash and all three target reviewer artifacts, and implementation remains locked until this record and architect approval exist.
- [ ] **Step 4.2b: signed review의 HMAC·artifact hash binding을 검증한다.**
  - Run: `python3 -c "import json,hmac,hashlib; from pathlib import Path; import sys; sys.path.insert(0,'.agents/skills/harness/writing-plans/scripts'); from review_artifacts import plan_hash; from request_review import verify_signature; root=Path('.'); p=root/'.agentos/project/exec-plans/active/2026-08-31-pre-plan-decision-gate-agent.md'; s=json.loads((root/'.agentos/secret.key').read_bytes().decode('latin1')) if False else (root/'.agentos/secret.key').read_bytes(); d=json.loads((root/'.agents/traces/reviews/2026-08-31-pre-plan-decision-gate-agent/signed_review.json').read_text()); assert d['schema']=='crypto-signed-review-v1' and d['plan_path']==p.as_posix() and d['plan_sha256']==plan_hash(p.read_text()); assert verify_signature(s,f\"{d['plan_path']}:{d['plan_sha256']}:{d['reviewed_at']}\",d['signature']); assert set(d['gate2_artifacts'])=={'plan-reviewer','principle-auditor','usability-reviewer'}; print('PASS signed-review-oracle')"`
  - Expected: `PASS signed-review-oracle`; HMAC, normalized plan hash, path, timestamp, and exactly three reviewer artifact bindings all verify. `test_all_gate_artifacts_share_normalized_hash` additionally compares every embedded reviewer artifact hash with the approval and signed-review hash.
- [ ] **Step 4.3: manifest를 소유 범위로 반영한다.**
  - Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: both exit 0 and `PASS`; post-update diff is limited to `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json`, and the explicitly planned catalog entry, while the captured dirty baseline remains unchanged elsewhere.
- [ ] **Step 4.4: 전체 pre-plan 검증과 lifecycle refresh를 실행한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_decision_reviewer.py && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: all tests collected and exit 0, lifecycle exit 0, manifest check exit 0; plan stays active until explicit archive request.
- [ ] **Step 4.5: 구현 진입 전 승인 gate를 확인한다.**
  - Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-08-31-pre-plan-decision-gate-agent.md --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['valid'] and set(d['required_reviewers'])=={'plan-reviewer','principle-auditor','usability-reviewer'}; print('PASS reviewer-gate')" && .venv/bin/pytest -q tests/test_pre_plan_decision_reviewer.py -k 'all_gate_artifacts_share_normalized_hash' && test -f .agents/traces/reviews/2026-08-31-pre-plan-decision-gate-agent/harness-architect-approval.json && test -f .agents/traces/reviews/2026-08-31-pre-plan-decision-gate-agent/signed_review.json && test -f .agents/traces/audit-plan-review.md && test -f .agents/traces/audit-principle.md && test -f .agents/traces/audit-usability-review.md && echo 'PASS pre-plan-implementation-gate'`
  - Expected: `PASS reviewer-gate` followed by `PASS pre-plan-implementation-gate`; implementation is forbidden unless Step 4.1a, Step 4.2b, all three audit traces, reviewer artifacts, signed_review, and architect approval pass. A runtime test verifies the same normalized hash across all artifact classes.

## Plan Quality Gate

- clear: 질문 0개, plan generation 허용.
- minor gap: 질문 0개, assumption 기록.
- material ambiguity: 정확히 질문 1개, active plan/완료 Intent Sheet 금지, secret-safe pending record만 허용.
- pre-answer artifact boundary: blocking 상태에서 허용되는 유일한 durable artifact는 request id, unresolved decision id, redacted confirmed facts, redacted assumptions를 가진 pending record이며 active plan, completed Intent Sheet, reviewer artifact, approval, secret/env field는 생성하지 않는다. `test_blocking_case_creates_only_pending_record`가 이 목록을 검사한다.
- valid answer: 기존 사실 보존 → triage 재실행 → 남은 질문만 질문 → 모두 해소될 때만 Intent Sheet/plan 생성.
- invalid/incomplete answer: 같은 결정만 재질문, 기존 답변 유지, plan 생성 금지.
- resume protocol: 사용자는 질문이 표시된 같은 대화의 다음 메시지에 제시된 A/B 또는 짧은 자유 입력으로 답한다. 중단 후 재접속하면 pending record의 plan request를 재개하고, 기존 confirmed facts/assumptions를 먼저 한 줄로 확인한 뒤 같은 미해결 질문을 다시 표시한다.
- user confirmation: 모든 blocking question이 해소되기 전에는 active plan을 생성하지 않으며, 해소 후 `확인된 목표·범위·완료 기준을 반영했습니다.`를 먼저 출력하고 `계획을 작성할 준비가 되었습니다.`를 성공 신호로 출력한다.
- prompt/data boundary, reviewer authority, protected approval, manifest ownership remain unchanged.

## 리뷰 반영 이력

- 2026-09-01 plan-reviewer: exact state/output oracle, 대상 plan-bound approval/review, preflight, dirty baseline, checkpoint 보강.
- 2026-09-01 principle-auditor: 정확한 manifest 경로, distinct architect approval, prompt-boundary/secret test, canonical owner 보강.
- 2026-09-01 usability-reviewer: valid/invalid resume, no-artifact-before-question, one-question wording, mandatory docs acceptance 보강.

## 구현 결과

(Gate 2 PASS와 구현 후 기록)

## 사용 방법

구현 후 사용자는 blocking 질문에 제시된 A/B 또는 짧은 답을 같은 대화의 다음 메시지로 보낸다. 불완전한 답이면 시스템은 기존 답변을 보존하고 같은 미해결 결정만 다시 묻는다. 모든 결정이 해소되면 `계획을 작성할 준비가 되었습니다.`가 표시되고 기존 writing-plans 흐름이 시작된다.

## 완료 증거

(구현 후 fresh command output을 기록)

## 아카이브 결정

(구현·검증·Gate 2 closeout 후에도 사용자 명시적 archive 요청 전까지 active 유지)
