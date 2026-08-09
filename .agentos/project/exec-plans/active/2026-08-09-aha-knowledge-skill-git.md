# AHA·스킬 양방향 장기지식 저장소 및 Git 연동 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-08-09<br>
> reviewed: false<br>
> user_request: `aha knowledge`와 knowledge skill 양쪽에서 장기지식을 저장·검색하고, 문서 폴더를 Git으로 백업하며 다른 프로젝트에서 연동할 수 있게 한다.<br>
> active_agent: codex<br>
> active_session: 2026-08-09-aha-knowledge-skill-git<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `aha knowledge`와 knowledge skill이 동일한 저장·검토·검색 서비스를 사용하고, 지식 문서를 독립 Git 저장소로 백업·동기화·다른 프로젝트 재사용할 수 있게 한다.

**사용자 결과:** 사용자는 CLI 또는 스킬 지침 중 편한 진입점을 선택해 지식을 관리하고, 명시적 Git 명령으로 백업하거나 다른 프로젝트에 clone/pull해 같은 knowledge surface를 재사용한다.

**진행 상태:** 계획 초안 작성, Gate 2 리뷰 대기 중

**아키텍처:** Markdown 문서와 frontmatter 계약은 기존 knowledge domain을 유지한다. 저장소 경로·Git remote·프로젝트 checkout 정책을 하나의 repository manager가 관리하고, `aha knowledge`와 knowledge skill은 이 manager/service를 호출하는 얇은 adapter가 된다. 프로젝트의 `docs/knowledge`는 관리된 checkout surface로 유지하며, inbox 문서는 publish 전까지 instruction authority가 아니다.

**기술 스택:** Python 3.11+, Typer, Markdown frontmatter, `subprocess` 기반 Git CLI, AgentOS skill catalog/manifest, pytest와 Bash harness tests

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 초안 / 리뷰 대기 |
| 완료됨 | 기존 `agentos knowledge` store·CLI·문서·테스트 조사, Intent Sheet 작성 |
| 현재 위치 | Gate 2 독립 리뷰 및 사용자 승인 대기 |
| 다음 단계 | 리뷰 PASS 후 Task 0 preflight, 이어서 공통 service와 Git/skill adapter 구현 |
| 완료 신호 | Intent Sheet의 knowledge test, AHA/skill parity, Git workflow, cross-project 검증이 모두 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `aha knowledge`와 설치된 knowledge skill에서 같은 지식 저장소를 관리하고, Git backup/clone/pull로 재사용한다. |
| 누구를 위한 것인가? | AgentOS 사용자, 에이전트, 프로젝트 간 장기지식을 재사용하는 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 지식 초안을 inbox에 넣은 뒤 CLI 또는 skill flow로 publish·search·context하고, 필요할 때 `sync`로 Git 상태를 확인한다. |
| 무엇은 바뀌지 않는가? | 기존 frontmatter/category/status 계약, root project docs의 권한, 자동 publish·자동 push, 외부 벡터 검색은 범위 밖이다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 공통 저장 계약 | AHA와 skill이 같은 publish/search 결과를 반환 | `agentos/knowledge/`, `agentos/commands/knowledge.py` | `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q` / Expected: PASS |
| 2. Git 지식 저장소 | 지식 repository를 init/status/backup/sync할 수 있음 | `agentos/knowledge/git.py`, `agentos/commands/knowledge.py` | `bash tests/harness/test_aha_knowledge_git_workflow.sh` / Expected: `PASS aha-knowledge-git-workflow` |
| 3. knowledge skill | 스킬이 정확한 명령과 안전한 복구 경로를 안내함 | `catalog/skills/knowledge-curator/SKILL.md`, skill manifest/catalog | `bash tests/harness/test_aha_knowledge_skill_parity.sh` / Expected: `PASS aha-knowledge-skill-parity` |
| 4. 다른 프로젝트 연동 | 별도 프로젝트에서 clone/pull한 knowledge checkout을 검색·인용함 | `docs/knowledge/README.md`, integration test fixture | `bash tests/harness/test_aha_knowledge_cross_project.sh` / Expected: `PASS aha-knowledge-cross-project` |

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, Gate 2 reviewer artifacts
- durable result surface: `agentos/knowledge/`, `agentos/commands/knowledge.py`, `catalog/skills/knowledge-curator/`, `docs/knowledge/README.md`, `docs/knowledge/index.md`, Git repository contract와 테스트
- documentation-only exception: 없음

