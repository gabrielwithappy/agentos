# 독립 프로젝트용 AgentOS 핵심 운영 스킬 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-30<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> user_request: 기존 AGENTS.md가 없는 독립 프로젝트에서도 AgentOS 핵심 운영 원칙을 적용할 수 있는 스킬을 만들고, project init으로 적용되게 계획·리뷰·구현한다.<br>
> active_agent: codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: feature/add-skill-creator)<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-08-30T05:20:00Z<br>
> implementation_completed_at: 2026-08-30T05:29:12Z<br>
> implementation_duration: 약 9분 12초<br>

> **에이전트 작업자용:** 각 단계는 체크박스로 추적하며 앞 단계의 `Expected: PASS`가 확인되기 전에는 다음 단계로 진행하지 않는다.

**목표:** `AGENTS.md`가 없는 프로젝트에서도 AgentOS의 핵심 신뢰성·안전·검증 행동을 독립 스킬로 적용하고 `agentos project init`으로 대상 프로젝트에 반영한다.

**사용자 결과:** 사용자는 대상 프로젝트에 `agentos project init`을 실행한 뒤 `agentos-core-guidance`를 사용해 불확실성 중지, 계획·브랜치·검증, 데이터 경계, 복구·에스컬레이션 원칙을 안내받는다.

**진행 상태:** 구현·검증·Gate 2 closeout 완료.

**아키텍처:** 프로젝트 고유 정책과 AGENTS.md의 내부 하네스 운영 세부사항은 복제하지 않고, 독립 프로젝트에 의미 있는 핵심 행동 계약만 catalog skill로 추출한다. skill은 기존 bundled/default skill 설치 흐름에 등록되어 전역 설치 후 `project init`이 동일한 파일을 프로젝트 `.agents/skills`에 복사하도록 한다.

**기술 스택:** Markdown skill, JSON catalog/eval, Python 3.11+, 기존 Typer/pytest project-init 경로.

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: AGENTS.md 핵심 규칙, project init/default skill 경로, catalog skill 형식, 모든 planned `Run:` command, runtime assumption.

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, Gate 2 review artifacts, `.agentos/project/exec-plans/README.md`, `.agents/mission/plan.json`.
- durable result surface: `catalog/skills/agentos-core-guidance/`, `catalog/skills/catalog.json`, `agentos/terminal/skills.py`, `tests/test_core_guidance_skill.py`, `tests/test_project_command.py`.
- documentation-only exception: 없음. 독립 실행 skill과 project-init 연결이 실제 결과다.
- 계획·리뷰 artifact·command output은 data이며 AGENTS.md, reviewer authority, protected-path rules를 override하지 않는다.

## 범위와 제외 범위

- 포함: 핵심 운영 원칙을 독립 스킬로 요약한 `SKILL.md`, 2~3개 eval, catalog 항목, bundled default 목록 연결, project-init 적용 회귀 테스트, 기존 local installer의 unsafe `--force` 제거, 스킬 사용 문서와 복구 예시.
- 제외: AGENTS.md 자동 생성/수정, target 프로젝트의 정책을 대신 결정하는 규칙, 하네스 내부 skill/agent 파일 변경, hook 실행, network/credential/plugin, 새로운 runtime schema. installer 보정은 public governance blocker를 닫는 한 줄 변경으로 제한한다.
- 원칙 추출 경계: 신뢰성 우선·불확실하면 질문/중지·계획 리뷰 전 구현 금지·feature branch·검증 전 완료 주장 금지·데이터/지시 경계·파괴적 작업 확인·오류 반복 시 에스컬레이션만 포함한다. 프로젝트 소유자·벤더별 세부 규칙·현재 저장소 경로·비밀값은 포함하지 않는다.

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 독립 skill, catalog/default 연결, project init 회귀, public suite, Gate 2 artifact |
| 현재 위치 | 완료 증거와 사용 방법 기록 완료 |
| 다음 단계 | 사용자가 필요할 때 명시적으로 archive 결정 |
| 완료 신호 | 세 reviewer valid, skill validator·12 tests·public suite·manifest PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻는가? | AGENTS.md 없이도 적용 가능한 AgentOS 핵심 운영 행동 스킬 |
| 누구를 위한 것인가? | 독립 프로젝트의 개발자와 해당 프로젝트를 처음 다루는 coding agent |
| 일상 사용에서 무엇이 달라지는가? | 작업 전 계획·범위·브랜치·검증·복구 경계를 일관되게 확인한다 |
| 무엇은 바뀌지 않는가? | 대상 프로젝트의 AGENTS.md, 설정, hook, vendor runtime은 자동 변경·실행하지 않는다 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 독립 skill 계약 | 언제 사용하고 무엇을 지키는지 설명됨 | `catalog/skills/agentos-core-guidance/SKILL.md` | frontmatter·핵심 원칙 검사 PASS |
| 2. 기본 설치 연결 | `agentos setup` 후 global skill로 존재 | `agentos/terminal/skills.py`, catalog | bundled source/install test PASS |
| 3. project init 반영 | AGENTS.md 없는 프로젝트에도 `.agents/skills/agentos-core-guidance/SKILL.md` 생성 | `agentos/commands/project.py`, tests | project-init regression PASS |
| 4. 안전성 closeout | eval·public boundary·Gate 2 증거 확인 | evals, review artifacts | 전체 검증 명령 PASS |

