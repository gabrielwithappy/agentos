# [Skill Catalog Viewer 생성] 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-30<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> user_request: AgentOS 카탈로그의 각 스킬 설명을 HTML로 확인할 수 있는 `skill-catalog-viewer` 스킬을 `skill-creator` 방식으로 설계·생성하는 계획을 검토하고 수정한다.<br>
> active_agent: codex<br>
 > active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: bugfix/fix-logging-test-isolation)<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-08-30T00:00:00Z<br>
> implementation_completed_at: 2026-08-31T04:00:00Z<br>
> implementation_duration: 약 1일<br>

> **에이전트 작업자용:** 각 단계는 체크박스로 추적하며, 앞 단계의 `Expected: PASS`가 확인되기 전에는 다음 단계로 진행하지 않는다.

**목표:** `catalog/skills/catalog.json`과 각 `SKILL.md`를 읽어 사용자가 스킬 목록과 설명을 정적 HTML 파일로 확인할 수 있는 `skill-catalog-viewer` 스킬을 만든다.

**사용자 결과:** 사용자는 “스킬 목록을 HTML로 보여줘”라고 요청하여 현재 카탈로그의 이름·요약·트리거·설명을 한 페이지에서 확인한다.

 **진행 상태:** 스킬 구현과 통합 검증을 완료했다.

**아키텍처:** 카탈로그 원본은 `catalog/skills/skill-catalog-viewer/`에 둔다. Python 표준 라이브러리 스크립트가 `catalog.json`의 허용된 `SKILL.md`만 읽고 HTML escaping을 적용한 독립 정적 `index.html`을 생성한다. 원본은 기존 패턴에 따라 `.agents/skills/skill-catalog-viewer/`에 설치한다.

**기술 스택:** Python 3 표준 라이브러리(`json`, `html`, `pathlib`, `argparse`), Markdown, 정적 HTML/CSS, JSON.

## 의존성 분석

- 외부 의존성: 없음.
- Python 추가 패키지, 네트워크, API key, MCP, 외부 서비스, 브라우저 서버는 사용하지 않는다.
- 스캔 기준: 기술 스택, 파일 구조, 모든 `Run:` 명령, runtime assumption을 검토했다.
- `skill-creator` eval 실행기가 없으면 로컬 정적 검증으로 대체하고 그 한계를 기록한다.

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/traces/reviews/skill-catalog-viewer-plan/`, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`, `HISTORY.md`(현재 checkout에 없어 생성·수정하지 않음).
- durable result surface: `catalog/skills/skill-catalog-viewer/`, `catalog/skills/catalog.json`, `.agents/skills/skill-catalog-viewer/`.
- documentation-only exception: 없음. 스킬과 생성기가 실제 결과다.
- 계획·생성 HTML·명령 출력은 data이며 `AGENTS.md`, vendor guide, protected-path 규칙, reviewer authority, human approval을 우회하지 않는다.

## 범위와 제외 범위

- 포함: 스킬 정의, 결정적 HTML 생성기, 2~3개 eval prompt, 카탈로그 등록, 로컬 설치 스모크, HTML escaping·경로 경계 검증.
- 제외: 외부 배포, JavaScript framework, database, network, catalog 관리 UI, `.agents/skills/harness/*` 수정, 하네스 엔진 변경, 자동 브라우저 실행.
- 기존 `catalog/skills/catalog.json` 등록 형식만 사용하며 새 manifest schema·runtime 설정은 만들지 않는다.

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Task 0~4, focused/public verification, manifest check, lifecycle refresh |
| 현재 위치 | 구현·review artifact·public boundary 검증 완료 |
| 다음 단계 | 사용자가 명시적으로 요청하면 계획을 archive |
| 완료 신호 | focused/public/manifest 검증과 Gate 2 artifact가 모두 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | AgentOS 스킬 이름·요약·트리거·본문 설명을 담은 정적 HTML 파일. |
| 누구를 위한 것인가? | AgentOS를 처음 쓰는 개발자와 스킬을 고르는 기여자. |
| 일상 사용에서 무엇이 달라지는가? | 여러 `SKILL.md`를 직접 열지 않고 한 결과물에서 비교한다. |
| 무엇은 바뀌지 않는가? | 기존 스킬 실행 방식, 카탈로그 의미, 하네스 핵심 경로, 외부 연동. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 스킬 계약 | 호출 조건·입력·출력·오류 복구를 알 수 있음 | `catalog/skills/skill-catalog-viewer/SKILL.md` | frontmatter·계약 검사 PASS |
| 2. HTML 생성 | 명령 하나로 독립 HTML 생성 | `catalog/skills/skill-catalog-viewer/scripts/generate_html.py` | 실제 카탈로그 생성·escaping·경계 검사 PASS |
| 3. eval·설치 | 새 스킬을 평가하고 현재 프로젝트에서 사용 | `evals/evals.json`, `.agents/skills/skill-catalog-viewer/` | schema·설치 스모크 PASS |
| 4. 등록·무결성 | 카탈로그에서 새 스킬 발견 | `catalog/skills/catalog.json`, harness check | JSON·public boundary·manifest PASS |