## 파일 구조

- 생성: `agentos/knowledge/git.py` — repository 초기화, remote/status/sync/backup 경계와 안전한 Git 실행
- 수정: `agentos/knowledge/store.py` — managed checkout 경로와 기존 lifecycle의 결합
- 수정: `agentos/commands/knowledge.py` — `init`, `status`, `sync`, `backup`, `import` 또는 동등 명령을 공통 service에 연결
- 수정: `agentos/cli.py` 또는 AHA adapter surface — 두 진입점 등록 및 동일 output contract
- 생성: `catalog/skills/knowledge-curator/SKILL.md` — 스킬 사용법·Git 복구 절차·권한 경계
- 수정: `catalog/skills/catalog.json` 및 필요한 catalog manifest — skill 설치/발견 등록
- 생성: `tests/test_knowledge_skill.py` — skill 계약과 CLI parity 검증
- 생성: `tests/harness/test_aha_knowledge_git_workflow.sh` — local Git backup/restore 계약
- 생성: `tests/harness/test_aha_knowledge_skill_parity.sh` — AHA와 skill 명령 결과 parity
- 생성: `tests/harness/test_aha_knowledge_cross_project.sh` — 두 임시 프로젝트의 clone/pull 재사용 검증
- 수정: `docs/knowledge/README.md`, `docs/knowledge/index.md` — canonical repository, checkout, backup/sync 사용법
- 수정: `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/06-decisions-change-log.md` — SSOT traceability와 Git/skill 권한 경계
- 수정: `.agents/agents/harness/knowledge-curator.md` — protected 운영 지침을 실제 두 진입점과 Git flow에 맞게 갱신
- 수정: `tests/test_knowledge_store.py`, `tests/test_knowledge_cli.py` — managed path와 새 lifecycle 회귀 보강

## 의존성 분석

- 외부 의존성: 아래에 선언함
- 스캔 기준: 기존 Python/Typer CLI, skill catalog/manifest, 표준 Git CLI, 계획의 모든 `Run:` 명령과 cross-project fixture

## 의존성 게이트

### Git CLI 및 원격 저장소

- name: Git CLI 및 원격 저장소
- type: network
- required: true
- purpose: 지식 repository backup, clone/pull, 다른 프로젝트 연동을 검증한다.
- preflight:
  Run: `git --version && git ls-remote <test-remote>`
  Expected: `PASS knowledge-git-ready` (버전 출력과 remote 접근 성공)
- fallback:
  available: true
  reason: 원격 접근이 불가능하면 local bare repository fixture로 저장·clone·pull 계약을 검증하되, 실제 원격 push는 수행하지 않는다.
- failure_behavior: NEEDS_CONTEXT

## 실행 전 안전 경계

- remote URL과 credential은 문서·로그·테스트 출력에 기록하지 않는다.
- 기본 동작은 local commit와 fetch/pull까지만 수행하며 `push`는 사용자가 명시적으로 실행한다.
- 기존 `docs/knowledge` 문서를 자동 삭제하거나 덮어쓰지 않는다. 충돌·dirty working tree·잘못된 remote는 중단하고 복구 명령을 안내한다.
- skill 설치는 기존 AgentOS skill manifest 규칙을 따르며, 임의 symlink나 프로젝트 외부 파일을 읽지 않는다.

## 구현 작업

### Task 0: 실행 전 baseline과 Git 경계 확인

**파일:**
- 수정 없음
- 참조: `docs/knowledge/README.md`, `agentos/knowledge/store.py`, `agentos/commands/knowledge.py`, `catalog/skills/catalog.json`

**사용자에게 보이는 마일스톤:** 구현자가 현재 knowledge 계약과 Git 실행 환경을 재현할 수 있다.

