# writing-plans 리뷰 경계 정렬 구현 계획

> **상태:** 완료<br>
> **작성일:** 2026-09-01<br>
> reviewed: true<br>
> user_request: 반복적인 메타 리뷰를 막고 구조적으로 명확한 실행 계획을 작성하도록 writing-plans 계약과 검증기를 정렬한다.<br>
> **usability_review_required:** true<br>
> **protected_change:** true<br>
> active_agent: Codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos-plan-2026-08-31-pre-plan-decision-gate-split-2 (branch: plan/2026-08-31-pre-plan-decision-gate-split-2)<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-09-01T13:16:21Z<br>
> implementation_completed_at: 2026-09-01T13:21:00Z<br>
> implementation_duration: 4m 39s<br>

**목표:** 기능 구현, 사전 Gate 2, protected 승인, 구현 후 closeout을 서로 다른 lifecycle 단계로 고정해 리뷰가 자기 자신의 증거를 요구하는 구조를 제거한다.

**사용자 결과:** 계획 작성자는 기능 Task만 실행 목록에 넣고, reviewer가 남긴 독립 증거·승인·closeout은 각 시점의 lifecycle 절차에서 확인할 수 있다.

**진행 상태:** 초안 작성 완료, Gate 2 독립 리뷰 대기

**아키텍처:** canonical plan metadata와 Gate 2 artifact 검증은 `writing-plans`가 소유한다. canonical usability header는 정확히 `> **usability_review_required:** true|false<br>` 한 줄이며, 기존 plain form은 migration 기간에 같은 boolean 값일 때만 읽고 duplicate·conflict·non-boolean은 fail closed 처리한다. validator는 File Structure와 Task의 실제 `.agents/**` 경로에서 protected 여부를 계산하고 `protected_change`/`## 보호 변경 범위` 선언과 불일치하면 `FAIL protected-change-metadata-mismatch`로 멈춘다. Task 경계 validator가 사전 Gate·승인·closeout을 구현 Task에서 발견하면 Task/line과 안전한 이동 위치를 반환한다. `request_review.py`는 existing artifact를 검증·서명하는 도구임을 명시하며 독립 reviewer 호출을 주장하지 않는다. artifact recorder는 empty·same implementer/reviewer identity와 unknown source label을 거부한다. 독립성의 실제 attestation은 trusted runtime review surface가 소유하며 local parser가 보장한다고 주장하지 않는다. hook의 hash normalization은 artifact validator와 동일한 metadata 계약을 공유한다.

**기술 스택:** Markdown, Python 표준 라이브러리, pytest, 기존 manifest/lifecycle 도구

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 기존 active 계획 5개 삭제 및 lifecycle registry 갱신 |
| 현재 위치 | lifecycle 경계와 verifier 변경 범위 확정 |
| 다음 단계 | 독립 Gate 2 리뷰 후 승인된 Task 실행 |
| 완료 신호 | 경계 회귀 테스트·hook 회귀·manifest check가 모두 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 리뷰를 통과할 수 있는 작은 기능 계획과, 언제 무엇을 확인해야 하는지 분명한 절차. |
| 누구를 위한 것인가? | AgentOS 계획 작성자, 독립 리뷰어, protected 경로 변경을 승인하는 운영자. |
| 일상 사용에서 무엇이 달라지는가? | 기능 Task에 reviewer artifact 생성이나 self-signing을 넣지 않고, Gate 단계에서만 독립 증거를 확인한다. |
| 무엇은 바뀌지 않는가? | 독립 리뷰 요구, protected 승인, secret redaction, manifest integrity, 명시적 archive 규칙. |

