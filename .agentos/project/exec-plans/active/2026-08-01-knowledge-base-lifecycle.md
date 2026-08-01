# 장기지식 저장·검토·publish·검색 흐름 구현 계획

> **상태:** 완료<br>
> **작성일:** 2026-08-01<br>
> reviewed: false<br>
> user_request: AgentOS의 장기지식 계획을 실제 사용자용 저장·검토·publish·검색 흐름으로 구현하고, 기존 조사 결과를 이후 계획에서 재사용할 수 있게 한다.<br>
> active_agent: codex<br>
> active_session: main checkout; post-merge review artifact remediation<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg04yN4<br>
> implementation_started_at: 2026-08-01T13:18:31Z<br>
> implementation_completed_at: 2026-08-01T13:23:39Z<br>
> implementation_duration: 5m 8s<br>
> **usability_review_required:** true<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** Markdown·JSON·파일 시스템만으로 장기지식의 저장, 사용자 검토, publish, 키워드 검색, 근거 인용을 제공한다.

**사용자 결과:** 사용자는 `docs/knowledge`에서 승인된 지식을 찾고, 에이전트 조사 결과를 inbox에서 검토·publish한 뒤 CLI로 재검색·인용할 수 있다.

**진행 상태:** 구현·검증·main 병합·로컬 feature branch 삭제 완료. Stop hook 지적으로 current checkout의 리뷰 증거를 재생성 중.

**아키텍처:** 에이전트 또는 사용자가 Markdown 초안을 `docs/knowledge/inbox/`에 저장하고, CLI가 메타데이터와 상태를 검증한 뒤 `references/`, `topics/`, `decisions/` 중 하나로 publish한다. 검색은 파일 인덱스 또는 재현 가능한 키워드 스캔을 사용하며, 결과에는 문서 경로와 근거 위치를 포함한다.

**기술 스택:** Python 표준 라이브러리, Markdown, JSON 인덱스, Typer/Rich 기반 기존 AgentOS CLI, pytest

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 지식 문서 계약, 파일 store lifecycle, `agentos knowledge` CLI, 검색/context 인용, 사용자 문서, project index/requirement trace, curator 지침 업데이트 |
| 현재 위치 | main checkout에 구현 병합 완료, fresh Gate 2 review artifact 재생성 중 |
| 다음 단계 | 독립 리뷰 PASS artifact 기록 후 `reviewed: true` 복구 |
| 완료 신호 | 저장·검토·publish·검색·인용 CLI의 focused pytest와 manifest check가 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `docs/knowledge`에서 지식을 찾고, inbox 초안을 검토·publish하고, 검색 결과와 원문 인용을 확인한다. |
| 누구를 위한 것인가? | 장기 조사 결과를 보존하려는 프로젝트 사용자와 후속 계획을 작성하는 AgentOS 에이전트 |
| 일상 사용에서 무엇이 달라지는가? | 조사 결과를 trace나 임시 계획에만 남기지 않고 검토 가능한 knowledge inbox에 저장한 뒤 다시 검색할 수 있다. |
| 무엇은 바뀌지 않는가? | 벡터 DB·임베딩 검색·외부 자동 수집·자동 publish·Slack/GitHub 직접 연동·기존 Gate 2 권한 모델은 이번 범위에서 바꾸지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 지식 저장소 구조와 문서 계약 | `docs/knowledge/index.md`, `inbox/`, `references/`, `topics/`, `decisions/`가 보이고 문서 메타데이터 규칙을 확인할 수 있음 | `docs/knowledge/`, `agentos/knowledge/` | `python3 -m pytest tests/test_knowledge_store.py -q` / Expected: PASS |
| 2. 검토·publish 흐름 | inbox 문서의 메타데이터를 검사하고 승인된 category로 publish할 수 있음 | `agentos/commands/knowledge.py`, `agentos/knowledge/` | `python3 -m pytest tests/test_knowledge_cli.py -q` / Expected: PASS |
| 3. 키워드 검색·인용 출력 | 검색 결과가 문서 경로·제목·태그·근거 위치를 포함해 출력됨 | `agentos/knowledge/search.py`, CLI | `agentos knowledge search "..."` / Expected: 결과와 인용 경로 출력 |
| 4. 사용자 문서·프로젝트 인덱스 연결 | 사용자가 지식 흐름을 한 곳에서 찾고 다음 행동을 알 수 있음 | `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `docs/knowledge/index.md`, `docs/knowledge/README.md` | `grep -n "agentos knowledge\|docs/knowledge\|publish" .agentos/project/00-project-index.md docs/knowledge/index.md docs/knowledge/README.md` / Expected: 사용자 명령과 경로 매치 |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agents/traces/research/2026-08-01-llm-connection-patterns-pi-hermes-aionui-qm.md`, `.agentos/project/exec-plans/README.md`, `.agentos/project/exec-plans/evolution-status.md`
- durable result surface: `docs/knowledge/`, `agentos/knowledge/`, `agentos/commands/knowledge.py`, 프로젝트 인덱스와 사용자 가이드
- documentation-only exception: 없음. 사용자용 문서와 파일 기반 knowledge runtime을 함께 추가한다.

