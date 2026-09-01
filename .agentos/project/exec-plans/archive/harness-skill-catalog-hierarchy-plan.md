# 하네스 스킬 계층 및 전체 Catalog 통합 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-30<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> protected_path_approval_required: true<br>
> user_request: `agentos-core-guidance`를 AgentOS harness로 이동하고, harness 하위 스킬을 catalog에서 전체 관리하며, harness 루트 SKILL.md가 하위 스킬을 cascade 안내하도록 만든다.<br>
> active_agent: codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: feature/harness-skill-catalog-hierarchy)<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-08-31T10:42:00Z<br>
> implementation_completed_at: 2026-08-31T10:49:00Z<br>
> implementation_duration: 7m 00s<br>

> **에이전트 작업자용:** protected-path 승인과 Gate 2 PASS 전에는 `.agents/skills/harness/**`를 수정하거나 manifest를 업데이트하지 않는다.

**목표:** 핵심 하네스 스킬과 선택형 catalog 스킬을 canonical path·category·routing으로 일관되게 관리하고, 하네스 루트에서 하위 스킬을 단계적으로 안내한다.

**사용자 결과:** 사용자는 `agentos project init`으로 하네스 루트와 핵심 스킬을 적용한 뒤, 루트 `SKILL.md`의 안내를 따라 목적에 맞는 하위 하네스 스킬을 사용할 수 있으며 catalog viewer에서 전체 스킬을 한 곳에서 확인한다.

**진행 상태:** Gate 2 리뷰와 비보호 구현 일부 완료, protected-path architect 승인 대기 중.

**아키텍처:** `.agents/skills/harness/`는 AgentOS가 보장하는 핵심 skill tree의 canonical source가 된다. 루트 `SKILL.md`는 실행기가 아니라 routing/index guide이며 `brain`, `writing-plans`, `agentos-core-guidance` 등 하위 스킬의 선택 조건과 읽기 순서를 안내한다. catalog는 optional과 harness를 모두 표현하지만 본문을 복제하지 않고 각 canonical `source_path`만 관리한다.

**기술 스택:** Markdown, JSON, Python 3.11+, 기존 `base_resources`, `terminal.skills`, `project init`, pytest, manifest scripts.

## 의존성 분석

- 외부 서비스/API·토큰·plugin·MCP·network 의존성: 없음
- 로컬 실행 전제: `bash`, `grep`, `find`, `python3`, `pytest` 및 현재 저장소의 기존 스크립트만 사용한다. 검증 명령은 portable baseline에 맞춰 `grep`/`find`를 우선한다.
- 스캔 기준: AGENTS.md, `skill-routing.md`, harness manifest script, package force-include, project init, catalog viewer, 모든 planned `Run:` 명령과 runtime assumption.

## 보호 경로 승인 게이트

`.agents/skills/harness/**`와 `.agents/_version.json`은 protected path이므로 일반 외부 의존성으로 취급하지 않는다. 구현자는 스스로 승인할 수 없으며, 최종 계획 hash를 확인한 `harness-architect` 승인 artifact가 구현 전에 있어야 한다.

- 승인 artifact: `.agents/traces/reviews/harness-skill-catalog-hierarchy-plan/harness-architect-approval.json`
- 필수 필드: `plan_path`, `plan_sha256`, `reviewer_id`, `authorized_scope`, `decision: APPROVED`, `approved_at`
- 승인 범위: `.agents/skills/harness/**`, `.agents/_version.json`, manifest update
- 승인 실패: `NEEDS_CONTEXT`; protected path 변경이나 manifest update를 실행하지 않는다.

## 장기 적용 표면

