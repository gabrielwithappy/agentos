# knowledge-curator harness 경로 정규화 구현 계획

> **상태:** 리뷰 대기 (완료 후 '완료'로 변경)<br>
> **작성일:** 2026-09-05<br>
> reviewed: false (리뷰 증거 파일 생성 전까지 절대 true로 변경 불가)<br>
> **usability_review_required:** false<br>
> user_request: 날짜가 붙어 혼동을 주는 knowledge-curator harness 경로를 canonical 이름으로 정리하는 계획만 작성한다. 이번 단계에서는 실제 변경을 실행하지 않는다.<br>
> active_agent: codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: chore/remove-manifest-governance)<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(- [ ]) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** .agents/skills/harness/2026-08-31-project-init-project-documents를 .agents/skills/harness/knowledge-curator로 정규화하여 스킬 이름·경로·catalog·harness 검증을 일치시킨다.

**사용자 결과 요약:** 사용자는 날짜가 붙은 내부 경로 대신 knowledge-curator라는 일관된 이름으로 동일한 장기지식 관리 스킬을 발견·설치·검증할 수 있다. 스킬 기능과 knowledge 문서 내용은 유지한다.

**의존성 분석:**
- 외부 의존성: 없음
- 내부 선행 조건: 다른 active 계획과 동시 실행하지 않는다.
- 스캔 기준: Git 상태, catalog/skills/catalog.json, harness source tree, public boundary, catalog viewer, knowledge-curator 및 harness 테스트.

**장기 적용 표면:**
- traceability surface: 이 active plan, Intent Sheet archive/reference/intent/intent-20260905-knowledge-curator-path-normalization.md, HISTORY.md, lifecycle board
- durable result surface: .agents/skills/harness/knowledge-curator/, catalog/skills/knowledge-curator/, catalog/skills/catalog.json, config/public-boundary.json, 관련 검증 테스트
- documentation-only exception: 없음. 계획 실행 후 실제 discovery/install source 경로가 정규화되는 변경이다.

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기 중. 실제 rename·삭제·manifest 수정은 아직 실행하지 않았다.

**아키텍처:**
- catalog/skills/knowledge-curator는 bundled skill의 기능 source로 보존한다.
- .agents/skills/harness에는 날짜 접두사가 아닌 frontmatter name과 동일한 knowledge-curator child 경로를 둔다.
- catalog와 public boundary는 canonical 경로만 가리키고, 이전 날짜 경로는 현재 active surface에서 제거한다. archive/HISTORY/trace의 역사 기록은 보존한다.

**기술 스택:** Git, Markdown, JSON, Python 3.11+, pytest, 기존 catalog viewer 및 public verifier

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 계획 초안 / 리뷰 대기 |
| 완료됨 | 날짜 경로와 canonical bundled skill의 SKILL.md 내용이 동일함을 확인; catalog가 기대하는 harness 경로가 현재 누락되어 viewer 경고가 발생함을 확인 |
| 현재 위치 | Intent Sheet와 active plan 작성 완료; 독립 Gate 2 리뷰 전 |
| 다음 단계 | Gate 2 PASS와 사용자 실행 승인 후에만 rename 및 경로 정합화를 실행 |
| 완료 신호 | canonical 경로만 존재하고 catalog viewer·knowledge-curator 테스트·harness 테스트·public verifier가 모두 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 날짜가 붙지 않은 knowledge-curator 경로와 일관된 discovery/install 결과 |
| 누구를 위한 것인가? | AgentOS 프로젝트를 초기화·설치·검증하는 개발자와 coding agent |
| 일상 사용에서 무엇이 달라지는가? | catalog와 harness가 서로 다른 경로를 가리키지 않으며, 동일한 스킬을 이름으로 찾을 수 있음 |
| 무엇은 바뀌지 않는가? | knowledge-curator 기능, catalog/skills/knowledge-curator 본문, docs/knowledge 콘텐츠, archive/HISTORY/trace 기록 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 범위와 충돌 고정 | 다른 active 계획과 충돌하지 않을 범위가 확정됨 | Intent Sheet, active plans, Git status | rg inventory PASS |
| 2. canonical 경로 정규화 | 날짜 경로가 harness/knowledge-curator로 바뀜 | .agents/skills/harness/ | canonical path PASS |
| 3. discovery 정합화 | catalog viewer에서 knowledge-curator가 누락 없이 보임 | catalog/skills/catalog.json, config/public-boundary.json, viewer | catalog-discovery PASS |
| 4. 기능 보존 검증 | knowledge-curator와 harness 기능이 유지됨 | tests, public verifier | focused tests 및 PASS agentos-public-suite |

## 리뷰 반영 이력

- 계획 초안: 날짜 접두사 경로를 기능 삭제가 아닌 canonical path normalization 대상으로 분류했다.
- Gate 2 리뷰 결과는 독립 reviewer artifact가 생성된 뒤 기록한다.