## Worktree Execution Record

- canonical skill: `git-worktree-parallel`
- 이 섹션은 현재 실행 지시가 아니라 구현 당시 사용한 격리 기록이다.
- 격리 사유: main checkout에는 다른 세션이 작업 중인 미커밋 변경이 있어, 이 계획의 작성·구현·커밋 흐름을 main checkout과 분리해야 했다.
- historical worktree path: `.agentos/worktrees/knowledge-base-plan`
- historical branch: `feature/knowledge-base-plan` (base: `main`, 실제 생성 시점의 `main` HEAD `3b2f6d5`)
- current state: 구현은 `main`에 merge commit `e70ec1d`로 병합됐고, historical worktree와 local feature branch는 삭제됐다.
- 현재 다음 행동: main checkout에서 missing Gate 2 review artifact만 재생성하고, PASS evidence가 생긴 뒤 `reviewed: true`를 복구한다.
- 당시 검증 명령:
  Run: `git worktree list`
  Expected: `.agentos/worktrees/knowledge-base-plan`가 `feature/knowledge-base-plan` 브랜치로 표시됨
  Run: `git -C .agentos/worktrees/knowledge-base-plan branch --show-current`
  Expected: `feature/knowledge-base-plan`

## 범위와 비목표

### 포함

- Markdown 지식 문서의 필수 frontmatter/metadata 계약
- `inbox`, `references`, `topics`, `decisions` lifecycle
- draft 검증, publish, update, deprecate 상태 흐름
- 파일 기반 키워드 검색과 경로/섹션 인용 출력
- 지식 index 생성 또는 갱신
- 사용자용 CLI 도움말·가이드와 프로젝트 SSOT 인덱스 연결
- 사용자 publish 권한의 별도 제한을 초기 범위에서 두지 않음

### 제외

- SQLite/Postgres 같은 무거운 데이터베이스
- 벡터 DB, 임베딩, 의미 검색
- Slack/GitHub webhook 자동 수집
- 에이전트의 자동 publish 또는 승인 우회
- 기존 조사 문서의 일괄 publish
- 계획 작성 흐름에 자동 검색을 강제 삽입하는 통합 변경

## 파일 구조

- 생성: `docs/knowledge/README.md` — 사용자용 시작점, lifecycle과 명령 예시
- 생성: `docs/knowledge/index.md` — 지식 문서 카탈로그와 category별 링크
- 생성: `docs/knowledge/inbox/.gitkeep` — 검토 전 초안 영역
- 생성: `docs/knowledge/references/.gitkeep` — 승인된 참고 지식 영역
- 생성: `docs/knowledge/topics/.gitkeep` — 승인된 주제 지식 영역
- 생성: `docs/knowledge/decisions/.gitkeep` — 승인된 결정 지식 영역
- 생성: `agentos/knowledge/__init__.py` — knowledge 도메인 공개 함수
- 생성: `agentos/knowledge/schema.py` — metadata 파싱·검증·상태 계약
- 생성: `agentos/knowledge/store.py` — 파일 탐색·draft/publish/update/deprecate 저장 동작
- 생성: `agentos/knowledge/search.py` — 키워드 검색·인용 위치 계산
- 생성: `agentos/commands/knowledge.py` — `agentos knowledge` CLI 명령
- 수정: `agentos/cli.py` — knowledge typer app 등록
- 수정: `.agentos/project/00-project-index.md` — knowledge supporting surface 등록
- 수정: `.agents/agents/harness/knowledge-curator.md` — 실제 AgentOS CLI·경로와 현재 운영 규칙 정합화. Protected `.agents` 경로이므로 `codex` authorized architect 확인, `principle-auditor` PASS/CLEAN, `sync-manifest --update codex`, `sync-manifest --check`가 필요하다.
- 생성: `tests/test_knowledge_store.py` — schema/store lifecycle focused tests
- 생성: `tests/test_knowledge_cli.py` — CLI 출력·검색·인용 focused tests
- 수정: `.gitignore` — 기존 `knowledge/` ignore rule은 유지하되 `agentos/knowledge/**`와 `docs/knowledge/**`를 추적 가능한 durable result surface로 허용하고 `agentos/knowledge/__pycache__/`와 `*.pyc`는 계속 제외한다.