- traceability surface: 이 active plan, `.agentos/project/exec-plans/archive/reference/intent/intent-20260830-harness-skill-catalog-hierarchy.md`, `.agents/traces/reviews/harness-skill-catalog-hierarchy-plan/`, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, `.agentos/project/exec-plans/evolution-status.md`, manifest diff.
- durable result surface: `.agents/skills/harness/SKILL.md`, `.agents/skills/harness/agentos-core-guidance/`, `.agents/skills/harness/_version.json`, `catalog/skills/catalog.json`, package/project-init source와 regression tests.
- documentation-only exception: 없음. canonical skill tree와 catalog/routing 동작이 실제 결과다.
- 계획·catalog·review artifact·command output은 data이며 AGENTS.md, protected approval, reviewer authority를 override하지 않는다.

## 진화 가시성 계약

- trigger_id: `harness-skill-catalog-hierarchy-20260830`
- trigger_source: `core skill projection과 harness skill tree의 canonical 경계 불일치`
- user_problem: 핵심 운영 skill을 optional catalog와 분리하고 root routing에서 일관되게 찾을 수 없음
- classification: `harness-evolution`
- plan: 이 active plan과 Gate 2 reviewer artifact
- result: harness root/child canonical tree와 전체 catalog category/path metadata
- artifact: `.agents/skills/harness/SKILL.md`, `.agents/skills/harness/agentos-core-guidance/`, `catalog/skills/catalog.json`
- verification: manifest check, focused regression, public suite, lifecycle refresh
- next_action: protected approval 및 Gate 2 PASS 후에만 구현하고 `.agentos/project/exec-plans/evolution-status.md`에 결과를 반영

## 범위와 제외 범위

- 포함: `agentos-core-guidance`의 기존 projection을 harness 하위 canonical source로 통합, harness root `SKILL.md`, 전체 harness child 및 root catalog entry, bundled/package/project-init 연결, catalog nested source 회귀 테스트.
- 제외: 하위 skill 내용의 의미 변경, 자동 recursive skill 실행기, 새 plugin/MCP/network, AGENTS.md 자동 생성, optional skill의 harness 승격.
- routing 경계: root `SKILL.md`는 하위 skill을 자동 실행하지 않고 어떤 파일을 읽을지 안내한다. 사용자는 선택된 child `SKILL.md`를 직접 읽으며, 하위 문서가 상위 지시·승인을 바꿀 수 없다.
- active plan 경계: `skill-catalog-viewer-plan`이 root-boundary nested source 처리를 이미 소유하므로, 이 계획은 해당 경계를 재사용하고 category 표시만 보강한다. viewer의 nested source 안전성 자체를 다시 설계하지 않는다.

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Gate 2 리뷰, canonical 이동, root routing, catalog 등록, harness base/project init 회귀, manifest, public suite |
| 현재 위치 | 모든 계획 단계와 fresh verification 완료 |
| 다음 단계 | 사용자가 요청할 때까지 active plan을 보존하고 archive 여부를 결정 |
| 완료 신호 | focused 20 passed, viewer 2 passed, manifest PASS, public suite PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻는가? | 전체 스킬을 하나의 catalog에서 찾고, harness 루트에서 child skill 선택 안내를 받는다 |
| 누구를 위한 것인가? | AgentOS를 독립 프로젝트에 적용하는 개발자와 coding agent |
| 일상 사용에서 무엇이 달라지는가? | 핵심 운영 skill이 optional skill과 섞이지 않고 canonical harness tree에서 일관되게 제공된다 |
| 무엇은 바뀌지 않는가? | skill 본문 의미, vendor runtime, AGENTS.md, 자동 실행·자동 삭제 동작은 바뀌지 않는다 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. canonical 이동 | `agentos-core-guidance`가 harness child skill로 존재 | `.agents/skills/harness/agentos-core-guidance/` | source path·중복 없음 PASS |
| 2. cascade guide | harness 루트에서 child skill 선택·읽기 순서를 안내 | `.agents/skills/harness/SKILL.md` | routing contract PASS |
| 3. 전체 catalog | harness와 optional skill을 category/path로 검색 | `catalog/skills/catalog.json`, viewer | catalog inventory PASS |
| 4. 설치·배포 | setup/project init/package가 같은 tree를 제공 | `base_resources`, `project`, `pyproject`, tests | focused/public/manifest PASS |