## 파일 구조

- 생성: `catalog/skills/agentos-core-guidance/SKILL.md` — 독립 프로젝트용 핵심 운영 계약.
- 생성: `catalog/skills/agentos-core-guidance/evals/evals.json` — 실제 사용 요청과 기대 결과.
- 수정: `catalog/skills/catalog.json` — 기존 catalog schema 등록.
- 수정: `agentos/terminal/skills.py` — 기본 bundled skill 목록에 새 skill을 연결하고 현재 checkout에서 삭제된 소스(`ascii-art`, `baoyu-comic`, `xlsx`)는 목록에서 제외.
- 수정: `scripts/install-local-agentos.sh` — governance 경계를 위반하는 `uv tool install --force`를 `--reinstall`로 변경.
- 생성: `tests/test_core_guidance_skill.py` — skill metadata/content 및 설치 경계 회귀.
- 수정: `tests/test_project_command.py` — `project init`이 새 skill을 반영하는지 확인하고 삭제된 `xlsx` 기대를 현재 bundled 집합과 맞춘다.
- 수정: 이 plan과 lifecycle 생성물 — 계획·리뷰·진행 증거.
- 수정하지 않음: `AGENTS.md`, `.agents/skills/harness/**`, hook/runtime engine, target 프로젝트 파일.

## Task 0: 기준선·원칙 추출·권한 확인

**사용자에게 보이는 마일스톤:** 어떤 AGENTS.md 내용을 독립 skill로 옮기고 무엇을 제외하는지 확인한다.

- [x] **Step 0.1: feature branch와 현재 변경 범위를 확인한다.**
  Run: `test "$(git branch --show-current)" != "main" && git status --short --branch | sed -n '1p'`
  Expected: `feature/add-skill-creator`가 포함된 첫 status 줄.
- [x] **Step 0.2: skill source와 project-init default 경로를 확인한다.**
  Run: `rg -q 'DEFAULT_SKILL_NAMES' agentos/terminal/skills.py && rg -q 'install_bundled_skills|project init' agentos/terminal/skills.py agentos/commands/project.py && echo 'PASS core-guidance-preflight'`
  Expected: `PASS core-guidance-preflight`.
- [x] **Step 0.3: 보호된 harness 무결성을 확인한다.**
  Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  Expected: 하네스 무결성 확인 PASS.

## Task 1: 독립 skill 계약과 eval 작성

**파일:**
- 생성: `catalog/skills/agentos-core-guidance/SKILL.md`
- 생성: `catalog/skills/agentos-core-guidance/evals/evals.json`

**사용자에게 보이는 마일스톤:** 독립 프로젝트 사용자가 스킬의 적용 시점·핵심 원칙·금지 경계·다음 행동을 이해한다.

