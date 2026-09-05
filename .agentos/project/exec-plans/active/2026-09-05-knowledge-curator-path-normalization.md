---
status: 완료
date: 2026-09-05
reviewed: true
usability_review_required: false
user_request: 2026-09-05-knowledge-curator-path-normalization 계획을 구현하자
active_agent: antigravity
active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: feature/knowledge-curator-path-normalization)
dashboard_item_id:
implementation_started_at: 2026-09-05T02:23:00Z
implementation_completed_at: 2026-09-05T02:25:00Z
implementation_duration: 2m
next_action: user archive decision
---

# knowledge-curator harness 경로 정규화 구현 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- `.agents/skills/harness/2026-08-31-project-init-project-documents/`를 `.agents/skills/harness/knowledge-curator/`로 정규화하여 스킬 이름, 디렉터리 경로, catalog 및 harness 검증을 일치시킨다.

**사용자 결과 요약:**
- 사용자는 날짜가 붙은 임시 경로 대신 `knowledge-curator`라는 일관된 canonical 이름으로 동일한 장기지식 관리 스킬을 카탈로그 뷰어에서 확인하고 하네스에서 사용할 수 있다. 스킬 기능과 knowledge 문서 내용은 온전히 보존된다.

**의존성 분석:**
- 외부 의존성: 없음
- 내부 선행 조건: 선행 계획(`2026-09-05-remove-manifest-governance.md`)이 이미 `main`에 완료 및 아카이브되어 동시성 충돌 없음. 다른 active 계획 없음.
- 스캔 기준: Git 상태, `catalog/skills/catalog.json`, `config/public-boundary.json`, harness source tree, catalog viewer, knowledge-curator 및 harness 테스트.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, Intent Sheet `archive/reference/intent/intent-20260905-knowledge-curator-path-normalization.md`, `HISTORY.md`, generated plan board
- Durable Result Surface: `.agents/skills/harness/knowledge-curator/`, `catalog/skills/knowledge-curator/`, `catalog/skills/catalog.json`, `config/public-boundary.json`, 관련 검증 테스트
- Documentation-Only Exception: 없음. 실제 discovery/install source 경로가 정규화되는 구조적 변경이다.

**진행 상태:** 계획 초안 작성, 독립 리뷰 대기 중

**아키텍처:**
- `catalog/skills/knowledge-curator/`는 번들 스킬의 기능 source로 보존한다.
- `.agents/skills/harness/`에는 날짜 접두사가 아닌 frontmatter name과 일치하는 `knowledge-curator/` 디렉터리를 둔다.
- `catalog/skills/catalog.json`과 `config/public-boundary.json`은 canonical 경로만 가리키고, 이전 날짜 경로는 현재 active surface에서 제거한다. `HISTORY.md`, `archive/`, `traces/`의 역사 기록은 보존한다.

**기술 스택:** Git, Markdown, JSON, Python 3.11+, pytest, 기존 catalog viewer 및 public verifier

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 구현 계획 (리뷰 대기) |
| 완료됨 | 날짜 경로와 canonical bundled skill의 SKILL.md 내용이 동일함을 확인; catalog viewer 경고 원인(harness 경로 불일치) 확인 |
| 현재 위치 | Gate 2 독립 서브에이전트 리뷰 대기 |
| 다음 단계 | plan-reviewer 및 principle-auditor PASS 후 구현 착수 |
| 완료 신호 | canonical 경로만 존재하고 catalog viewer 경고 해소, knowledge-curator/harness 테스트 27/27 PASS, public suite PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 날짜가 붙지 않은 `knowledge-curator` 경로와 일관된 discovery/install 결과 |
| 누구를 위한 것인가? | AgentOS 프로젝트를 초기화·설치·검증하는 개발자와 coding agent |
| 일상 사용에서 무엇이 달라지는가? | catalog viewer에서 knowledge-curator 누락 경고가 사라지고, catalog와 harness가 일치된 이름을 사용함 |
| 무엇은 바뀌지 않는가? | knowledge-curator 기능, `catalog/skills/knowledge-curator/` 본문, `docs/knowledge/` 콘텐츠, `archive/`, `HISTORY.md`, `traces/` 기록 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 사전 검증 및 디렉터리 이동 | 기능 파일 내용 손실 없이 canonical 경로로 이동됨 | `.agents/skills/harness/` | `git mv` 및 digest 동일성 검증 |
| 2. discovery 및 경계 정합화 | public-boundary와 catalog viewer에서 정상 인식 | `config/public-boundary.json`, viewer | `generate_html.py` 경고 해소 및 public-boundary 16개 항목 교체 확인 |
| 3. 기능 보존 및 전체 검증 | knowledge-curator 기능과 전체 하네스가 안정적으로 통과 | tests, harness suite, public suite | focused pytest 16개 통과, harness 27/27 통과, public suite PASS |

## 리뷰 반영 이력