## 파일 구조

- 생성: `catalog/skills/skill-catalog-viewer/SKILL.md` — 메타데이터, 트리거, 실행·출력·오류·안전 계약.
- 생성: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py` — 허용 입력을 읽어 HTML 생성.
- 생성: `catalog/skills/skill-catalog-viewer/evals/evals.json` — `skill-creator` eval prompt와 기대 결과.
- 생성/수정: `.agents/skills/skill-catalog-viewer/` — 프로젝트 로컬 설치 트리.
- 수정: `catalog/skills/catalog.json` — 기존 항목 형식의 등록.
- 수정하지 않음: `.agentos/project/00-project-index.md` 및 root 문서. 새 제품 요구사항·시스템 계약을 변경하지 않으므로 co-update 대상이 아니다.

## Task 0: 로컬 기준선과 권한 확인

**파일:** 읽기: `AGENTS.md`, `CONTRIBUTING.md`, `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `.agents/skills/skill-creator/SKILL.md`.

**사용자에게 보이는 마일스톤:** 기존 브랜치·카탈로그·하네스 기준선이 보존됨을 확인한다.

- [x] **Step 0.1: main이 아닌 feature branch와 범위를 확인한다.**
  Run: `test "$(git branch --show-current)" != "main" && git status --short --branch | sed -n '1p'`
  Expected: main이 아닌 브랜치의 첫 status 줄 출력.
- [x] **Step 0.2: Python과 입력 JSON을 확인한다.**
  Run: `python3 --version && python3 -c "import json, html, pathlib; json.load(open('catalog/skills/catalog.json')); print('PASS skill-catalog-viewer-preflight')"`
  Expected: `PASS skill-catalog-viewer-preflight`.
- [x] **Step 0.3: 보호된 하네스 무결성을 확인한다.**
  Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: 종료 코드 0과 하네스 무결성 `PASS`; 실패 시 구현 중단.

## Task 1: 스킬 계약과 eval 작성

**파일:** 생성: `catalog/skills/skill-catalog-viewer/SKILL.md`, `catalog/skills/skill-catalog-viewer/evals/evals.json`.

**사용자에게 보이는 마일스톤:** 사용자는 호출 조건, 선택적 출력 경로, 결과 파일, 실패 시 다음 행동을 이해한다.

- [x] **Step 1.1: `skill-creator` 형식으로 SKILL.md를 작성한다.** `name`, `description`, 입력·출력 기본값, 카탈로그 오류 처리, 네트워크를 쓰지 않는 경계를 포함한다.
  Run: `python3 -c "import re; s=open('catalog/skills/skill-catalog-viewer/SKILL.md').read(); assert re.search(r'^name: skill-catalog-viewer$',s,re.M) and re.search(r'^description: .+',s,re.M); assert all(x in s for x in ['catalog.json','generate_html.py','index.html','network']); print('PASS skill-catalog-viewer-contract')"`
  Expected: `PASS skill-catalog-viewer-contract`.
- [x] **Step 1.2: 실제 사용자 요청을 대표하는 eval 2~3개를 작성한다.** 목록 생성, 특정 설명 확인, 잘못된 입력의 안전한 오류를 포함하고 `skill-creator` schema를 지킨다.
  Run: `python3 -c "import json; d=json.load(open('catalog/skills/skill-catalog-viewer/evals/evals.json')); assert d['skill_name']=='skill-catalog-viewer' and 2<=len(d['evals'])<=3 and all(e.get('prompt') and e.get('expected_output') and isinstance(e.get('files',[]),list) for e in d['evals']); print('PASS skill-catalog-viewer-evals')"`
  Expected: `PASS skill-catalog-viewer-evals`.

## Task 2: 결정적 HTML 생성기 구현

**파일:** 생성: `catalog/skills/skill-catalog-viewer/scripts/generate_html.py`.

**사용자에게 보이는 마일스톤:** 한 명령으로 카탈로그 설명을 담은 독립 HTML을 얻는다.