## Task 1: 지식 문서 계약과 파일 저장소 만들기

**파일:**
- 생성: `docs/knowledge/README.md`, `docs/knowledge/index.md`, category directories
- 생성: `agentos/knowledge/__init__.py`, `agentos/knowledge/schema.py`, `agentos/knowledge/store.py`
- 생성: `tests/test_knowledge_store.py`

**사용자에게 보이는 마일스톤:** 사용자가 초안을 넣을 위치와 승인된 지식의 category를 알 수 있고, 잘못된 metadata는 publish 전에 거부된다.

- [x] **Step 1: metadata schema와 category/status 계약 정의**

  `title`, `status`, `category`, `source`, `created_at`, `updated_at`, `tags`, `summary`, `citation` 필드를 정의한다. `status`는 최소 `draft`, `published`, `deprecated`를 지원하고, publish 대상 category는 `references`, `topics`, `decisions`로 제한한다.

  Run: `python3 -m pytest tests/test_knowledge_store.py -q -k schema`
  Expected: 필수 metadata·허용 category·잘못된 값 거부 테스트가 모두 PASS

- [x] **Step 2: 파일 기반 store lifecycle 구현**

  inbox 문서 탐색, publish 대상 경로 검증, 파일 이동/metadata 갱신, update, deprecate, index 입력 수집을 구현한다. 경로 traversal과 category 외부 저장을 거부한다.

  Run: `python3 -m pytest tests/test_knowledge_store.py -q -k lifecycle`
  Expected: draft → published → deprecated와 실패 복구 경로가 모두 PASS

- [x] **Step 3: 사용자용 knowledge 디렉터리와 README 작성**

  `docs/knowledge/README.md`에 초안 작성 형식, category 선택, 검토·publish·폐기 명령, 인용 형식을 설명하고 `index.md`에는 현재 문서 목록과 빈 category를 표시한다.

  Run: `test -f docs/knowledge/README.md && test -f docs/knowledge/index.md && find docs/knowledge -type d | grep -E 'inbox|references|topics|decisions'`
  Expected: 모든 경로가 존재하고 category가 4개 출력

## Task 2: 검색·인용과 `agentos knowledge` CLI 구현

**파일:**
- 생성: `agentos/knowledge/search.py`, `agentos/commands/knowledge.py`, `tests/test_knowledge_cli.py`
- 수정: `agentos/cli.py`

**사용자에게 보이는 마일스톤:** 사용자가 저장·검토·publish·검색·인용을 명령어로 수행할 수 있다.

- [x] **Step 1: 인덱스 생성과 키워드 검색 구현**

  Markdown 본문·title·summary·tags를 대상으로 대소문자 무관 키워드 검색을 구현하고, 검색 결과에 category·status·문서 경로·일치 섹션을 포함한다. 임베딩이나 외부 API는 사용하지 않는다.

  Run: `python3 -m pytest tests/test_knowledge_cli.py -q -k search`
  Expected: 단일/복수 키워드와 category/status 필터 테스트가 모두 PASS

- [x] **Step 2: publish/update/deprecate/list/search/context 명령 연결**

  `agentos knowledge inbox`, `publish`, `update`, `deprecate`, `list`, `search`, `context` 명령을 추가한다. `context`는 짧은 인용 bundle을 반환하며 원문 경로와 섹션/라인 근거를 포함한다.

  Run: `python3 -m pytest tests/test_knowledge_cli.py -q`
  Expected: CLI lifecycle·오류 메시지·인용 출력 테스트 전부 PASS

- [x] **Step 3: CLI help와 no-op/오류 경계 검증**

  지식 디렉터리가 비어 있거나 metadata가 잘못된 경우 안전한 메시지를 출력하고, CLI help에 사용자 관점의 다음 행동을 표시한다. Publish나 검증이 실패하면 사용자는 `docs/knowledge/inbox/<draft>.md`의 frontmatter를 고친 뒤 같은 `agentos knowledge publish ...` 명령을 다시 실행한다.

  Run: `python3 -m agentos.cli knowledge --help`
  Expected: `inbox`, `publish`, `update`, `deprecate`, `list`, `search`, `context`가 모두 표시