- 1차 독립 리뷰(2026-09-05) 지적 사항 반영:
  1. PA-001 (경로 선언): 명확한 파일 및 디렉터리 경로 명시 (`.agents/skills/harness/2026-08-31-project-init-project-documents/`, `.agents/skills/harness/knowledge-curator/`, `config/public-boundary.json`, `catalog/skills/catalog.json`). manifest 거버넌스는 선행 계획에서 공식 제거되었으므로 불필요한 pseudo-path 의존성 제거.
  2. PA-002 (동시성 중복): 선행 계획(`2026-09-05-remove-manifest-governance.md`)이 이미 `main`에 완료 및 아카이브되어 동시성 충돌 없음.
  3. PA-003 (검증 완전성): Task 3에 전체 하네스 검증기(`bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`) 및 public-boundary 정확한 엔트리 수(16개 old path 삭제, 16개 canonical path 등록) 검증 추가.
  4. PA-004 (복구 실행성): `git mv` 전후의 디렉터리/파일 해시 및 상태 확인 커맨드와 롤백 절차 명시.
  5. PA-005 (단일 실행 경로): 조건 분기를 제거하고 단일 확정 경로로 정리.

## 사전 실행 Gate와 closeout 경계

- 이 계획은 `.agents/` surface를 변경하므로 Gate 2 PASS를 구현 전에 확인한다.
- 다른 active 계획과 같은 파일을 동시에 수정하지 않는다.
- reviewer artifact 생성·검증 및 closeout은 구현 Task가 아니라 Gate 2와 closeout 절차에서 처리한다.

## 리뷰 범위

- 변경 범위:
  - `.agents/skills/harness/2026-08-31-project-init-project-documents/**`
  - `.agents/skills/harness/knowledge-curator/**`
  - `config/public-boundary.json`
  - `catalog/skills/catalog.json`
- required review: `plan-reviewer` PASS, `principle-auditor` PASS/CLEAN
- recovery: 구현 전 git status와 source digest를 기록하고, rename 실패 시 `git checkout` 또는 `git mv` 역방향으로 롤백한다. 기능 삭제를 위한 임의 파일 삭제나 history rewrite는 금지한다.

## Task 0: 실행 전 기준과 선행 조건 확인

**파일:**
- 읽기: `AGENTS.md`, `CONTRIBUTING.md`, `catalog/skills/catalog.json`, `config/public-boundary.json`
- 수정: 없음

**사용자에게 보이는 마일스톤:** non-main 브랜치 상태와 source/target/catalog 상태가 확인된다.

- [x] **Step 0.1: feature 브랜치 상태를 확인한다.**

Run: `test "$(git branch --show-current)" = "feature/knowledge-curator-path-normalization" && git status --short && echo 'PASS branch-preflight'`
Expected: `PASS branch-preflight`

- [x] **Step 0.2: source 및 catalog 상태를 확인한다.**

Run: `test -f .agents/skills/harness/2026-08-31-project-init-project-documents/SKILL.md && test -f catalog/skills/knowledge-curator/SKILL.md && cmp -s .agents/skills/harness/2026-08-31-project-init-project-documents/SKILL.md catalog/skills/knowledge-curator/SKILL.md && python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); e=next(x for x in d['skills'] if x['name']=='knowledge-curator'); assert e['source_path']=='.agents/skills/harness/knowledge-curator' and e['install_path']=='.agents/skills/harness/knowledge-curator'" && echo 'PASS preflight-knowledge-curator-path'`
Expected: `PASS preflight-knowledge-curator-path`

## Task 1: harness skill 디렉터리를 canonical 이름으로 정규화한다

**파일:**
- rename: `.agents/skills/harness/2026-08-31-project-init-project-documents/**` → `.agents/skills/harness/knowledge-curator/**`

**사용자에게 보이는 마일스톤:** 날짜 접두사 경로가 사라지고 디렉터리 이름이 `knowledge-curator`로 일치한다.

- [x] **Step 1.1: 기능 파일 전체를 Git rename으로 이동한다.**

`git mv`로 디렉터리를 이동하고, 이동 후 16개 파일이 그대로 유지되며 SKILL.md 내용이 catalog 원본과 일치하는지 확인한다.

Run: `git mv .agents/skills/harness/2026-08-31-project-init-project-documents .agents/skills/harness/knowledge-curator && test -f .agents/skills/harness/knowledge-curator/SKILL.md && ! test -e .agents/skills/harness/2026-08-31-project-init-project-documents && cmp -s .agents/skills/harness/knowledge-curator/SKILL.md catalog/skills/knowledge-curator/SKILL.md && echo 'PASS harness-path-renamed'`
Expected: `PASS harness-path-renamed`

## Task 2: public boundary 및 catalog discovery 정합화

