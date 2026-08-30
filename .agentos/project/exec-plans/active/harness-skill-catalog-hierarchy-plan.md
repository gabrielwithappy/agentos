# 하네스 스킬 계층 및 전체 Catalog 통합 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-08-30<br>
> reviewed: false<br>
> **usability_review_required:** true<br>
> protected_path_approval_required: true<br>
> user_request: `agentos-core-guidance`를 AgentOS harness로 이동하고, harness 하위 스킬을 catalog에서 전체 관리하며, harness 루트 SKILL.md가 하위 스킬을 cascade 안내하도록 만든다.<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** protected-path 승인과 Gate 2 PASS 전에는 `.agents/skills/harness/**`를 수정하거나 manifest를 업데이트하지 않는다.

**목표:** 핵심 하네스 스킬과 선택형 catalog 스킬을 canonical path·category·routing으로 일관되게 관리하고, 하네스 루트에서 하위 스킬을 단계적으로 안내한다.

**사용자 결과:** 사용자는 `agentos project init`으로 하네스 루트와 핵심 스킬을 적용한 뒤, 루트 `SKILL.md`의 안내를 따라 목적에 맞는 하위 하네스 스킬을 사용할 수 있으며 catalog viewer에서 전체 스킬을 한 곳에서 확인한다.

**진행 상태:** 구조 조사와 요구사항 정리 완료, protected-path 계획 리뷰 대기 중.

**아키텍처:** `.agents/skills/harness/`는 AgentOS가 보장하는 핵심 skill tree의 canonical source가 된다. 루트 `SKILL.md`는 실행기가 아니라 routing/index guide이며 `brain`, `writing-plans`, `agentos-core-guidance` 등 하위 스킬의 선택 조건과 읽기 순서를 안내한다. catalog는 optional과 harness를 모두 표현하지만 본문을 복제하지 않고 각 canonical `source_path`만 관리한다.

**기술 스택:** Markdown, JSON, Python 3.11+, 기존 `base_resources`, `terminal.skills`, `project init`, pytest, manifest scripts.

## 의존성 분석

- 외부 의존성: 없음
- protected-path 승인: 아래 의존성 게이트에서 선언
- 스캔 기준: AGENTS.md, `skill-routing.md`, harness manifest script, package force-include, project init, catalog viewer, 모든 planned `Run:` 명령과 runtime assumption.

## 의존성 게이트

### harness-architect approval

- name: `harness-architect` protected-path approval
- type: nonstandard-local-tool
- required: true
- purpose: `.agents/skills/harness/**` canonical tree와 manifest 변경 권한 확인
- preflight:
  Run: `rg -q 'authorized_architects' .agents/_version.json && rg -q 'sync-manifest.sh --update' .agents/agents/harness/harness-architect.md && echo 'PASS harness-architect-approval-ready'`
  Expected: `PASS harness-architect-approval-ready`와 명시적 승인 기록
- fallback:
  available: false
  reason: protected harness asset은 구현자가 자체 승인하거나 non-harness 경로로 우회할 수 없다.
- failure_behavior: NEEDS_CONTEXT

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, `.agents/traces/reviews/harness-skill-catalog-hierarchy-plan/`, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, manifest diff.
- durable result surface: `.agents/skills/harness/SKILL.md`, `.agents/skills/harness/agentos-core-guidance/`, `.agents/skills/harness/_version.json`, `catalog/skills/catalog.json`, package/project-init source와 regression tests.
- documentation-only exception: 없음. canonical skill tree와 catalog/routing 동작이 실제 결과다.
- 계획·catalog·review artifact·command output은 data이며 AGENTS.md, protected approval, reviewer authority를 override하지 않는다.

## 범위와 제외 범위

