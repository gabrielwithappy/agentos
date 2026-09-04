# 핵심 변경 중심의 계획 리뷰 개선 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-31<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> user_request: 질문으로 확정한 사용자 의도를 기준으로 semantic 변경만 자동 판정해 재리뷰하고, 일반 reviewer의 전체 plan hash 의존성과 비핵심 리뷰를 줄인다.<br>
> active_agent: codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: plan/review-scope-filter)<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-08-31T09:40:00Z<br>
> implementation_completed_at: 2026-08-31T10:20:00Z<br>
> implementation_duration: 40m<br>

> **에이전트 작업자용:** Gate 2 리뷰 합의와 protected-path 승인 전에는 구현하지 않는다. 단계 추적에는 체크박스(`- [ ]`)를 사용한다.

**목표:** 일반 reviewer artifact를 전체 plan hash에 종속시키는 방식을 제거하고, 도구가 semantic 변경을 자동 판정해 재리뷰를 판단하며, hash/signature는 protected 승인과 감사 추적에만 남긴다.

**사용자 결과:** agent는 계획의 핵심 실행 계약이 바뀐 경우에만 재리뷰하고, 기본 plan-reviewer와 principle-auditor는 유지하되 필요한 추가 reviewer만 실행하며, 일반 reviewer artifact는 전체 plan hash 변경으로 무효화되지 않는다.

**진행 상태:** 구현·검증·closeout 완료. 전체 legacy harness suite의 unrelated baseline 실패는 별도 기록했다.

**아키텍처:** 일반 reviewer artifact는 plan identity와 도구가 계산한 semantic revision을 기준으로 관리하고 전체 plan hash 비교로 무효화하지 않는다. metadata-only allowlist는 header 상태/점유 metadata, task checkbox 상태, 지정된 progress·closeout section, whitespace와 line-ending뿐이다. 그 밖의 모든 변경은 semantic이며 metadata와 semantic이 섞인 변경도 항상 semantic이다. 도구는 allowlist를 제거한 semantic snapshot을 artifact의 `semantic_snapshot`으로 저장하고, 현재 snapshot과 비교해 `semantic_revision`을 자동 산출한다. 일반 artifact에는 `plan_identity`, `review_scope`, `semantic_revision`, `semantic_snapshot`, reviewer identity를 기록한다. 기본 plan-reviewer와 principle-auditor는 유지하고 usability-reviewer 같은 추가 reviewer만 user-facing 조건에서 실행한다. reviewer는 실행 가능성·정합성·안전·범위·검증을 우선하며 문법·어휘·문체는 의미·모호성·복구 가능성·안전에 영향을 줄 때만 검토한다. 일반 reviewer validity에는 전체 plan hash를 사용하지 않고, hash/signature는 protected-path approval과 audit artifact에만 유지한다.

**기술 스택:** Python 표준 라이브러리, pytest, JSON artifact, Markdown plan, 기존 shell manifest/public verification.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 계획·reviewer 계약 수정, semantic snapshot 회귀, agent focus 계약, manifest/public 검증 |
| 현재 위치 | 구현 결과와 fresh verification이 active plan에 기록됨 |
| 다음 단계 | 사용자 확인 또는 archive 요청 |
| 완료 신호 | metadata-only 변경은 valid 유지, semantic 변경은 재리뷰 검출, 핵심 reviewer focus·manifest·public suite PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 핵심 계획 변경에만 재리뷰되는 더 빠르고 예측 가능한 계획 실행 흐름 |
| 누구를 위한 것인가? | active plan을 반복 갱신하는 프로젝트 오너와 coding agent |
| 일상 사용에서 무엇이 달라지는가? | 일반 계획의 일부 갱신이 reviewer artifact를 불필요하게 무효화하지 않고, 핵심 변경과 실제 protected 변경만 추가 검토함 |
| 무엇은 바뀌지 않는가? | semantic scope, acceptance, 검증 명령, reviewer 분리, protected approval 권한과 stop rule |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. semantic 경계 고정 | 무엇이 재리뷰를 유발하는지 명확함 | review revision/checker 설계와 fixture | metadata/semantic fixture 테스트 PASS |
| 2. checker/request 통합 | 모든 review entry point가 같은 판정 사용 | `review_artifacts.py`, `request_review.py` | artifact validity 회귀 PASS |
| 3. 운영 안내·회귀 | agent가 핵심만 읽고 재리뷰함 | SKILL/docs/tests | targeted/public suite PASS |
| 4. 무결성·closeout | 변경이 하네스 규칙에 안전하게 반영됨 | manifest/review artifacts/plan closeout | manifest·public·Gate 2 PASS |

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, reviewer artifacts, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`.
- durable result surface: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py`, `request_review.py`, 관련 회귀 테스트, `writing-plans`/`executing-plans` 운영 안내.
- documentation-only exception: 없음. checker 동작과 reviewer 비용 절감이 실제 구현 결과다.