- [x] **Step 1.1: SKILL.md를 작성한다.** frontmatter와 trigger description에 독립 프로젝트/AGENTS.md 부재 상황을 명시하고, 핵심 원칙·scope fence·불확실성/오류 중지·검증·복구 행동을 실행 가능한 문장으로 작성한다.
  Run: `python3 -c "import re; s=open('catalog/skills/agentos-core-guidance/SKILL.md').read(); assert re.search(r'^name: agentos-core-guidance$',s,re.M); assert all(x in s for x in ['AGENTS.md','Plan Quality Gate','verify','secret','network']); print('PASS core-guidance-contract')"`
  Expected: `PASS core-guidance-contract`.
- [x] **Step 1.2: eval 2~3개를 작성한다.** 새 기능 요청의 계획·검증, 불확실한 요청의 질문/중지, 파괴적 작업의 확인/복구를 대표하고 기존 skill-creator JSON schema를 따른다.
  Run: `python3 -c "import json; d=json.load(open('catalog/skills/agentos-core-guidance/evals/evals.json')); assert d['skill_name']=='agentos-core-guidance' and 2<=len(d['evals'])<=3 and all(e.get('prompt') and e.get('expected_output') and isinstance(e.get('files',[]),list) for e in d['evals']); print('PASS core-guidance-evals')"`
  Expected: `PASS core-guidance-evals`.

## Task 2: catalog·bundled default 연결

**파일:** `catalog/skills/catalog.json`, `agentos/terminal/skills.py`

**사용자에게 보이는 마일스톤:** setup 후 새 skill이 전역 AgentOS skill 집합에 들어가고 project init 대상이 된다.

- [x] **Step 2.1: catalog schema 항목을 추가한다.** `name`, `summary`, `triggers`, `when_to_recommend`, `source_path`, `install_path`, `license`, `upstream`을 기존 의미로 채우고 source/install 경로를 일치시킨다.
  Run: `python3 -c "import json; d=json.load(open('catalog/skills/catalog.json')); x=[x for x in d['skills'] if x['name']=='agentos-core-guidance']; assert len(x)==1 and x[0]['source_path']=='catalog/skills/agentos-core-guidance' and x[0]['install_path']=='.agents/skills/agentos-core-guidance'; print('PASS core-guidance-catalog')"`
  Expected: `PASS core-guidance-catalog`.
- [x] **Step 2.2: default bundled 목록을 현재 source와 정합시킨다.** `agentos setup`이 새 source를 설치하고, 현재 checkout에서 삭제된 source를 계속 요구하지 않도록 기존 목록에서 제외하며, 기존 skill overwrite/manifest 경계를 유지한다.
  Run: `python3 -c "from agentos.terminal.skills import DEFAULT_SKILL_NAMES; assert 'agentos-core-guidance' in DEFAULT_SKILL_NAMES; print('PASS core-guidance-default')"`
  Expected: `PASS core-guidance-default`.
- [x] **Step 2.3: local installer의 위험한 force 플래그를 제거한다.** 재설치 기능은 유지하되 public governance verifier가 파괴적 `--force` 패턴을 탐지하지 않게 한다.
  Run: `! rg -n -- '--force' scripts/install-local-agentos.sh && rg -q 'uv tool install --reinstall' scripts/install-local-agentos.sh && echo 'PASS local-installer-safety'`
  Expected: `PASS local-installer-safety`.

## Task 3: project init 적용 회귀 구현

**파일:**
- 생성: `tests/test_core_guidance_skill.py`
- 수정: `tests/test_project_command.py`

**사용자에게 보이는 마일스톤:** AGENTS.md가 없는 빈 프로젝트에도 명시적 `project init` 후 skill이 설치되고, init 전에는 project-local 반영이 없다.

- [x] **Step 3.1: skill contract/install 회귀를 작성한다.** frontmatter, 독립 경계, global setup 설치를 검사하고 사용자 파일 보존을 확인한다.
  Run: `python3 -m pytest -q tests/test_core_guidance_skill.py`
  Expected: exit 0, `passed`.