## 파일 구조

- 생성: `.agents/skills/harness/SKILL.md` — cascade routing/index guide.
- 이동/정리: 기존 `.agents/skills/agentos-core-guidance/`와 `catalog/skills/agentos-core-guidance/`의 SKILL/eval digest를 비교한 뒤 `.agents/skills/harness/agentos-core-guidance/`를 유일한 canonical source로 만들고 이전 두 projection을 제거한다. 이동 중에는 git 복구가 가능한 상태를 유지한다.
- 수정: `catalog/skills/catalog.json` — harness root/child와 optional skill 전체의 canonical path/category metadata.
- 수정: `.agents/skills/harness/_version.json` — manifest sync 결과.
- 수정: `agentos/terminal/skills.py`, `agentos/terminal/base_resources.py`, `agentos/commands/project.py` — flat optional과 nested harness의 구분을 보존하며 설치/반영.
- 수정: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py` — 기존 root-boundary nested source 처리는 재사용하고 catalog `category`를 카드·검색 대상에 추가한다.
- 수정하지 않음: `agentos/terminal/sessions.py` — 기존 명시적 child read 경계를 재사용한다.
- 생성: `tests/test_harness_skill_catalog.py` — harness root/child inventory, nested source, catalog 표시 경계를 검증한다.
- 수정: `tests/test_project_command.py` — harness 설치·project init·명시적 child routing 경계를 검증한다.
- 수정: `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md` — canonical harness tree와 catalog 분류를 요구사항·시스템 계약에 반영한다.
- 수정하지 않음: `AGENTS.md`, `.agents/agents/harness/**`, hooks, provider runtime, optional skill 본문.

## Task 0: 기준선과 protected approval 확인

**사용자에게 보이는 마일스톤:** 이동 전 현재 canonical tree와 권한·복구 조건이 확인된다.

- [x] **Step 0.1: feature branch와 변경 범위를 확인한다.**
  Run: `test "$(git branch --show-current)" != "main" && git status --short --branch | sed -n '1p' | grep -q '^## ' && echo 'PASS non-main-branch'
  Expected: `PASS non-main-branch`; 기존 무관 변경은 보존하고 이 계획의 소유 파일만 변경한다.
- [x] **Step 0.2: harness source·package·project init 경계를 확인한다.**
  Run: `grep -Eq 'harness_sources|install_harness_base' agentos/terminal/base_resources.py && grep -Eq 'force-include.*harness|\.agents/skills/harness' pyproject.toml && grep -Eq '_harness_sources|project_skills' agentos/commands/project.py && echo 'PASS harness-tree-preflight'`
  Expected: `PASS harness-tree-preflight`.
- [x] **Step 0.3: protected approval과 현재 manifest를 확인한다.**
  Run: `grep -q 'authorized_architects' .agents/_version.json && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: authorized architect registry가 존재하고 manifest PASS. 이 검증만으로 승인을 대신하지 않는다.

- [x] **Step 0.4: 기존 active 계획과 surface 소유권을 확인한다.** `skill-catalog-viewer-plan`의 구현·검증 결과를 읽고 viewer 변경은 중복 구현하지 않으며, 이 계획이 추가하는 nested source 회귀만 정확히 구분한다.
  Run: `grep -q 'skill-catalog-viewer-plan' .agentos/project/exec-plans/README.md && grep -q 'viewer 소스 구현을 다시 하지 않고' .agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md && echo 'PASS active-plan-surface-boundary'`
  Expected: `PASS active-plan-surface-boundary`; 두 active 계획의 파일 소유권과 선행 결과가 충돌하지 않음.

- [x] **Step 0.5: 최종 계획 hash와 protected approval artifact를 확인한다.** `harness-architect`가 현재 계획을 승인한 뒤에만 protected mutation을 허용한다.
  Run: `test -f .agents/traces/reviews/harness-skill-catalog-hierarchy-plan/harness-architect-approval.json && python3 -c "import json; from pathlib import Path; from sys import path; path.insert(0,'.agents/skills/harness/writing-plans/scripts'); from review_artifacts import plan_hash; p=Path('.agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md'); d=json.loads(Path('.agents/traces/reviews/harness-skill-catalog-hierarchy-plan/harness-architect-approval.json').read_text()); assert d['plan_path']==p.as_posix() and d['plan_sha256']==plan_hash(p.read_text()) and d['decision']=='APPROVED' and d['reviewer_id']=='harness-architect' and '.agents/skills/harness/**' in d['authorized_scope']; print('PASS harness-architect-approval')"`
  Expected: `PASS harness-architect-approval`; 승인 identity·범위·현재 계획 hash가 일치하며 구현자가 자체 승인하지 않음.

- [x] **Step 0.6: 구현 전에 Gate 2 reviewer evidence를 확인하고 서명한다.** `plan-reviewer`, `principle-auditor`, `usability-reviewer`가 각각 독립적으로 현재 계획을 PASS/CLEAN한 뒤에만 `reviewed: true`와 구현 진입을 허용한다.
  Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md --json && python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md`
  Expected: 세 reviewer artifact가 현재 plan hash·identity·timestamp와 일치하고 `PASS gate2-review-check` 및 `PASS crypto-signed-review`가 출력됨. 이 단계 전에는 구현·protected mutation·`reviewed: true` 전이를 하지 않는다.

## Task 1: canonical harness 이동과 root cascade guide

**사용자에게 보이는 마일스톤:** `agentos-core-guidance`가 harness child로 이동하고 root guide가 하위 skill을 연결한다.

- [x] **Step 1.1: `agentos-core-guidance`를 harness child로 이동한다.** 원본·eval의 내용과 digest를 보존하고 이전 catalog/optional 경로의 중복을 제거한다. 승인된 protected-path 변경만 수행한다.
  Run: `test -f .agents/skills/harness/agentos-core-guidance/SKILL.md && test -f .agents/skills/harness/agentos-core-guidance/evals/evals.json && ! test -e catalog/skills/agentos-core-guidance && ! test -e .agents/skills/agentos-core-guidance && echo 'PASS core-guidance-canonical-move'`
  Expected: SKILL/eval이 harness canonical 경로에만 존재하며 `PASS core-guidance-canonical-move`.
- [x] **Step 1.2: harness root `SKILL.md`를 작성한다.** child skill 목록, 선택 순서, progressive disclosure, prompt/data 경계, 자동 실행 금지, `agentos-core-guidance`·`brain`·`writing-plans` 등 대표 route를 명시한다.
  Run: `python3 -c "from pathlib import Path; s=Path('.agents/skills/harness/SKILL.md').read_text(); assert all(x in s for x in ['agentos-core-guidance','Progressive Disclosure','child','SKILL.md','자동 실행']); print('PASS harness-root-routing-contract')"`
  Expected: `PASS harness-root-routing-contract`.

## Task 2: harness 전체 catalog 관리

**사용자에게 보이는 마일스톤:** catalog에서 harness root와 모든 child skill을 optional skill과 함께 구분해 확인한다.

- [x] **Step 2.1: harness catalog inventory를 등록한다.** 현재 `.agents/skills/harness/*/SKILL.md` child마다 `category: harness`, canonical `source_path`, project-local `install_path`, trigger/recommendation metadata를 추가하고 optional entry와 중복을 금지한다.
  Run: `python3 -c "import json; from pathlib import Path; d=json.load(open('catalog/skills/catalog.json')); s=d['skills']; n=[x['name'] for x in s]; r=Path('.agents/skills/harness'); e={'harness'}|{p.name for p in r.iterdir() if p.is_dir() and (p/'SKILL.md').is_file()}; assert len(n)==len(set(n)) and set(n)>=e; assert all(next(x for x in s if x['name']==k)['category']=='harness' and next(x for x in s if x['name']==k)['source_path']==('.agents/skills/harness' if k=='harness' else f'.agents/skills/harness/{k}') and next(x for x in s if x['name']==k)['install_path']==('.agents/skills/harness' if k=='harness' else f'.agents/skills/harness/{k}') for k in e); print('PASS harness-catalog-inventory')"`
  Expected: `PASS harness-catalog-inventory`; root·모든 child가 중복 없이 canonical source/install path와 harness category를 가짐.
- [x] **Step 2.2: catalog viewer에 category 표시를 추가하고 nested source 회귀를 검증한다.** viewer는 root-boundary nested source 처리를 유지하면서 각 entry의 `category`를 카드·검색 대상에 표시하고, root 밖 source를 거부한다.
  Run: `python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output /tmp/agentos-all-skills.html && grep -q 'agentos-core-guidance' /tmp/agentos-all-skills.html && grep -q 'writing-plans' /tmp/agentos-all-skills.html && grep -q 'harness' /tmp/agentos-all-skills.html && python3 -m pytest -q tests/test_harness_skill_catalog.py -k viewer`
  Expected: harness/optional entry와 `category`가 생성 HTML에 나타나고 nested source 경계 회귀가 exit 0.

## Task 3: setup·project init·package 연결과 회귀

**사용자에게 보이는 마일스톤:** setup과 project init이 동일한 harness tree를 제공하고 기존 optional skill fallback을 깨지 않는다.

- [x] **Step 3.1: bundled/base 설치 경로를 정합시킨다.** `agentos-core-guidance`를 flat default 목록에서 제거하고 harness base copy/manifest가 root guide와 child를 함께 포함하게 한다.
  Run: `test -f tests/test_harness_skill_catalog.py && python3 -m pytest -q tests/test_harness_skill_catalog.py tests/test_common_base_resources.py`
  Expected: exit 0, bundled/package harness tests 전체 PASS.
- [x] **Step 3.2: project init과 read routing 회귀를 추가·실행한다.** AGENTS.md가 없는 임시 프로젝트에서 root/child가 설치되고, init 전에는 local fallback이 생기지 않으며, child는 명시 경로로만 읽힌다.
  Run: `test -f tests/test_harness_skill_catalog.py && python3 -m pytest -q tests/test_project_command.py tests/test_harness_skill_catalog.py`
  Expected: exit 0, project-init 및 routing tests 전체 PASS.

- [x] **Step 3.3: 프로젝트 요구사항·시스템 계약을 동기화한다.** 사용자에게 보이는 canonical harness tree, catalog category/path, opt-in project init 경계를 관련 root 문서에 기록하고 기존 REQ-HARNESS-002 및 global-skill 경계를 보존한다.
  Run: `grep -q 'REQ-HARNESS-002-d' .agentos/project/02-product-scope-and-requirements.md && grep -q '핵심 harness는 그 아래' .agentos/project/03-system-contract.md && echo 'PASS project-contract-sync'`
  Expected: 요구사항과 시스템 계약이 canonical harness tree·catalog·project init 경계를 함께 설명함.

## Task 4: manifest·public suite·Gate 2 closeout

**사용자에게 보이는 마일스톤:** 하네스 구조의 무결성과 전체 설치/검증 근거가 남는다.

- [x] **Step 4.1: protected manifest를 승인된 아키텍트로 동기화한다.**
  Run: `test -f .agents/traces/reviews/harness-skill-catalog-hierarchy-plan/harness-architect-approval.json && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: 승인 artifact가 먼저 존재하고 manifest update/check가 모두 PASS.