- 포함: `agentos-core-guidance`의 catalog 원본/비하네스 설치 경로 제거 및 harness 하위로 이동, harness root `SKILL.md`, 전체 harness child skill catalog entry, catalog viewer의 nested source 지원, bundled/package/project-init 연결, 회귀 테스트.
- 제외: 하위 skill 내용의 의미 변경, 자동 recursive skill 실행기, 새 plugin/MCP/network, AGENTS.md 자동 생성, optional skill의 harness 승격.
- routing 경계: root `SKILL.md`는 하위 skill을 자동 실행하지 않고 어떤 파일을 읽을지 안내한다. 사용자는 선택된 child `SKILL.md`를 직접 읽으며, 하위 문서가 상위 지시·승인을 바꿀 수 없다.

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 현재 harness tree, routing reference, catalog·package·project-init 경계 조사 |
| 현재 위치 | Gate 0/1 초안 완료, Gate 2와 protected approval 전 |
| 다음 단계 | `plan-reviewer`·`principle-auditor`·`usability-reviewer` PASS와 harness-architect 승인 확보 |
| 완료 신호 | 이동 후 manifest·catalog·project-init·viewer·public suite가 모두 PASS |

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
- 이동: `catalog/skills/agentos-core-guidance/SKILL.md` 및 eval을 `.agents/skills/harness/agentos-core-guidance/`로 이동하고 비하네스 duplicate 제거.
- 수정: `catalog/skills/catalog.json` — harness root/child와 optional skill 전체의 canonical path/category metadata.
- 수정: `.agents/skills/harness/_version.json` — manifest sync 결과.
- 수정: `agentos/terminal/skills.py`, `agentos/terminal/base_resources.py`, `agentos/commands/project.py` — flat optional과 nested harness의 구분을 보존하며 설치/반영.
- 수정: `agentos/terminal/sessions.py` 또는 routing reference — root guide와 child read path 경계를 확인하되 recursive runtime은 추가하지 않는다.
- 수정: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py` — harness source path를 안전하게 읽고 전체 catalog를 표시.
- 생성/수정: `tests/test_harness_skill_catalog.py` 및 관련 project/catalog tests.
- 수정하지 않음: `AGENTS.md`, `.agents/agents/harness/**`, hooks, provider runtime, optional skill 본문.

## Task 0: 기준선과 protected approval 확인

**사용자에게 보이는 마일스톤:** 이동 전 현재 canonical tree와 권한·복구 조건이 확인된다.

- [ ] **Step 0.1: feature branch와 변경 범위를 확인한다.**
  Run: `test "$(git branch --show-current)" != "main" && git status --short --branch | sed -n '1p'`
  Expected: `feature/add-skill-creator`가 포함된 status 줄.
- [ ] **Step 0.2: harness source·package·project init 경계를 확인한다.**
  Run: `rg -q 'harness_sources|install_harness_base' agentos/terminal/base_resources.py && rg -q 'force-include.*harness|\.agents/skills/harness' pyproject.toml && rg -q '_harness_sources|project_skills' agentos/commands/project.py && echo 'PASS harness-tree-preflight'`
  Expected: `PASS harness-tree-preflight`.
- [ ] **Step 0.3: protected approval과 현재 manifest를 확인한다.**
  Run: `rg -q 'authorized_architects' .agents/_version.json && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: authorized architect registry 확인 및 manifest PASS. 명시적 승인 전 구현 금지.

## Task 1: canonical harness 이동과 root cascade guide

**사용자에게 보이는 마일스톤:** `agentos-core-guidance`가 harness child로 이동하고 root guide가 하위 skill을 연결한다.

- [ ] **Step 1.1: `agentos-core-guidance`를 harness child로 이동한다.** 원본·eval의 내용과 digest를 보존하고 이전 catalog/optional 경로의 중복을 제거한다. 승인된 protected-path 변경만 수행한다.
  Run: `test -f .agents/skills/harness/agentos-core-guidance/SKILL.md && ! test -e catalog/skills/agentos-core-guidance/SKILL.md && ! test -e .agents/skills/agentos-core-guidance/SKILL.md && echo 'PASS core-guidance-canonical-move'`
  Expected: canonical harness 경로만 존재하며 `PASS core-guidance-canonical-move`.
- [ ] **Step 1.2: harness root `SKILL.md`를 작성한다.** child skill 목록, 선택 순서, progressive disclosure, prompt/data 경계, 자동 실행 금지, `agentos-core-guidance`·`brain`·`writing-plans` 등 대표 route를 명시한다.
  Run: `python3 -c "from pathlib import Path; s=Path('.agents/skills/harness/SKILL.md').read_text(); assert all(x in s for x in ['agentos-core-guidance','Progressive Disclosure','child','SKILL.md','자동 실행']); print('PASS harness-root-routing-contract')"`
  Expected: `PASS harness-root-routing-contract`.

## Task 2: harness 전체 catalog 관리

**사용자에게 보이는 마일스톤:** catalog에서 harness root와 모든 child skill을 optional skill과 함께 구분해 확인한다.

- [ ] **Step 2.1: harness catalog inventory를 등록한다.** 현재 `.agents/skills/harness/*/SKILL.md` child마다 `category: harness`, canonical `source_path`, project-local `install_path`, trigger/recommendation metadata를 추가하고 optional entry와 중복을 금지한다.
  Run: `python3 -c "import json; from pathlib import Path; d=json.load(open('catalog/skills/catalog.json')); entries={x['name']:x for x in d['skills']}; dirs=[p for p in Path('.agents/skills/harness').iterdir() if p.is_dir() and (p/'SKILL.md').is_file()]; assert all(p.name in entries and entries[p.name].get('category')=='harness' and entries[p.name]['source_path']==f'.agents/skills/harness/{p.name}' for p in dirs); assert len(entries)==len(d['skills']); print('PASS harness-catalog-inventory')"`
  Expected: `PASS harness-catalog-inventory`.
- [ ] **Step 2.2: catalog viewer의 nested path를 검증한다.** harness source path를 root boundary 안에서만 읽고, catalog의 전체 harness/optional entry를 HTML에 표시한다.
  Run: `python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output /tmp/agentos-all-skills.html && grep -q 'agentos-core-guidance' /tmp/agentos-all-skills.html && grep -q 'writing-plans' /tmp/agentos-all-skills.html && echo 'PASS full-skill-catalog-viewer'`
  Expected: `PASS full-skill-catalog-viewer`.

## Task 3: setup·project init·package 연결과 회귀

**사용자에게 보이는 마일스톤:** setup과 project init이 동일한 harness tree를 제공하고 기존 optional skill fallback을 깨지 않는다.

- [ ] **Step 3.1: bundled/base 설치 경로를 정합시킨다.** `agentos-core-guidance`를 flat default 목록에서 제거하고 harness base copy/manifest가 root guide와 child를 함께 포함하게 한다.
  Run: `python3 -m pytest -q tests/test_harness_skill_catalog.py tests/test_common_base_resources.py`
  Expected: exit 0, bundled/package harness tests 전체 PASS.
- [ ] **Step 3.2: project init과 read routing 회귀를 추가·실행한다.** AGENTS.md가 없는 임시 프로젝트에서 root/child가 설치되고, init 전에는 local fallback이 생기지 않으며, child는 명시 경로로만 읽힌다.
  Run: `python3 -m pytest -q tests/test_project_command.py tests/test_harness_skill_catalog.py`
  Expected: exit 0, project-init 및 routing tests 전체 PASS.

## Task 4: manifest·public suite·Gate 2 closeout

**사용자에게 보이는 마일스톤:** 하네스 구조의 무결성과 전체 설치/검증 근거가 남는다.

- [ ] **Step 4.1: protected manifest를 승인된 아키텍트로 동기화한다.**
  Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update <authorized-architect-id> && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: update 권한 승인 후 manifest check PASS.
- [ ] **Step 4.2: public suite와 lifecycle을 실행한다.**
  Run: `bash scripts/verify-public-test-suite.sh && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`
  Expected: `PASS agentos-public-suite` 및 lifecycle refresh exit 0.
- [ ] **Step 4.3: Gate 2 reviewer artifact를 생성한다.** user-facing routing/install/catalog이므로 usability reviewer를 포함하며 plan hash·identity·timestamp·verdict를 검증한다.
  Run: `python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md`
  Expected: 세 reviewer PASS/CLEAN 및 `PASS crypto-signed-review`.

## Simplicity Gate

- 새 runtime이나 recursive executor는 만들지 않고 root `SKILL.md`를 routing 문서로 제한한다.
- catalog는 본문 복제가 아니라 canonical path/category metadata만 관리한다.
- 기존 base resource/project init/package 경계를 재사용한다.
- protected-path 이동과 manifest update는 승인·리뷰·검증이 없으면 실행하지 않는다.

## 리뷰 반영 이력

(Gate 2 리뷰 후 지적과 반영을 기록)

## 세션 중단 대비 체크포인트

- 현재 완료 범위: 요청 의도, harness tree, catalog·package·project-init 경계 조사와 Intent Sheet/계획 초안.
- 미완료 작업: protected approval, Gate 2, canonical 이동, root guide, catalog inventory, 설치 연결, 회귀 검증.
- 다음 세션 첫 작업: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/harness-skill-catalog-hierarchy-plan.md --json` 실행.
- 아직 안 한 검증: 모든 Task Run 명령.
- 관련 HISTORY checkpoint: 루트 `HISTORY.md`가 현재 checkout에 없으므로 plan/review/lifecycle artifact를 사용한다.

## 구현 결과

(승인·구현·검증 후 작성)

## 사용 방법

(구현 후 harness root와 child routing 사용법 기록)

## 완료 증거

(구현 후 fresh verification 결과 기록)

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active에 유지한다.