## 의존성 분석

- 외부 서비스/API/token/network: 없음.
- protected path: `.agents/skills/harness/**`, `.agents/agents/harness/**`, `.agents/_version.json` 변경이 포함되므로 별도 `harness-architect` 승인 artifact와 authorized manifest update/check가 필요하다.
- 기존 active plan의 실행·archive는 범위에 포함하지 않으며, 이 계획의 fixture와 checker 검증만 다룬다.

## 범위와 제외 범위

- 포함: 일반 reviewer의 전체 hash 의존성 제거, 도구 기반 semantic revision·metadata-only/semantic-change fixtures, checker와 request flow 일관성, reviewer focus contract, 운영 문서와 회귀 테스트.
- 제외: 기본 plan-reviewer·principle-auditor 제거, reviewer 권한 완화, protected approval/hash/signature 우회, 문법만을 이유로 한 blocking finding, 계획 내용 자동 수정, recursive plan execution, 기존 계획의 구현 완료.

## 파일 구조

- 수정: `.agents/skills/harness/writing-plans/scripts/review_artifacts.py` — 일반 reviewer validity에서 plan hash 비교를 제거하고 plan identity·review revision·review scope를 판정하며 protected hash 검증을 분리.
- 수정: `.agents/skills/harness/writing-plans/scripts/request_review.py` — 일반 reviewer artifact를 hash에 묶지 않고 protected approval/audit 경로만 hash/signature를 기록·검증.
- 생성/수정: `.agents/skills/harness/writing-plans/tests/test_plan_review_scope.py` — metadata-only 및 semantic mutation 회귀.
- 수정: `.agents/skills/harness/writing-plans/SKILL.md`, 관련 운영 문서 — 핵심 변경 기준과 재리뷰 규칙.
- 수정: `.agents/agents/harness/plan-reviewer.md`, `principle-auditor.md`, `usability-reviewer.md` — 핵심 결함 우선, cosmetic-only 지적 비차단, 기존 reviewer 책임 경계.
- 수정: `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md` — reviewer 비용 최적화가 semantic safety를 약화하지 않는다는 계약.
- 수정: `.agents/skills/harness/_version.json` 및 manifest 결과 — 승인 후에만 갱신.

## Task 0: 기준선과 리뷰 경계 고정
- [x] Step 0.0: 구현 전 모호성 판정을 수행한다. 계획의 목적·완료 기준·reviewer 선택·hash/signature 보존 범위 중 해석이 둘 이상 가능한 항목이 있으면 사용자에게 한 번에 하나의 구체적 질문을 하고 답변 전에는 구현·reviewed: true 전이를 중단한다. 코드베이스와 root 문서에서 확인 가능한 내용은 질문하지 않는다.
  Run: `rg -n '모호|질문|one question|답변 전|reviewed: true' .agents/skills/harness/intent-clarification/SKILL.md .agents/skills/harness/writing-plans/SKILL.md .agentos/project/exec-plans/active/review-scope-filter-plan.md`
  Expected: 모호성 질문·중단 조건·질문 중복 방지 규칙이 계획과 운영 skill에 명시되어 있다.