- [x] **Step 4.2: public suite와 lifecycle을 실행한다.**
  Run: `bash scripts/verify-public-test-suite.sh && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`
  Expected: `PASS agentos-public-suite` 및 lifecycle refresh exit 0.
- [x] **Step 4.3: 진화 상태와 closeout trace를 기록한다.** 구현 결과·검증·다음 행동을 `.agentos/project/exec-plans/evolution-status.md`와 active plan closeout에 남긴다.
  Run: `grep -q 'harness-skill-catalog-hierarchy-20260830' .agentos/project/exec-plans/evolution-status.md && grep -q 'classification=harness-evolution' .agentos/project/exec-plans/evolution-status.md && echo 'PASS evolution-trace'`
  Expected: 진화 trigger·classification·result·verification·next action이 사용자용 status surface에 기록됨.
- [x] **Step 4.4: Gate 2 reviewer evidence의 closeout 유효성을 재확인한다.** 구현 중 living metadata와 closeout 섹션만 바뀌었고 승인된 계획 범위가 변하지 않았는지 확인한다.
  Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md --json && test -f .agents/traces/reviews/harness-skill-catalog-hierarchy-plan/signed_review.json && echo 'PASS gate2-closeout-evidence'`
  Expected: Gate 2 reviewer artifact와 signed review가 현재 계획에 대해 계속 유효하며 `PASS gate2-closeout-evidence`가 출력됨.

## Simplicity Gate

- 새 runtime이나 recursive executor는 만들지 않고 root `SKILL.md`를 routing 문서로 제한한다.
- catalog는 본문 복제가 아니라 canonical path/category metadata만 관리한다.
- 기존 base resource/project init/package 경계를 재사용한다.
- protected-path 이동과 manifest update는 승인·리뷰·검증이 없으면 실행하지 않는다.

## 리뷰 반영 이력

- 2026-08-31: protected approval을 단순 문자열 preflight와 분리하고, 승인 artifact·현재 계획 hash·승인 범위를 구현 전 검증하도록 보강했다.
- 2026-08-31: catalog inventory가 root·전체 child·중복·canonical install path를 검증하도록 수정했다.
- 2026-08-31: 이미 구현된 viewer nested-path 처리는 재사용하고, viewer source 수정 대신 harness 회귀 테스트만 소유하도록 범위를 축소했다.

## 세션 중단 대비 체크포인트

- 현재 완료 범위: Gate 2 reviewer evidence, catalog category 등록, viewer 회귀, project init 중복 방지, 요구사항·시스템 계약 동기화.
- 미완료 작업: harness-architect 승인, canonical 이동, root guide, base/default skill 연결, project-init 최종 회귀, manifest/public suite/closeout.
- 다음 세션 첫 작업: `.agents/traces/reviews/harness-skill-catalog-hierarchy-plan/harness-architect-approval.json` 존재와 계획 hash 일치를 확인한다.
- 아직 안 한 검증: protected 이동 이후의 catalog inventory, base/project-init 전체 회귀, manifest update/check, public suite, evolution trace.
- 관련 HISTORY checkpoint: 루트 `HISTORY.md`가 현재 checkout에 없으므로 plan/review/lifecycle artifact를 사용한다.

## 구현 결과

- `agentos-core-guidance`의 SKILL/evals를 `.agents/skills/harness/agentos-core-guidance/`로 이동하고 flat/catalog 중복을 제거했다.
- harness root `SKILL.md`에 progressive disclosure, 명시적 child routing, prompt/data boundary, 자동 실행 금지 경계를 추가했다.
- catalog의 harness root와 모든 child를 canonical source/install path 및 `category: harness`로 등록했다.
- setup/base/project init은 root와 child를 하나의 nested harness tree로 제공하고 optional skills는 flat fallback으로 유지한다.

## 사용 방법

프로젝트 초기화 후 `.agents/skills/harness/SKILL.md`를 읽고 작업에 맞는 child
`SKILL.md`를 명시적으로 선택해 읽는다. 전체 skill inventory와 category/path는
catalog viewer 생성 HTML에서 검색할 수 있다.

## 완료 증거

- `PASS core-guidance-canonical-move`
- `PASS harness-root-routing-contract`
- `PASS harness-catalog-inventory`
- focused pytest: `20 passed`
- viewer pytest: `2 passed`
- sync manifest update/check: harness integrity `PASS`
- public suite: `PASS agentos-public-suite`
- Gate 2 closeout: `review_artifacts.py check` valid, signed review present

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active에 유지한다.