## 사전 실행 Gate와 closeout 경계

- 이 계획은 `.agents/` surface를 변경하므로 Gate 2 PASS를 구현 전에 확인한다.
- 다른 active 계획과 같은 파일을 동시에 수정하지 않는다.
- 이 계획은 실행 계획 작성만 완료하는 현재 턴에서 어떤 파일도 rename·삭제·수정하지 않는다.
- reviewer artifact 생성·self-signing·승인·lifecycle closeout은 구현 Task가 아니라 Gate 2와 closeout 절차에서 처리한다.

## 리뷰 범위

- 변경 범위: `.agents/skills/harness/2026-08-31-project-init-project-documents/**`, `.agents/skills/harness/knowledge-curator/**` (rename target), `catalog/skills/catalog.json`, `config/public-boundary.json`, 관련 harness/catalog 검증 surface
- required review: plan-reviewer PASS, principle-auditor PASS/CLEAN
- recovery: 구현 전 git status와 source/destination digest를 기록하고, rename 실패 시 Git rename 상태를 보존한 채 즉시 중단한다. 기능 삭제를 위한 git rm이나 history rewrite는 사용하지 않는다.

## 파일 구조

- 생성: 없음
- rename: .agents/skills/harness/2026-08-31-project-init-project-documents/ → .agents/skills/harness/knowledge-curator/
- 수정: config/public-boundary.json — 날짜 경로 항목을 canonical 경로 항목으로 정합화한다.
- 검증/필요 시 수정: catalog/skills/catalog.json — knowledge-curator의 source_path·install_path가 canonical harness 경로인지 확인하고, 이미 맞으면 내용은 바꾸지 않는다.
- 검증: catalog/skills/skill-catalog-viewer/scripts/generate_html.py, tests/test_knowledge_skill.py, tests/test_knowledge_curator_evals.py, tests/test_common_base_resources.py, scripts/verify-public-test-suite.sh
- 보존: catalog/skills/knowledge-curator/**, docs/knowledge/**, .agentos/project/exec-plans/archive/**, HISTORY.md, .agents/traces/**, 현재 미커밋 계획·README 변경

## 의존성 게이트

외부 서비스·credential·plugin·MCP·network 의존성은 없다. 모든 검증은 repository-local Git/Python/Bash/pytest 도구로 수행한다.

## Task 0: 실행 전 기준과 계획 충돌을 고정한다

**파일:**
- 읽기: AGENTS.md, .agentos/project/00-project-index.md, CONTRIBUTING.md, 두 active plan, catalog·harness source와 검증 파일
- 수정: 없음

**사용자에게 보이는 마일스톤:** 이 계획이 기존 manifest governance 계획과 충돌하지 않고, 현재 미커밋 변경을 덮어쓰지 않는 상태가 확인된다.

- [ ] **Step 0.1: non-main branch와 기존 변경을 확인한다.**

Run: test "$(git branch --show-current)" != "main" && git status --short --branch && echo 'PASS non-main-plan-branch'
Expected: non-main branch 상태가 출력되고 PASS non-main-plan-branch가 출력된다.

- [ ] **Step 0.2: source·target·catalog 상태를 읽기 전용으로 확인한다.**

Run: test -f .agents/skills/harness/2026-08-31-project-init-project-documents/SKILL.md && test -f catalog/skills/knowledge-curator/SKILL.md && cmp -s .agents/skills/harness/2026-08-31-project-init-project-documents/SKILL.md catalog/skills/knowledge-curator/SKILL.md && rg -n '"name": "knowledge-curator"|"source_path": ".agents/skills/harness/knowledge-curator"|"install_path": ".agents/skills/harness/knowledge-curator"' catalog/skills/catalog.json && echo 'PASS preflight-knowledge-curator-path'
Expected: source·bundled SKILL.md가 동일하고 catalog에 canonical source_path·install_path가 존재하며 PASS preflight-knowledge-curator-path가 출력된다.

## Task 1: harness skill 경로를 canonical 이름으로 정규화한다

**파일:**
- rename: .agents/skills/harness/2026-08-31-project-init-project-documents/** → .agents/skills/harness/knowledge-curator/**

**사용자에게 보이는 마일스톤:** 날짜가 붙은 경로가 사라지고 skill 이름과 디렉터리 이름이 knowledge-curator로 일치한다.

- [ ] **Step 1.1: 기능 파일 전체를 Git rename으로 이동한다.**

git mv는 파일 내용을 바꾸지 않고 directory path만 정규화한다. catalog/skills/knowledge-curator/**는 별도 source로 보존한다.

Run: git mv .agents/skills/harness/2026-08-31-project-init-project-documents .agents/skills/harness/knowledge-curator && test -f .agents/skills/harness/knowledge-curator/SKILL.md && ! test -e .agents/skills/harness/2026-08-31-project-init-project-documents && cmp -s .agents/skills/harness/knowledge-curator/SKILL.md catalog/skills/knowledge-curator/SKILL.md && echo 'PASS harness-path-renamed'
Expected: PASS harness-path-renamed가 출력되고 이전 경로는 존재하지 않는다.

## Task 2: catalog와 public boundary discovery를 정합화한다

**파일:**
- 확인/필요 시 수정: catalog/skills/catalog.json
- 수정: config/public-boundary.json
- 검증: catalog/skills/skill-catalog-viewer/scripts/generate_html.py

**사용자에게 보이는 마일스톤:** catalog viewer가 knowledge-curator를 누락 없이 표시하고 public boundary가 이전 날짜 경로를 가리키지 않는다.

- [ ] **Step 2.1: catalog source/install path를 canonical 경로로 고정한다.**

catalog entry는 name: knowledge-curator, source_path: .agents/skills/harness/knowledge-curator, install_path: .agents/skills/harness/knowledge-curator를 사용해야 한다. 이미 이 값이면 변경하지 않는다.

Run: python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); e=next(x for x in d['skills'] if x['name']=='knowledge-curator'); assert e['source_path']=='.agents/skills/harness/knowledge-curator' and e['install_path']=='.agents/skills/harness/knowledge-curator'; print('PASS catalog-canonical-path')"
Expected: PASS catalog-canonical-path가 출력된다.

- [ ] **Step 2.2: generated public boundary를 canonical path로 갱신한다.**

현재 public boundary 생성·동기화 절차를 사용해 old path 항목을 canonical path 항목으로 교체하고, canonical source tree의 모든 파일이 누락 없이 등록되었는지 확인한다. 다른 active 계획과 같은 파일을 동시에 갱신하지 않는다.

Run: ! rg -n '2026-08-31-project-init-project-documents' config/public-boundary.json && rg -n 'agents/skills/harness/knowledge-curator/' config/public-boundary.json && echo 'PASS public-boundary-canonical-path'
Expected: old path가 검색되지 않고 canonical path가 검색되며 PASS public-boundary-canonical-path가 출력된다.

- [ ] **Step 2.3: catalog viewer 누락 경고와 표시를 검증한다.**

Run: catalog_tmp=$(mktemp -d) && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output "$catalog_tmp/index.html" 2>"$catalog_tmp/stderr" && ! grep -q 'skipping knowledge-curator' "$catalog_tmp/stderr" && grep -q 'knowledge-curator' "$catalog_tmp/index.html" && echo 'PASS catalog-viewer-knowledge-curator'
Expected: generator가 exit 0이고 knowledge-curator 누락 경고가 없으며 PASS catalog-viewer-knowledge-curator가 출력된다.

## Task 3: 기능 보존과 전체 경계를 검증한다

**파일:**
- 검증: tests/test_knowledge_skill.py, tests/test_knowledge_curator_evals.py, tests/test_common_base_resources.py, scripts/verify-public-test-suite.sh
- 보존 확인: catalog/skills/knowledge-curator/**, docs/knowledge/**

**사용자에게 보이는 마일스톤:** 경로만 정리되고 knowledge-curator 기능과 일반 harness 설치가 유지된다.

- [ ] **Step 3.1: focused knowledge-curator와 harness 테스트를 실행한다.**

Run: pytest -q tests/test_knowledge_skill.py tests/test_knowledge_curator_evals.py tests/test_common_base_resources.py
Expected: 모든 수집된 테스트가 exit 0으로 통과한다.

- [ ] **Step 3.2: 이전 경로의 active 참조와 의도하지 않은 기능 삭제를 검사한다.**

Run: if rg -n '2026-08-31-project-init-project-documents' AGENTS.md .agents/agents .agents/skills/harness catalog/skills/catalog.json config/public-boundary.json agentos tests --glob '!**/archive/**' --glob '!**/traces/**'; then exit 1; else test -f catalog/skills/knowledge-curator/SKILL.md && test -f catalog/skills/knowledge-curator/scripts/knowledge.py && echo 'PASS active-reference-and-feature-preservation'; fi
Expected: active source·검증 표면에서 이전 경로가 검색되지 않고 bundled knowledge-curator 핵심 파일이 남아 PASS active-reference-and-feature-preservation이 출력된다.

- [ ] **Step 3.3: public boundary와 diff 형식을 검증한다.**

Run: bash scripts/verify-public-test-suite.sh && git diff --check
Expected: PASS agentos-public-suite 및 git diff --check exit 0.

## 구현 결과

(실행 승인·구현·검증 후 작성. 현재 계획 작성 단계에서는 미작성)

## 사용 방법

(구현 후 knowledge-curator canonical 경로와 catalog discovery 결과를 작성)

## 아카이브 결정

이 계획은 구현·Gate 2·검증이 모두 끝난 뒤에도 사용자 명시 요청 전까지 active에 둔다. archive는 공식 lifecycle 명령으로만 수행한다.