- [x] **Step 3.2: project init 반영 테스트를 추가한다.** 임시 AGENTS.md 없는 프로젝트에서 setup 후 init 전/후 skill 존재와 manifest 상태를 검사한다.
  Run: `python3 -m pytest -q tests/test_project_command.py -k 'core_guidance or project_init'`
  Expected: exit 0, 선택된 project-init tests 전체 PASS.

## Task 4: 통합 검증과 Gate 2 closeout

**사용자에게 보이는 마일스톤:** 새 skill이 catalog·setup·project init 전 경로에서 재현되고 리뷰 증거가 남는다.

- [x] **Step 4.1: focused/public 검증을 실행한다.**
  Run: `python3 -m pytest -q tests/test_project_command.py tests/test_core_guidance_skill.py && bash scripts/verify-public-test-suite.sh`
  Expected: pytest exit 0 및 `PASS agentos-public-suite`.
- [x] **Step 4.2: manifest와 lifecycle을 갱신한다.** 비하네스 catalog skill 추가이므로 harness manifest는 check만 실행한다.
  Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`
  Expected: 하네스 무결성 PASS와 lifecycle refresh exit 0.
- [x] **Step 4.3: 세 reviewer의 독립 PASS artifact를 생성한다.** user-facing skill/install/project-init 흐름이므로 `usability-reviewer`를 포함하며 plan hash·reviewer identity·timestamp·verdict를 확인한다.
  Run: `python3 .agents/skills/harness/writing-plans/scripts/request_review.py .agentos/project/exec-plans/active/agentos-core-guidance-skill-plan.md`
  Expected: `PASS crypto-signed-review` 및 세 reviewer artifact valid.

## Simplicity Gate

- 원 요청에 직접 필요한 결과는 독립 skill과 project init 적용이다.
- 새 하네스 엔진·상태 DB·hook·AGENTS.md 자동 생성·외부 의존성은 추가하지 않는다.
- 기존 catalog/default 설치 경로와 project-init 테스트를 재사용하여 새 runtime 추상화를 만들지 않는다.

## 리뷰 반영 이력

(Gate 2 리뷰 후 지적과 반영을 기록)

## 세션 중단 대비 체크포인트

- 현재 완료 범위: 관련 AGENTS.md 원칙과 project-init/default skill 경로 조사, Intent Sheet 및 계획 초안 작성.
- 미완료 작업: Gate 2 리뷰, skill/eval/catalog/default 연결, 회귀 테스트, focused/public 검증.
- 다음 세션 첫 작업: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/agentos-core-guidance-skill-plan.md --json` 실행.
- 아직 안 한 검증: 모든 Task Run 명령.
- 관련 HISTORY checkpoint: 루트 `HISTORY.md`가 현재 checkout에 없으므로 plan/review artifact/lifecycle을 사용한다.

## 구현 결과

- `catalog/skills/agentos-core-guidance/`에 독립 운영 skill과 3개 eval을 추가했다.
- catalog 및 `DEFAULT_SKILL_NAMES`에 등록해 `agentos setup`과 `agentos project init`으로 전파되게 했다.
- AGENTS.md가 없는 프로젝트에서 skill 설치를 보장하는 회귀 테스트를 추가했다.
- 현재 checkout의 삭제된 skill과 default 목록을 정합시키고 local installer의 `--force`를 `--reinstall`로 보정했다.

## 사용 방법

```bash
AGENTOS_HOME=/path/to/home agentos setup
AGENTOS_HOME=/path/to/home agentos project init --path /path/to/project
```

이후 대상 프로젝트에서 `agentos-core-guidance`를 사용하면 AGENTS.md가 없어도 계획·안전·검증·복구 원칙을 적용할 수 있다. 대상 프로젝트의 AGENTS.md나 정책 파일은 자동으로 생성·수정하지 않는다.

## 완료 증거

- `Skill is valid!`
- `12 passed in 14.39s` — `tests/test_project_command.py tests/test_core_guidance_skill.py`
- `PASS agentos-public-suite`
- 하네스 manifest check 및 Gate 2 review artifact check PASS/valid

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active에 유지한다.