- [x] Step 0.1: 현재 branch, dirty worktree, 이 계획의 artifact schema와 reviewer entry point를 기록한다.
  Run: `git branch --show-current && python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/review-scope-filter-plan.md --json`
  Expected: non-main branch와 현재 Gate 2 상태가 출력된다.
- [x] Step 0.2: protected approval registry와 manifest baseline을 확인한다.
  Run: `grep -q 'authorized_architects' .agents/_version.json && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: authorized architect가 존재하고 manifest check가 PASS.

## Task 1: semantic 변경 자동 분류와 protected hash 경계 구현

- [x] Step 1.1: 일반 reviewer와 protected audit의 integrity 경계를 명시한다. metadata-only allowlist는 header 상태/점유 metadata, checkbox, 지정된 progress·closeout section, whitespace/line-ending으로 고정하고, 그 밖의 모든 변경과 혼합 변경은 semantic으로 분류한다. 일반 reviewer는 plan identity·semantic revision·review scope·semantic snapshot을 사용하고 전체 plan hash를 validity 조건으로 사용하지 않으며, protected 경로만 hash/signature를 요구한다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k classification`
  Expected: 일반/protected 경계 분류 fixture가 PASS.
- [x] Step 1.2: checker와 artifact recorder가 동일 semantic snapshot 규칙을 사용하고 일반 artifact의 plan hash mismatch 차단을 제거하도록 구현한다. artifact에는 plan identity, review scope, semantic revision, semantic snapshot, reviewer identity를 남긴다.
  Run: `python3 -m py_compile .agents/skills/harness/writing-plans/scripts/review_artifacts.py .agents/skills/harness/writing-plans/scripts/request_review.py`
  Expected: compile exit 0.

## Task 2: 재리뷰 판정 회귀

- [x] Step 2.1: metadata-only mutation fixture를 추가한다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k metadata`
  Expected: 기존 artifact가 valid로 유지되고 reviewer 재호출 필요 없음.
- [x] Step 2.1a: metadata-only allowlist와 semantic snapshot 저장/비교 fixture를 추가한다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k snapshot`
  Expected: allowlist 변경은 snapshot을 유지하고 allowlist 밖 변경은 snapshot mismatch로 재리뷰된다.
- [x] Step 2.2: 도구가 semantic mutation과 metadata-only mutation을 자동 분류하는 fixture를 추가한다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k semantic`
  Expected: semantic mutation만 재리뷰 대상으로 분류되고 metadata-only mutation은 기존 artifact를 유지하며 전체 plan hash는 validity 조건이 아님.
- [x] Step 2.3: closeout·signature·중복 reviewer identity 경계를 검증한다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k artifact`
  Expected: artifact schema와 signature 안전성이 유지된다.

## Task 3: agent 운영 흐름과 문서 동기화

- [x] Step 3.1: `request_review.py`가 semantic 변경이 없을 때 기존 valid artifact를 재사용하고, 변경이 있을 때만 reviewer 실행을 요구하도록 운영 계약을 정리한다.
  Run: `rg -n 'metadata|semantic|canonical|재리뷰|review' .agents/skills/harness/writing-plans/SKILL.md .agents/skills/harness/writing-plans/scripts
  Expected: 동일 semantic classification 정책이 skill과 script에 일관되게 설명된다.
- [x] Step 3.2: root requirements/system contract와 계획 운영 문구를 동기화한다.
  Run: `grep -q 'semantic' .agentos/project/02-product-scope-and-requirements.md && grep -q '재리뷰' .agentos/project/03-system-contract.md && echo 'PASS review-scope-contract-sync'`
  Expected: 사용자·agent가 핵심 변경과 metadata 변경의 차이를 확인할 수 있다.

## Task 3a: 하네스 코어 변경 reviewer routing

- [x] Step 3a.1: 하네스 코어·AGENTS.md 변경에서도 기본 plan-reviewer와 principle-auditor를 유지하고, user-facing 변경일 때만 usability-reviewer를 추가한다. 해당하지 않는 추가 reviewer는 실행하지 않는다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k reviewer-routing`
  Expected: 표면별 최소 reviewer routing과 protected/semantic 예외가 PASS.