독립 리뷰는 다른 작업자가 계획을 검토하고 결과 artifact를 남기는 절차다. protected 승인은 `.agents/` 같은 보호 경로를 바꾸기 직전의 별도 권한 확인이다. 둘 다 기능 구현 Task가 아니며, 이 계획의 reader-first 문구는 system/developer instructions, `AGENTS.md`, vendor guide, protected-path 규칙, reviewer authority를 바꾸거나 우회하지 않는다. reviewer evidence가 없으면 작성자는 missing role별로 독립 리뷰를 요청하고 trusted runtime review surface에 artifact를 기록한 뒤 `request_review.py`를 다시 실행한다. 이 재실행은 artifact 검증·서명만 하며 안전한 read-only 실패다. Task/lifecycle boundary 위반이면 validator가 지목한 Task/line의 사전 Gate 행동은 `## 사전 실행 Gate와 closeout 경계`로, 구현 후 기록 행동은 `## 구현 후 closeout`으로 옮긴 뒤 전체 독립 리뷰를 다시 요청한다.

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/traces/reviews/2026-09-01-writing-plans-review-boundary/`, lifecycle board
- durable result surface: `.agents/skills/harness/writing-plans/SKILL.md`, `.agentos/project/exec-plans/TEMPLATE.md`, `review_artifacts.py`, `request_review.py`, `check-alignment.py`, reviewer contracts와 회귀 테스트
- documentation-only exception: 없음

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 명확한 계획 형식 | 새 계획이 기능 Task와 lifecycle 절차를 혼합하지 않는다. | skill, template, reviewer contracts | focused pytest → PASS |
| 2. 일관된 Gate 판정 | usability 리뷰 요구와 artifact 서명 역할이 모든 도구에서 같게 보인다. | validator, signing tool, hook | focused pytest → PASS |
| 3. 회귀 방지 | 메타 Task가 포함된 계획은 실행 전 구체적 이유와 복구 방법으로 거부된다. | boundary tests, manifest/lifecycle | focused/public verifier → PASS |

## 파일 구조

- 수정: `.agents/skills/harness/writing-plans/SKILL.md` — Task와 lifecycle 단계의 책임 분리 및 서명 도구의 실제 역할을 명시한다.
- 수정: `.agentos/project/exec-plans/TEMPLATE.md` — canonical metadata와 사전 Gate/승인/closeout 섹션을 Task 밖에 둔다.
- 수정: `.agents/skills/harness/writing-plans/plan-review-checklist.md` — mixed lifecycle Task를 blocking finding으로 추가한다.
- 수정: `.agents/agents/harness/{plan-reviewer,principle-auditor,usability-reviewer}.md` — 정상 lifecycle 증명과 bypass 요구를 구별하는 review boundary를 정렬한다.
- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py` — canonical/legacy usability metadata, provenance, Task/lifecycle boundary, protected approval validation을 제공한다.
- 수정: `.agents/skills/harness/writing-plans/scripts/request_review.py` — artifact를 생성하지 않는 검증·서명 도구라는 역할과 실패 복구를 정확히 출력한다.
- 수정: `.agents/hooks/scripts/check-alignment.py` — shared metadata/hash normalization 계약과 동기화한다.
- 수정: `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `tests/test_cryptographic_hook.py`, `tests/test_setup_bootstrap.py` — canonical/legacy metadata, boundary rejection, signing precondition, hook bundle parity 회귀를 추가한다.
- 수정: `.agents/_version.json`, `catalog/agents/catalog.json` — 변경된 harness assets의 manifest metadata를 갱신한다.
- 제외: 외부 reviewer dispatcher, network/MCP, archive 계획 재작성, active plan 자동 삭제, `.agentos/secret.key` 내용 또는 credential 처리 변경, `HISTORY.md` evolution closeout, `.agentos/project/exec-plans/evolution-status.md` 갱신.

## 의존성 분석

- 외부 의존성: 없음.
- 스캔 기준: Python 표준 라이브러리, pytest, git, bash와 repository-local manifest/lifecycle 스크립트만 사용한다.
- protected paths: `.agents/**` 변경은 independent Gate 2 PASS, authorized architect approval, manifest update/check 뒤에만 실행한다.
- destructive baseline action: 이전 active 계획 5개는 사용자 지시에 따라 이 계획 작성 전에 삭제했으며, archive·TEMPLATE·registry는 보존했다. 이 계획은 그 삭제를 재실행하지 않는다.

## 보호 변경 범위

- declared protected paths: `.agents/skills/harness/writing-plans/SKILL.md`, `.agents/skills/harness/writing-plans/plan-review-checklist.md`, `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/scripts/request_review.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, `.agents/agents/harness/usability-reviewer.md`, `.agents/hooks/scripts/check-alignment.py`, `.agents/_version.json`, `.agents/mission/plan.json`, `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json`
- related non-protected paths: `.agentos/project/exec-plans/TEMPLATE.md`, `catalog/agents/catalog.json`, `tests/test_cryptographic_hook.py`, `tests/test_setup_bootstrap.py`
- rule: validator가 File Structure/Task에서 `.agents/**` 변경을 찾지 못하고 declared protected paths도 없을 때만 `protected_change: false`는 independent Gate 2 artifact만 요구한다. detected paths와 `protected_change: false`, detected paths와 empty declaration, `protected_change: true`와 empty declaration, 또는 detected/declared path mismatch는 모두 `FAIL protected-change-metadata-mismatch`다. valid protected plan의 approval scope는 declared protected paths와 정확히 같아야 하며, manifest update의 tool-managed outputs는 `.agents/agents/harness/_version.json`, `.agents/skills/harness/_version.json`으로 명시해 포함한다.

## 사전 실행 Gate와 closeout 경계

이 절은 Task가 아니다. independent `plan-reviewer`, `principle-auditor`, 그리고 user-facing 분류에 따른 `usability-reviewer`가 동일 semantic snapshot을 PASS한 artifact를 trusted runtime review surface에 기록한 후에만 `reviewed: true`로 전이한다. missing artifact는 각 missing role과 review-record handoff를 출력하며, 기록 전에는 signer가 dispatch/approval을 주장하지 않는다.

이 계획의 protected 변경은 `harness-architect`가 승인하고 Codex가 self-certify하지 않는다. approval artifact는 `.agents/traces/reviews/2026-09-01-writing-plans-review-boundary/harness-architect-approval.json`에 `schema=harness-architect-approval-v1`, current `plan_path`, current semantic `plan_sha256`, `reviewer_id=harness-architect`, ISO `approved_at`, `decision=APPROVED`, 정확한 `authorized_scope`, nonempty `reviewer_source`를 가져야 한다. scope는 `## 보호 변경 범위`의 declared protected paths와 정확히 같으며 abstract `manifest update` 문자열은 포함하지 않는다. `HISTORY.md`와 evolution status는 이 approval scope 및 구현 범위에 포함하지 않는다.

- Run: `python3 - <<'PY'
import json
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, '.agents/skills/harness/writing-plans/scripts')
from review_artifacts import plan_hash
plan = Path('.agentos/project/exec-plans/active/2026-09-01-writing-plans-review-boundary.md')
approval = Path('.agents/traces/reviews/2026-09-01-writing-plans-review-boundary/harness-architect-approval.json')
data = json.loads(approval.read_text(encoding='utf-8'))
scope = {'.agents/skills/harness/writing-plans/SKILL.md', '.agents/skills/harness/writing-plans/plan-review-checklist.md', '.agents/skills/harness/writing-plans/scripts/review_artifacts.py', '.agents/skills/harness/writing-plans/scripts/request_review.py', '.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py', '.agents/agents/harness/plan-reviewer.md', '.agents/agents/harness/principle-auditor.md', '.agents/agents/harness/usability-reviewer.md', '.agents/hooks/scripts/check-alignment.py', '.agents/_version.json', '.agents/mission/plan.json', '.agents/agents/harness/_version.json', '.agents/skills/harness/_version.json'}
assert data['schema'] == 'harness-architect-approval-v1' and data['plan_path'] == plan.as_posix() and data['plan_sha256'] == plan_hash(plan.read_text(encoding='utf-8')) and data['reviewer_id'] == 'harness-architect' and data['reviewer_id'] != 'codex' and data['decision'] == 'APPROVED' and set(data['authorized_scope']) == scope and data['reviewer_source']
datetime.fromisoformat(data['approved_at'].replace('Z', '+00:00'))
print('PASS protected-approval')
PY`
- Expected: `PASS protected-approval`; current plan identity/hash, authorized non-self reviewer, timestamp, decision, and exact scope are valid. 없거나 invalid이면 `FAIL protected-approval`로 멈춘다. Task 2가 추가할 reusable validator는 이후 계획의 편의 도구이며 이 사전 Gate의 의존성이 아니다.

구현 완료 후에는 manifest update/check, lifecycle registry refresh, 그리고 plan-local 완료 증거만 수행한다. `HISTORY.md` evolution closeout과 evolution status regeneration은 별도 approved plan이 소유한다.

## 세션 중단 대비 체크포인트

- 현재 완료 범위: 기존 active 계획 5개를 삭제하고 lifecycle registry를 갱신했으며, 반복 리뷰 원인과 변경 boundary를 문서화했다.
- 미완료 작업: 이 계획의 독립 Gate 2, protected approval, skill/verifier 구현과 회귀 검증.
- 다음 세션 첫 작업: reviewer artifact가 없는 상태에서 이 계획을 독립 plan-reviewer·principle-auditor·usability-reviewer에게 검토 요청한다.
- 아직 안 한 검증: focused tests, hook parity, manifest update/check, lifecycle refresh 후 registry 확인. `HISTORY.md` evolution closeout과 evolution status regeneration은 별도 approved plan의 검증 항목이다.
- 관련 HISTORY checkpoint: `HISTORY.md`의 `gate2-triage-repeat-20260901`.

## Task 1: 계획 형식과 reviewer 경계 분리

**파일:** `.agents/skills/harness/writing-plans/SKILL.md`, `.agentos/project/exec-plans/TEMPLATE.md`, `.agents/skills/harness/writing-plans/plan-review-checklist.md`, `.agents/agents/harness/plan-reviewer.md`, `.agents/agents/harness/principle-auditor.md`, `.agents/agents/harness/usability-reviewer.md`

**사용자에게 보이는 마일스톤:** 새 계획은 기능 구현 목록과 review/approval/closeout 절차를 혼동 없이 구분한다.

- [x] **Step 1.1: canonical lifecycle section과 metadata를 정의한다.**
  - Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k 'canonical or lifecycle or boundary or usability'`
  - Expected: exit 0; exact bold canonical `true|false` header가 reviewer 집합을 결정하고, same-value plain legacy form만 migration-read되며 duplicate/conflict/non-boolean is `FAIL invalid-usability-metadata`; File Structure/Task에서 계산한 protected path와 `protected_change`/declared paths의 false·empty·mismatch 조합은 `FAIL protected-change-metadata-mismatch`이고 Task 밖 lifecycle section은 semantic contract로 유지한다.

- [x] **Step 1.2: reviewer가 정상 증명과 bypass 요구를 구별하도록 정렬한다.**
  - Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k 'boundary or reviewer'`
  - Expected: exit 0; 정상 Gate/approval 설명은 bypass로 오판하지 않고, Task 내부 self-certification·artifact 생성 요구는 Task/line과 lifecycle 이동 안내를 포함한 blocking finding이 된다.

## Task 2: artifact validator와 signing contract 정렬

**파일:** `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `.agents/skills/harness/writing-plans/scripts/request_review.py`, `.agents/hooks/scripts/check-alignment.py`, `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py`, `tests/test_cryptographic_hook.py`, `tests/test_setup_bootstrap.py`

**사용자에게 보이는 마일스톤:** Gate 검사는 필요한 독립 reviewer를 빠뜨리지 않고, review evidence가 없으면 무엇이 부족한지 알려주며 반복 실행을 유도하지 않는다.

- [x] **Step 2.1: metadata와 Task/lifecycle boundary validator를 구현한다.**
  - Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py tests/test_cryptographic_hook.py -k 'usability or boundary or semantic_snapshot'`
  - Expected: exit 0; canonical metadata는 usability reviewer를 요구하고, 기능 Task 안의 artifact/approval/signing/closeout self-management은 `FAIL plan-lifecycle-boundary task=<N> line=<N>`와 lifecycle 이동·재리뷰 안내를 반환하며, substantive plan edits만 re-review를 요구한다.

- [x] **Step 2.2: signing과 hook hash contract를 동일하게 만든다.**
  - Run: `python3 -m pytest -q tests/test_cryptographic_hook.py tests/test_setup_bootstrap.py -k 'request_review or signature or alignment or review_artifacts'`
  - Expected: exit 0; signer는 유효 artifact 없이는 dispatch했다고 주장하지 않고 `missing=<role>`별 trusted runtime review-record handoff와 safe re-run을 출력하며, empty/same implementer-reviewer identity와 unknown source label은 fail closed한다. protected approval은 detected/declared protected path가 exact-match인 plan에서만 exact scope를 요구하고, genuinely non-protected plan은 Gate 2 artifact만으로 PASS하며 hook과 artifact validator는 같은 semantic snapshot으로 PASS한다.

- [x] **Step 2.3: secret·prompt boundary 회귀를 추가한다.**
  - Run: `python3 -m pytest -q tests/test_cryptographic_hook.py tests/test_setup_bootstrap.py -k 'secret or environment or prompt or approval or self_certification'`
  - Expected: exit 0; secret/key/environment sentinel은 signer·artifact·failure output에 없고, repository/user text는 reviewer authority를 바꾸지 못하며, invalid protected approval is `FAIL` only for protected-change plans and local parser never claims to cryptographically establish external reviewer independence.

## 구현 후 closeout

이 절은 Task가 아니다. Task 1·2의 focused regression PASS 뒤, authorized `harness-architect`가 `manifest update`를 실행하고 integrity를 검사한 뒤 lifecycle registry를 refresh한다. `HISTORY.md` evolution closeout과 evolution status regeneration은 이 최소 수정 범위에서 제외하며, 별도 approved plan이 소유한다.

- Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update harness-architect && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && git diff --check`
- Expected: manifest `PASS`, lifecycle refresh succeeds, and `git diff --check` produces no whitespace errors.

## 리뷰 반영 이력

- 초안: 기존 triage 계획의 반복 FAIL RCA를 반영해 Task·Gate·approval·closeout의 책임을 분리하고, validator·signer·hook·reviewer 문구를 같은 변경 surface로 묶었다.

## 구현 결과

- `reviewed: false → true` lifecycle 전이가 Gate 2 artifact snapshot을 무효화하지 않도록 validator와 hook hash normalization을 정렬했다.
- canonical/legacy usability metadata와 missing-review artifact의 안전한 복구 안내를 정렬했다.
- template와 reviewer contracts가 기능 Task, Gate 2/protected approval, closeout을 분리하도록 갱신했다.

## 사용 방법

새 계획에는 canonical `> **usability_review_required:** true|false<br>` metadata를 쓰고, reviewer artifact·approval·signature는 Task가 아닌 lifecycle section에서 확인한다. missing role이 표시되면 독립 review-record를 남긴 뒤 signer를 다시 실행한다.

## 완료 증거

- `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py tests/test_cryptographic_hook.py tests/test_setup_bootstrap.py` → `25 passed`.
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → `PASS` integrity.
- `git diff --check` → exit 0.

## 아카이브 결정

구현·검증 후에도 사용자의 명시적 archive 요청 전까지 active 유지.