## Task 3: 프로젝트 문서·curator 지침과 index 연결

**파일:**
- 수정: `.agents/agents/harness/knowledge-curator.md`
- 수정: `.agentos/project/00-project-index.md`
- 생성: `docs/knowledge/README.md`
- 생성: `docs/knowledge/index.md`
- 수정: `.agentos/project/02-product-scope-and-requirements.md`

**사용자에게 보이는 마일스톤:** 사용자가 프로젝트 문서 인덱스에서 장기지식 시스템의 목적·진입점·안전한 사용 순서를 찾을 수 있다.

- [x] **Step 1: curator 지침을 실제 CLI 계약과 일치시킴**

  기존 `aha knowledge` 예시를 현재 AgentOS CLI 계약으로 갱신하거나, 실제 `aha` runtime이 제공되는 것이 확인되면 재사용 경계를 명시한다. 승인 전 inbox가 지시 권한이 아니라는 규칙을 유지한다.

  Run: `grep -n "agentos knowledge\|inbox\|publish\|deprecated\|citation" .agents/agents/harness/knowledge-curator.md docs/knowledge/README.md`
  Expected: 실제 명령·경로·상태·승인 경계가 일치

- [x] **Step 1.5: protected `.agents` curator 변경 거버넌스 확인**

  `.agents/agents/harness/knowledge-curator.md`는 protected harness agent surface다. `.agents/_version.json`에서 `codex`가 authorized architect인지 확인하고, independent `principle-auditor` PASS/CLEAN과 manifest sync/update/check evidence를 확보한다. 이 Step은 content update를 구조 변경으로 과장하지 않되, protected surface 변경이 검증 없이 닫히지 않게 한다.

  Run: `grep -n "authorized_architects" .agents/_version.json && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: `codex`가 authorized architect에 포함되고 manifest synchronization과 integrity check가 PASS

  Run: `test -f .agents/traces/reviews/2026-08-01-knowledge-base-lifecycle/principle-auditor.json && grep -n '"result": "PASS/CLEAN"' .agents/traces/reviews/2026-08-01-knowledge-base-lifecycle/principle-auditor.json`
  Expected: current-hash `principle-auditor` artifact가 존재하고 `PASS/CLEAN` 결과를 포함

- [x] **Step 2: project index에 사용자용 knowledge surface 등록**

  `00-project-index.md`의 supporting document 등록표와 읽기 경로에 `docs/knowledge/README.md`/`index.md`를 연결하고, 해당 surface가 root project documents를 override하지 않는다고 명시한다.

  Run: `grep -n "docs/knowledge\|장기지식\|knowledge" .agentos/project/00-project-index.md`
  Expected: 최소 1개의 사용자 진입점·목적·freshness rule이 출력

- [x] **Step 3: 계획·가이드에서 knowledge 검색을 선택적으로 안내**

  계획 작성자가 필요할 때 `agentos knowledge search/context`를 사용하도록 안내하되, 자동 검색 강제나 Gate 2 우회로 해석되지 않게 문구를 고정한다.

  Run: `python3 -m pytest tests/test_knowledge_cli.py -q && grep -rn "Gate 2\|knowledge context\|knowledge search" docs .agentos/project`
  Expected: focused tests PASS 및 승인 경계 문구 확인

## 의존성 분석

- 외부 의존성(API, 토큰, 환경 등): 없음
- 저장소 의존성: Markdown·JSON·파일 시스템만 사용하며 무거운 데이터베이스는 도입하지 않는다.
- 기존 시스템 의존성: Typer/Rich CLI 구조, `.agentos/project/00-project-index.md`, `knowledge-curator` 운영 규칙
- 권한 의존성: 초기 범위에는 별도의 publish role restriction을 두지 않지만, inbox는 instruction authority가 아니다.
- 실행 순서: Task 1 → Task 2 → Task 3

## 검증 계획

- `python3 -m pytest tests/test_knowledge_store.py -q`
  Expected: knowledge store focused tests PASS
- `python3 -m pytest tests/test_knowledge_cli.py -q`
  Expected: knowledge CLI focused tests PASS
- `python3 -m agentos.cli knowledge --help`
  Expected: `inbox`, `publish`, `update`, `deprecate`, `list`, `search`, `context` commands 표시
- `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py -q`
  Expected: combined focused tests PASS
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: harness agents/skills manifest integrity PASS

## 리뷰 반영 이력

- [Gate 2 1차] plan-reviewer 지적: Task 3와 검증 계획의 `Run:` 명령이 baseline harness tool 목록(`git`, `bash`, `python3`, `grep`, `find`)에 없는 `rg`(ripgrep)를 사용하면서 `의존성 분석`은 "외부 의존성: 없음"으로 남아 있어 undeclared dependency였음 → 모든 `rg -n` 명령을 baseline `grep -n`/`grep -rn`으로 교체(사용자 진행 계획 마일스톤 4, Task 3 Step 1/2/3, 검증 계획)하여 `의존성 분석`의 "없음" 주장과 실제 `Run:` 명령이 일치하도록 수정.
- [Stop hook 후 current-checkout 재검토] plan-reviewer 지적: closeout 후 현재 파일에 물리적 review artifact가 없고, Task 3 파일 경로와 protected `.agents` governance가 모호했으며, reader-facing status가 과거 상태를 섞고 있었음 → `reviewed: false`로 안전하게 되돌린 뒤 파일 경로를 exact path로 고정하고 protected-path governance Step을 추가했으며, 현재 상태 문구를 main 병합 후 review artifact 재생성 상태로 정렬함. fresh independent review PASS 후에만 `reviewed: true`로 복구한다.

## 구현 결과

Markdown frontmatter 기반 지식 문서 계약과 `docs/knowledge/inbox`, `references`, `topics`, `decisions` 구조를 추가했다. `agentos knowledge` CLI는 inbox 확인, publish, update, deprecate, list, search, context 인용 bundle을 제공하며 경로 traversal과 category 외부 publish를 거부한다.

`docs/knowledge/README.md`와 `index.md`, `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agents/agents/harness/knowledge-curator.md`를 현재 CLI 계약에 맞춰 연결했다. Knowledge 문서는 재사용 evidence이며 root project documents, active plan, Gate 2 reviewer authority, protected-path rules를 override하지 않는다는 경계를 문서화했다.

## 사용 방법

```bash
agentos knowledge inbox
agentos knowledge publish docs/knowledge/inbox/<draft>.md --category topics
agentos knowledge update docs/knowledge/topics/<doc>.md --summary "Updated summary"
agentos knowledge deprecate docs/knowledge/topics/<doc>.md --reason "superseded"
agentos knowledge list
agentos knowledge search "keyword"
agentos knowledge context "keyword"
```

초안은 `docs/knowledge/inbox/`에 두고, 승인 후 `references`, `topics`, `decisions` 중 하나로 publish한다. 이후 계획이나 답변에서 근거가 필요할 때 `agentos knowledge context "<keyword>"`로 경로와 line evidence를 포함한 짧은 인용 묶음을 확인한다.

## 완료 증거

- `python3 -m pytest tests/test_knowledge_store.py -q -k schema` / 10 passed, 3 deselected
- `python3 -m pytest tests/test_knowledge_store.py -q -k lifecycle` / 2 passed, 11 deselected
- `test -f docs/knowledge/README.md && test -f docs/knowledge/index.md && find docs/knowledge -type d | grep -E 'inbox|references|topics|decisions'` / 4 category paths 출력
- `python3 -m pytest tests/test_knowledge_cli.py -q -k search` / 2 passed, 3 deselected
- `python3 -m pytest tests/test_knowledge_cli.py -q` / 5 passed
- `python3 -m agentos.cli knowledge --help` / inbox, publish, update, deprecate, list, search, context 표시
- `grep -n "agentos knowledge\|inbox\|publish\|deprecated\|citation" .agents/agents/harness/knowledge-curator.md docs/knowledge/README.md` / 실제 명령·상태·인용 경계 확인
- `grep -n "docs/knowledge\|장기지식\|knowledge" .agentos/project/00-project-index.md` / 사용자 진입점과 freshness rule 확인
- `python3 -m pytest tests/test_knowledge_cli.py -q && grep -rn "Gate 2\|knowledge context\|knowledge search" docs .agentos/project` / focused tests PASS 및 승인 경계 문구 확인
- `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py -q` / 18 passed
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` / PASS

## 아카이브 결정

이 계획은 아직 active에 남아 있으며, 사용자가 명시적으로 archive를 요청하면 `plan_lifecycle.py archive <plan-path> --status 완료`로 이동한다.