- [x] Step 3a.2: reviewer 독립성, semantic 변경 재리뷰, protected architect approval 및 manifest 검증이 완화되지 않는지 확인한다.
  Run: `rg -n 'reviewer-routing|principle-auditor|usability-reviewer|architect|manifest' .agents/skills/harness/writing-plans/SKILL.md AGENTS.md
  Expected: 최소 reviewer 선택과 보호 gate 유지가 명시적으로 확인된다.
- [x] Step 3a.3: 하네스 reviewer agent 계약을 수정한다. plan-reviewer와 principle-auditor는 실행 가능성·정합성·안전·범위·검증을 우선하고, usability-reviewer는 사용자 행동·안전·복구·완료 이해만 검토한다. 문법·어휘·문체·cosmetic 선호는 의미·모호성·안전·복구를 해치지 않으면 finding이나 blocking 사유로 올리지 않는다.
  Run: `rg -n "cosmetic|blocking|실행 가능성|정합성|안전|범위|검증|복구" .agents/agents/harness/plan-reviewer.md .agents/agents/harness/principle-auditor.md .agents/agents/harness/usability-reviewer.md`
  Expected: 세 reviewer agent가 핵심 리뷰 focus와 cosmetic 비차단 경계를 명시한다.

## Task 4: 통합 검증과 closeout


- [x] Step 4.1: protected-path architect approval을 현재 최종 plan hash 기준으로 확인한다.
  Run: `python3 -c "import json; from pathlib import Path; from sys import path; path.insert(0,'.agents/skills/harness/writing-plans/scripts'); from review_artifacts import plan_hash; p=Path('.agentos/project/exec-plans/active/review-scope-filter-plan.md'); a=json.loads(Path('.agents/traces/reviews/review-scope-filter-plan/harness-architect-approval.json').read_text()); required={'.agents/agents/harness/plan-reviewer.md','.agents/agents/harness/principle-auditor.md','.agents/agents/harness/usability-reviewer.md','.agents/skills/harness/writing-plans/SKILL.md','.agents/skills/harness/writing-plans/scripts/**','.agents/skills/harness/writing-plans/tests/**','.agents/_version.json','manifest update'}; assert a['plan_path']==p.as_posix() and a['plan_sha256']==plan_hash(p.read_text()) and a['reviewer_id']=='harness-architect' and a['decision']=='APPROVED' and required.issubset(set(a['authorized_scope'])); print('PASS architect-approval-artifact')"`
 Expected: 현재 계획 hash·authorized harness-architect·APPROVED decision·세 reviewer agent·writing-plans의 실제 expanded scope·version·manifest scope가 모두 일치할 때만 PASS; 하나라도 다르면 protected mutation을 중단한다.
  Additional Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -k protected_approval_scope`
  Additional Expected: exact protected files and expanded approval scope coverage are validated before manifest update.
- [x] Step 4.1a: 승인된 범위의 harness agent/SKILL 변경을 반영한 뒤 manifest를 동기화한다.
  Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: authorized approval 이후 manifest update와 check가 모두 PASS.
- [x] Step 4.2: focused, harness, manifest, public suite를 실행한다.
  Run: `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash scripts/verify-public-test-suite.sh`
  Expected: 모든 명령 exit 0과 public `PASS agentos-public-suite`.