- [ ] **Step 1: 기존 knowledge 회귀 baseline 실행**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py -q`
Expected: 기존 knowledge 테스트가 모두 PASS하거나, 환경 의존 실패가 원인과 함께 기록됨

- [ ] **Step 2: Git 및 임시 bare remote preflight 실행**

Run: `git --version && tmpdir=$(mktemp -d) && git init --bare "$tmpdir/knowledge.git" >/dev/null && test -d "$tmpdir/knowledge.git/refs" && echo 'PASS knowledge-git-ready'`
Expected: `PASS knowledge-git-ready`

### Task 1: 공통 knowledge repository service 구현

**파일:**
- 생성: `agentos/knowledge/git.py`
- 수정: `agentos/knowledge/store.py`, `agentos/knowledge/__init__.py`
- 생성/수정: `tests/test_knowledge_store.py`

**사용자에게 보이는 마일스톤:** knowledge 문서가 관리된 checkout 안에서 기존 lifecycle과 동일하게 안전하게 저장된다.

- [ ] **Step 1: repository config와 managed path 계약 정의**

`docs/knowledge`를 project-relative managed surface로 식별하고 canonical Git repository URL, branch, checkout path, last sync metadata를 secret 없이 기록하는 config schema를 추가한다.

Run: `python3 -m pytest tests/test_knowledge_store.py -q -k 'managed or path or config'`
Expected: managed path/config 검증 테스트 PASS

- [ ] **Step 2: Git command runner와 dirty/conflict 보호 구현**

`subprocess` 호출을 중앙화하고 명령·remote·credential을 redaction한다. init/status/fetch/pull/local commit/backup의 실패를 typed error로 변환하며 dirty checkout 덮어쓰기를 차단한다.

Run: `python3 -m pytest tests/test_knowledge_store.py -q -k 'git or dirty or conflict'`
Expected: 성공·실패·복구 경계 테스트 PASS

- [ ] **Step 3: 기존 store lifecycle과 repository service 통합**

기존 frontmatter/status/category 검증을 유지하고 publish/update/deprecate 결과가 Git diff에서 추적되도록 연결한다. 자동 commit/push는 하지 않는다.

Run: `python3 -m pytest tests/test_knowledge_store.py -q`
Expected: 전체 store 테스트 PASS

### Task 2: AHA와 AgentOS CLI의 공통 adapter 구현

**파일:**
- 수정: `agentos/commands/knowledge.py`, `agentos/cli.py`
- 생성/수정: AHA command adapter surface와 관련 catalog/command 문서
- 생성: `tests/test_knowledge_skill.py`

**사용자에게 보이는 마일스톤:** `aha knowledge`와 `agentos knowledge`가 같은 저장소와 결과 계약을 사용한다.

- [ ] **Step 1: 명령 계약 확정**

`init`, `status`, `sync`, `backup`의 인자·출력·exit code를 정하고 기존 inbox/publish/update/deprecate/list/search/context와 충돌 없이 등록한다.

Run: `python3 -m agentos.cli knowledge --help`
Expected: 기존 명령과 새 Git 명령이 모두 표시됨

- [ ] **Step 2: AHA adapter를 공통 service에 연결**

레거시 shell 구현과 새 Python service가 서로 다른 저장 규칙을 갖지 않도록 AHA entrypoint는 service 호출만 수행하게 한다. AHA가 없는 개발 환경에서도 adapter contract test는 fake runner로 실행한다.

Run: `bash tests/harness/test_aha_knowledge_skill_parity.sh`
Expected: `PASS aha-knowledge-skill-parity`

- [ ] **Step 3: CLI lifecycle regression 실행**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q`
Expected: 모든 knowledge 관련 테스트 PASS

### Task 3: knowledge skill 패키지와 문서 흐름 구현

**파일:**
- 생성: `catalog/skills/knowledge-curator/SKILL.md`
- 수정: `catalog/skills/catalog.json`, 필요한 skill manifest
- 수정: `.agents/agents/harness/knowledge-curator.md`
- 수정: `docs/knowledge/README.md`, `docs/knowledge/index.md`

**사용자에게 보이는 마일스톤:** 에이전트가 같은 knowledge service를 사용하도록 안전한 명령 순서와 Git 복구 절차를 안내한다.

- [ ] **Step 1: skill 사용 계약 작성**

draft → review → publish → search/context → status → backup/sync 순서, dirty/conflict 복구, inbox 권한 경계를 skill 문서에 명시한다.