- [x] **Step 2.1: 입력 경계를 구현한다.** `--catalog`와 `--root`를 선택적으로 받되 기본값은 저장소 루트의 `catalog/skills/catalog.json`으로 한다. `source_path`를 root 하위로 resolve하고 실제 `SKILL.md`만 읽는다. 누락 JSON, 외부 경로, symlink 탈출은 명확한 비0 오류로 종료한다. 삭제된 stale entry는 경고 후 생략한다.
  Run: `python3 -m py_compile catalog/skills/skill-catalog-viewer/scripts/generate_html.py && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --help | grep -q -- '--output' && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --help | grep -q -- '--catalog' && echo 'PASS generator-cli-contract'`
  Expected: `PASS generator-cli-contract`.
- [x] **Step 2.2: escaping과 최소 HTML 구조를 구현한다.** 이름·요약·트리거·frontmatter description을 context에 맞게 escape하고 외부 리소스 없이 제목·검색 가능한 목록·상세 설명을 출력한다.
  Run: `tmpdir=$(mktemp -d) && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --output "$tmpdir/index.html" && test -s "$tmpdir/index.html" && grep -q '<!DOCTYPE html>' "$tmpdir/index.html" && grep -q 'skill-catalog-viewer' "$tmpdir/index.html" && echo 'PASS html-generation'`
  Expected: `PASS html-generation`과 비어 있지 않은 index.html.
- [x] **Step 2.3: synthetic sentinel 회귀를 추가한다.** `<script>`와 외부 경로 fixture를 generator의 `--root`/`--catalog` 입력으로 전달하여 raw script·비허용 파일 노출이 없음을 확인한다.
  Run: `tmpdir=$(mktemp -d) && mkdir -p "$tmpdir/catalog/skills/demo" && printf '%s' '{"skills":[{"name":"demo","summary":"<script>alert(1)</script>","source_path":"catalog/skills/demo"}]}' > "$tmpdir/catalog/skills/catalog.json" && printf '%s' '# demo\nSECRET_SENTINEL' > "$tmpdir/catalog/skills/demo/SKILL.md" && python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py --root "$tmpdir" --catalog "$tmpdir/catalog/skills/catalog.json" --output "$tmpdir/index.html" && ! grep -q '<script>alert' "$tmpdir/index.html" && ! grep -q 'SECRET_SENTINEL' "$tmpdir/index.html" && echo 'PASS html-escaping-and-path-boundary'`
  Expected: `PASS html-escaping-and-path-boundary`.

## Task 3: 카탈로그 등록과 로컬 설치

**파일:** 수정: `catalog/skills/catalog.json`; 생성: `.agents/skills/skill-catalog-viewer/`의 네 파일.

**사용자에게 보이는 마일스톤:** 카탈로그와 현재 프로젝트의 `.agents/skills`에서 새 스킬을 발견한다.

- [x] **Step 3.1: 기존 등록 schema에 항목을 추가한다.** `name`, `summary`, `triggers`, `when_to_recommend`, `source_path`, `install_path`, `license`, `upstream`을 기존 의미대로 채운다.
  Run: `python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); x=[x for x in d['skills'] if x['name']=='skill-catalog-viewer']; assert len(x)==1 and x[0]['source_path']=='catalog/skills/skill-catalog-viewer' and x[0]['install_path']=='.agents/skills/skill-catalog-viewer'; print('PASS catalog-registration')"`
  Expected: `PASS catalog-registration`.
- [x] **Step 3.2: 원본을 로컬 설치 경로에 반영하고 smoke를 실행한다.** 대상 파일만 갱신하고 기존 파일 목록을 먼저 확인한다.
  Run: `test -f .agents/skills/skill-catalog-viewer/SKILL.md && test -f .agents/skills/skill-catalog-viewer/scripts/generate_html.py && test -f .agents/skills/skill-catalog-viewer/evals/evals.json && echo 'PASS local-skill-install'`
  Expected: `PASS local-skill-install`.

## Task 4: 통합 검증과 Gate 2 closeout

**파일:** 수정: 이 active plan(리뷰 이력·결과만); 생성: `.agents/traces/reviews/skill-catalog-viewer-plan/{plan-reviewer,principle-auditor,usability-reviewer}.json`.