**파일:**
- 수정: `config/public-boundary.json`
- 검증: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py`

**사용자에게 보이는 마일스톤:** `config/public-boundary.json`이 갱신되고, catalog viewer에서 knowledge-curator 누락 경고가 사라진다.

- [x] **Step 2.1: public-boundary.json의 16개 경로를 canonical 경로로 치환한다.**

`2026-08-31-project-init-project-documents`를 `knowledge-curator`로 치환하여 16개 엔트리가 정확히 갱신되도록 한다.

Run: `python3 -c "import json; p='config/public-boundary.json'; d=json.load(open(p)); d['files']=[f.replace('.agents/skills/harness/2026-08-31-project-init-project-documents/', '.agents/skills/harness/knowledge-curator/') for f in d['files']]; json.dump(d, open(p, 'w'), indent=2); print('updated')"`
Expected: exit 0

Run: `python3 -c "import json; d=json.load(open('config/public-boundary.json')); old=[f for f in d['files'] if '2026-08-31-project-init-project-documents' in f]; new=[f for f in d['files'] if '.agents/skills/harness/knowledge-curator/' in f]; assert len(old)==0 and len(new)==16, f'old={len(old)}, new={len(new)}'; print('PASS public-boundary-canonical-path')"`
Expected: `PASS public-boundary-canonical-path`

- [x] **Step 2.2: catalog viewer 누락 경고 해소를 검증한다.**

Run: `catalog_tmp=$(mktemp -d) && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output "$catalog_tmp/index.html" 2>"$catalog_tmp/stderr" && ! grep -q 'skipping knowledge-curator' "$catalog_tmp/stderr" && grep -q 'knowledge-curator' "$catalog_tmp/index.html" && echo 'PASS catalog-viewer-knowledge-curator'`
Expected: `PASS catalog-viewer-knowledge-curator`

## Task 3: 기능 보존 및 전체 검증

**파일:**
- 검증: `tests/test_knowledge_skill.py`, `tests/test_knowledge_curator_evals.py`, `tests/test_common_base_resources.py`, `scripts/verify-public-test-suite.sh`, `.agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh`

**사용자에게 보이는 마일스톤:** knowledge-curator 기능, 하네스 전체 무결성, 공개 테스트 스위트가 모두 정상 통과한다.

- [x] **Step 3.1: 포커스 테스트를 실행한다.**

Run: `pytest -q tests/test_knowledge_skill.py tests/test_knowledge_curator_evals.py tests/test_common_base_resources.py`
Expected: 16 passed

- [x] **Step 3.2: 이전 경로의 잔존 참조 유무 및 기능 보존을 검사한다.**

Run: `if rg -n '2026-08-31-project-init-project-documents' AGENTS.md .agents/agents .agents/skills/harness catalog/skills/catalog.json config/public-boundary.json agentos tests --glob '!**/archive/**' --glob '!**/traces/**' --glob '!HISTORY.md'; then exit 1; else test -f catalog/skills/knowledge-curator/SKILL.md && test -f catalog/skills/knowledge-curator/scripts/knowledge.py && echo 'PASS active-reference-and-feature-preservation'; fi`
Expected: `PASS active-reference-and-feature-preservation`

- [x] **Step 3.3: 공개 테스트 스위트 및 하네스 전체 검증을 실행한다.**

Run: `bash scripts/verify-public-test-suite.sh && bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh && git diff --check`
Expected: `PASS agentos-public-suite`, `PASS=27 FAIL=0`, `git diff --check` clean exit 0.

## 구현 결과

1. **하네스 스킬 경로 정규화:**
   - `.agents/skills/harness/2026-08-31-project-init-project-documents/`를 `git mv`를 통해 `.agents/skills/harness/knowledge-curator/`로 이동 완료.
   - 이동 후 16개 파일의 무결성과 `SKILL.md` 내용 보존 확인.
2. **공개 경계(`config/public-boundary.json`) 및 카탈로그 디스커버리 정합화:**
   - `config/public-boundary.json`에서 구 임시 경로(`2026-08-31-project-init-project-documents`) 16개 항목을 완전히 정리하고, canonical 경로(`knowledge-curator`) 16개 항목만 정상 유지되도록 치환/정리 완료.
   - `skill-catalog-viewer`의 `generate_html.py` 실행 시 발생하던 `warning: skipping knowledge-curator; SKILL.md is missing` 경고가 완전히 해소되고 정상 카탈로그 HTML이 생성됨을 확인.
3. **전체 테스트 검증 통과:**
   - 포커스 테스트(16 passed), 잔존 구 경로 참조 없음 확인, `verify-public-test-suite.sh` PASS, 하네스 테스트 27/27 전체 PASS, `git diff --check` 클린 확인.

## 사용 방법

1. **하네스 스킬 참조:**
   - 에이전트 또는 프로젝트에서 장기 지식 큐레이터 스킬을 참조할 때 canonical 경로인 `.agents/skills/harness/knowledge-curator/`를 사용한다.
2. **카탈로그 뷰어 생성:**
   - `python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output catalog.html`를 실행하여 누락 경고 없이 `knowledge-curator` 스킬 정보를 온전히 조회할 수 있다.

## 완료 증거

- `pytest -q tests/test_knowledge_skill.py tests/test_knowledge_curator_evals.py tests/test_common_base_resources.py` → 16 passed
- `python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py` → skipping 경고 없음
- `bash scripts/verify-public-test-suite.sh` → PASS agentos-public-suite
- `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh` → PASS=27 FAIL=0
- `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-05-knowledge-curator-path-normalization.md` → PASS gate2-review-check
- `git diff --check` → Clean

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active 디렉토리에 유지한다.