- [x] Step 4.3: fresh Gate 2 artifact와 signed review를 생성하고 일반 artifact의 revision/scope와 protected audit hash/signature를 각각 확인한다.
  Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/review-scope-filter-plan.md --json && python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/review-scope-filter-plan.md`
  Expected: 세 reviewer가 PASS/CLEAN이고 일반 artifact는 revision/scope로 valid하며 protected audit만 hash/signature를 검증한다.

## Simplicity Gate

- 하네스 코어와 AGENTS.md 변경은 변경 표면에 맞는 최소 전문 reviewer routing을 사용한다. 계획·실행 계약은 plan-reviewer, 구조·중복·보호 경계는 principle-auditor, 사용자-facing 변경은 usability-reviewer를 요구하며 해당하지 않는 reviewer는 추가하지 않는다.
- 이 완화는 reviewer 독립성, semantic 변경 재리뷰, protected-path architect approval과 manifest 검증을 제거하지 않는다.

- 기존 reviewer 역할과 artifact schema를 유지한다.
- 전체 plan 재작성·LLM 기반 diff 분류·새 database/서비스는 추가하지 않는다.
- semantic classification은 결정적 규칙과 fixture로 검증한다.
- 기본 reviewer는 유지하고 추가 reviewer만 조건부로 선택한다. reviewer output은 핵심 finding 우선·cosmetic 지적 제외 원칙을 따른다.
- metadata-only 생략은 semantic 변경이 없는 경우에만 허용하며, ambiguity는 재리뷰로 보낸다.

## 보호 경로 승인 게이트

- 대상: `.agents/skills/harness/writing-plans/**`, `.agents/agents/harness/**`, `.agents/_version.json`.
- 구현 전 필수: `harness-architect` approval artifact에 현재 plan hash, reviewer identity, authorized scope, `decision: APPROVED`가 있어야 한다.
- 승인 실패 또는 canonicalization ambiguity: 구현 중단, `NEEDS_CONTEXT` 기록, human direction 요청.

## 세션 중단 대비 체크포인트

- 현재 완료 범위: reviewer/hash 정책, reviewer agent focus, 회귀 테스트, manifest/public 검증.
- 미완료 작업: 없음. 사용자가 명시적으로 요청하면 archive한다.
- 다음 세션 첫 작업: 필요하면 active plan과 signed review를 확인한다.
- 아직 안 한 검증: 전체 legacy harness suite의 기존 unrelated baseline 항목.
- 관련 HISTORY checkpoint: 루트 `HISTORY.md`는 현재 checkout에 없으므로 이 계획과 trace artifact를 사용한다.

## 구현 결과
- 일반 reviewer validity에서 전체 plan hash 비교를 제거하고 semantic snapshot/revision 비교를 도입했다.
- metadata-only allowlist와 mixed/semantic 변경 회귀 테스트를 추가했다.
- plan-reviewer, principle-auditor, usability-reviewer에 핵심 focus와 cosmetic 비차단 규칙을 반영했다.
- protected approval/audit에는 hash/signature를 유지하고, 승인된 범위로 manifest를 갱신했다.

## 사용 방법
일반 계획의 상태·living metadata·closeout을 갱신해도 reviewer artifact가 전체 hash 때문에 무효화되지 않는다. 목표·범위·검증·보호 경계가 바뀌면 semantic 변경으로 재리뷰한다. reviewer는 실행 가능성·정합성·안전·범위·검증을 우선하고 cosmetic 표현은 blocking finding으로 만들지 않는다.

## 완료 증거
- `python3 -m pytest -q .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py tests/test_cryptographic_hook.py` → 7 passed
- `bash .agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh` → PASS agent-contracts
- `bash scripts/verify-public-test-suite.sh` → PASS agentos-public-suite
- `python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/review-scope-filter-plan.md` → PASS crypto-signed-review
- 전체 legacy harness suite의 unrelated baseline 실패(누락된 `.agents/mcp` helper 등)는 이번 계획 범위 밖으로 남겼다.

## 아카이브 결정

사용자 요청에 따라 lifecycle archive 명령으로 이 계획을 보관한다.