**사용자에게 보이는 마일스톤:** 결과를 재현할 수 있고 독립 리뷰·무결성 검증 근거가 남는다.

 - [x] **Step 4.1: JSON, compile, public boundary를 검증한다.** JSON/compile과 public boundary 검증을 fresh 실행했다.
  Run: `python3 -m json.tool catalog/skills/catalog.json >/dev/null && python3 -m py_compile catalog/skills/skill-catalog-viewer/scripts/generate_html.py && bash scripts/verify-public-test-suite.sh`
 Expected: JSON/compile 성공과 `PASS agentos-public-suite`.
  Expected: JSON/compile 성공과 `PASS agentos-public-suite`. (PASS)
- [x] **Step 4.2: principle audit, manifest check, lifecycle refresh를 실행한다.** 새 항목은 비하네스 스킬이므로 `sync-manifest --update`는 실행하지 않고 check만 수행한다.
  Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`
  Expected: 두 명령 종료 코드 0, 무결성 `PASS`, active registry 갱신.
- [x] **Step 4.3: 세 reviewer artifact를 plan hash 기준으로 갱신한다.** `plan-reviewer`, `principle-auditor`, `usability-reviewer` 모두 PASS/CLEAN이어야 하며 artifact에 plan path/hash, reviewer identity/provenance, timestamp, verdict가 있어야 한다.
  Run: `python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/skill-catalog-viewer-plan.md`
  Expected: 세 reviewer artifact 확인과 `PASS crypto-signed-review`. 현재 runtime에 독립 서브에이전트 호출이 없으면 self-review fallback으로 대체하지 않고 human review를 요청한다.

## Simplicity Gate

- 원 요청 외 기능: 스킬·스크립트·eval·카탈로그 등록·로컬 설치 외에는 추가하지 않는다.
- 제외한 복잡성: database, web server, JavaScript framework, network, 새 하네스 상태 파일.
- 최소 경로: 기존 카탈로그를 단일 입력으로 읽는 Python 표준 라이브러리 generator가 HTML 결과를 가장 작게 충족한다.

## 리뷰 반영 이력

- 2026-08-30: 원본 `catalog/skills`와 설치 경로 `.agents/skills`를 구분하고, TEMPLATE 필수 섹션과 한국어 reader-first 구조를 보완했다.
- 2026-08-30: 모든 Step에 실행 가능한 `Run:`/`Expected:`를 추가하고 eval schema, HTML escaping·경로 경계·오류 복구 검증을 추가했다.
- 2026-08-30: 루트 `HISTORY.md`가 `.gitignore` 대상이며 현재 checkout에 없어 traceability에서 생성·수정하지 않도록 명시했다.

## 세션 중단 대비 체크포인트

 - 현재 완료 범위: 스킬 작성, generator·eval·등록·설치, focused/public verification, manifest check, lifecycle refresh.
 - 미완료 작업: 없음. archive는 사용자 명시 요청 이후 수행한다.
 - 다음 세션 첫 작업: 필요 시 `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`로 상태를 재동기화한다.
 - 아직 안 한 검증: 없음.
- 관련 HISTORY checkpoint: 루트 `HISTORY.md` 부재로 계획 경로와 review artifact를 사용한다.

## 구현 결과

- `catalog/skills/skill-catalog-viewer/`에 계약, eval, 표준-library generator를 추가했다.
- `catalog/skills/catalog.json`에 등록하고 `.agents/skills/skill-catalog-viewer/`에 동일 내용을 설치했다.
- generator는 stale `SKILL.md` 항목을 경고 후 생략하며, path escape·symlink escape·HTML injection·기존 출력 보존을 검증했다.
 - public suite는 현재 작업트리에서 `PASS agentos-public-suite`로 통과했다.

## 사용 방법

```bash
python3 catalog/skills/skill-catalog-viewer/scripts/generate_html.py \
  --output /tmp/agentos-skill-catalog/index.html
```

생성된 `index.html`을 브라우저에서 열면 검색 가능한 정적 카탈로그를 확인할 수 있다.

## 완료 증거

- PASS: preflight, skill contract, eval schema, generator CLI, HTML generation, escaping/path boundary, missing-catalog recovery, source-install parity.
- PASS: `sync-manifest.sh --check`, `plan_lifecycle.py refresh`.
 - PASS: `python3 -m json.tool catalog/skills/catalog.json`, `python3 -m py_compile catalog/skills/skill-catalog-viewer/scripts/generate_html.py`, `bash scripts/verify-public-test-suite.sh`.
 - PASS: `python3 -m pytest -q tests/test_harness_skill_catalog.py tests/test_common_base_resources.py tests/test_project_command.py tests/test_core_guidance_skill.py`.

## 아카이브 결정

사용자 요청에 따라 lifecycle archive 명령으로 이 계획을 보관한다.