Run: `grep -n 'aha knowledge\|agentos knowledge\|backup\|sync\|clone\|pull\|push' catalog/skills/knowledge-curator/SKILL.md`
Expected: 두 CLI 진입점과 Git 복구/사용 흐름이 모두 문서화됨

- [ ] **Step 2: skill catalog 등록과 설치 검증**

Run: `python3 -m pytest tests/test_knowledge_skill.py -q -k install`
Expected: skill catalog 발견·설치·manifest 기록 테스트 PASS

- [ ] **Step 3: 보호 문서와 사용자 문서 정합성 확인**

Run: `grep -n 'docs/knowledge\|agentos knowledge\|aha knowledge\|Git\|inbox' docs/knowledge/README.md docs/knowledge/index.md .agents/agents/harness/knowledge-curator.md`
Expected: path, command, authority boundary가 동일한 계약을 가리킴

### Task 4: Git backup과 cross-project 통합 검증

**파일:**
- 생성: `tests/harness/test_aha_knowledge_git_workflow.sh`, `tests/harness/test_aha_knowledge_cross_project.sh`
- 수정: `tests/test_knowledge_cli.py`
- 수정: `docs/knowledge/README.md`, project SSOT 문서

**사용자에게 보이는 마일스톤:** 한 프로젝트에서 만든 지식을 백업하고 다른 프로젝트에서 clone/pull해 검색·인용할 수 있다.

- [ ] **Step 1: local backup/restore 시나리오 검증**

Run: `bash tests/harness/test_aha_knowledge_git_workflow.sh`
Expected: `PASS aha-knowledge-git-workflow`

- [ ] **Step 2: 두 프로젝트 cross-project 시나리오 검증**

Project A에서 publish·commit한 뒤 bare remote를 통해 Project B가 clone/pull하고 `search`/`context` 결과에 동일한 문서 경로와 line evidence를 출력하는지 확인한다.

Run: `bash tests/harness/test_aha_knowledge_cross_project.sh`
Expected: `PASS aha-knowledge-cross-project`

- [ ] **Step 3: public boundary와 전체 focused suite 실행**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q && bash tests/harness/test_aha_knowledge_git_workflow.sh && bash tests/harness/test_aha_knowledge_skill_parity.sh && bash tests/harness/test_aha_knowledge_cross_project.sh`
Expected: 모든 명령이 exit code 0이고 세 harness 명령이 각각 PASS 출력

### Task 5: Gate 2 리뷰·manifest·closeout

**파일:**
- 수정: active plan 및 필요한 SSOT/HISTORY 문서
- 생성: `.agents/traces/reviews/2026-08-09-aha-knowledge-skill-git/` 리뷰 증거

**사용자에게 보이는 마일스톤:** 구현 계획과 구현 결과가 독립 리뷰·검증 증거를 갖는다.

- [ ] **Step 1: plan-reviewer와 principle-auditor 리뷰 요청**

Run: `python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/2026-08-09-aha-knowledge-skill-git.md`
Expected: plan-reviewer PASS와 principle-auditor PASS/CLEAN artifact가 생성됨

- [ ] **Step 2: protected `.agents` 변경 시 manifest 동기화**

Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: 두 명령 모두 PASS

- [ ] **Step 3: fresh verification과 closeout 기록**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q`
Expected: fresh focused suite PASS 후에만 plan의 `reviewed`/완료 상태와 HISTORY checkpoint를 갱신

## 비목표 및 보류 항목

- 외부 벡터 DB, semantic embedding, 중앙 knowledge SaaS는 이번 계획에서 다루지 않는다.
- Git remote 자동 생성·자동 push·credential 저장은 다루지 않는다.
- 기존 `docs/knowledge` 내용의 대량 이동/정리는 별도 migration plan 없이는 수행하지 않는다.
- `aha` 레거시 전체 리팩터링은 이 계획의 범위가 아니며 knowledge adapter 계약만 다룬다.

## 리뷰 반영 이력

- 2026-08-09: 사용자 선택으로 자동화 테스트와 별도 프로젝트 clone/pull 검증을 Plan Quality Gate에 반영함.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 아카이브 결정

(구현과 검증, Gate 2 closeout 후 기록)
