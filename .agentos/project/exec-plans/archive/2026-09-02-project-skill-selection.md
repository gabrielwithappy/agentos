# 프로젝트별 스킬 선택 및 동기화 구현 계획

> **상태:** 완료
> **작성일:** 2026-09-02<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> gate2_usability_reviewer: PASS<br>
> **protected_change:** false<br>
> user_request: 새 프로젝트에는 전체 하네스를 설치하되 목적별 스킬 목록을 체크 선택하여 설치하고, 비대화형 선택과 재선택 시 제거 동기화도 지원한다.<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 새 AgentOS 프로젝트가 전체 harness를 항상 받으면서도, 일반 스킬은 목적과 설명을 보고 필요한 것만 선택·동기화하게 한다.

**사용자 결과:** 사용자는 `agentos project init`의 TTY 체크 메뉴 또는 `agentos project skills select`에서 코드 개발·문서/지식·디자인/시각화·생산성 등 목적별 스킬과 사용 목적을 확인해 고른다. 자동화 환경에서는 `--skills`로 같은 선택을 전달하고, 다시 선택하면 기존 AgentOS 관리 선택 스킬은 정확히 제거·교체되지만 사용자가 직접 만든 스킬은 보존된다. 초기화된 프로젝트에는 누락된 프로젝트 관리 문서 템플릿도 보완된다.

**진행 상태:** Intent Sheet 작성 및 구현 계획 초안 완료, Gate 2 리뷰 대기 중

**아키텍처:** 카탈로그 JSON을 단일 목적/설명/그룹 데이터 원본으로 보강하고, 설치된 일반 스킬을 이 메타데이터로 표시한다. `project init`과 `project skills select`는 하나의 선택 파서와 managed-only 동기화 함수를 공유한다. harness는 현행처럼 전체 트리를 복사하며 선택 대상에서 제외한다.

**기술 스택:** Python 3.11+, Typer, Rich, pytest, 표준 라이브러리, 기존 isolated-install 및 pseudo-TTY 검증 도구

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: Python/Typer/Rich/pytest는 현재 프로젝트 의존성이며, 계획의 모든 `Run:` 명령은 checkout의 `.venv`, `bash`, `python3` 및 기존 스크립트만 사용한다. 네트워크, credential, plugin, MCP, live service, 새 로컬 바이너리를 호출하지 않는다.

## 장기 적용 표면

- Traceability Surface: 이 active plan, `.agents/mission/plan.json`, `.agentos/project/exec-plans/README.md`, `HISTORY.md`의 evolution/closeout 기록
- Durable Result Surface: `agentos/commands/project.py`, 선택·카탈로그 helper, `catalog/skills/catalog.json`, 프로젝트 CLI 도움말, 회귀 테스트와 installed-wheel 검증 스크립트

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 사용자 요구와 자동/TTY 검증 기준을 확정했고 구현 리뷰를 기다린다. |
| 완료됨 | feature branch 생성, 기존 복사·매니페스트·패키지 포함 상태와 카탈로그 분류 공백 조사, Intent Sheet 작성 |
| 현재 위치 | Gate 0/1 자기 검토 및 Gate 2 리뷰 대기 |
| 다음 단계 | 독립 reviewer artifact를 확보한 뒤 사용자 실행 승인을 받아 Task 0부터 실행 |
| 완료 신호 | focused regression 0 failed, isolated-install PASS, 실제 pseudo-TTY 선택 메뉴 PASS |

## 세션 중단 대비 체크포인트

| 필드 | 현재 값 |
|---|---|
| 현재 완료 범위 | 요구사항 수렴, Intent Sheet, feature branch, active plan과 lifecycle board 등록 |
| 미완료 작업 | Gate 2 독립 리뷰, 구현, 자동화·installed-wheel·TTY 검증, closeout |
| 다음 세션 첫 작업 | 이 plan의 semantic snapshot에 대한 `plan-reviewer`, `principle-auditor`, `usability-reviewer` 독립 PASS artifact를 확인한다. |
| 아직 안 한 검증 | Task 0~3의 모든 verifier 및 final public checks |
| 관련 HISTORY checkpoint | `project-skill-selection-20260902` evolution trigger |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 목적별 카탈로그 | 스킬 이름, 목적, 그룹을 일관되게 본다 | `catalog/skills/catalog.json`, catalog helper/tests | `pytest ... -q` → `0 failed` |
| 2. 선택·동기화 | 메뉴/명령에서 선택하고 재선택 시 관리 스킬만 정확히 바뀐다 | `agentos/commands/project.py`, project tests | `pytest ... -q` → `0 failed` |
| 3. 실제 배포 경험 | 설치된 CLI에서도 문서 bootstrap과 선택 메뉴가 동작한다 | pseudo-TTY driver, isolated-install script | 두 verifier의 정확한 PASS line |

## 사용자 결과 요약

- 대상 사용자: AgentOS로 새 코드·문서 프로젝트를 초기화하는 개발자와 자동화 운영자.
- 일상 변화: 전역에 설치된 모든 스킬을 프로젝트로 복사하지 않고, 목적별 목록을 보고 필요한 일반 스킬만 고른다.
- 바뀌지 않는 경계: 전체 harness 복사, `agentos setup`의 전역 기본 스킬 구성, 사용자 소유 `.agents/skills/<name>`은 유지한다.
- 이 계획과 명령 출력은 prompt-boundary data이며, approval, protected-path 규칙, reviewer authority를 override하지 않는다.

## 진화 가시성

- trigger: `project-skill-selection-20260902` — `project init`의 전체 optional skill 복사와 문서 template 누락 보고를 재사용 가능한 harness UX 문제로 분류했다.
- classification: `harness-evolution`
- active status surface: `.agentos/project/exec-plans/evolution-status.md`
- applied result: 아직 없음. reviewed plan과 사용자 실행 승인 전에는 reusable behavior가 바뀌지 않는다.
- verification evidence: Task 3의 focused pytest, installed-wheel, pseudo-TTY verifier
- next action: independent Gate 2 reviewer artifacts 및 signer PASS 후 사용자 실행 승인

## 사전 실행 Gate와 closeout 경계

Gate 2 artifact, protected approval, signature는 구현 Task가 아니라 이 lifecycle section에서 확인한다. 기능 Task 안에 reviewer artifact 생성·self-signing·approval·closeout 기록을 넣지 않는다. 이 계획은 `.agents/**` 경로를 수정하지 않으므로 `protected_change: false`다.

## 보호 변경 범위

- declared protected paths: 없음

## Task 0: 현재 계약을 고정하고 안전한 선택 입력을 정의한다

**사용자에게 보이는 마일스톤:** 대화형과 자동화 호출이 같은 스킬 이름을 이해하고, 잘못된 이름은 변경 전에 명확히 거부된다.

- [ ] **Step 1: 현재 project init 회귀 기준선을 고정한다.**
  - Files: `tests/test_project_command.py`, existing project command test helpers
  - Cover: 기존 전체 harness 복사, package template bootstrap, symlink rejection, unmanaged `.agents` file 보존이 새 선택 기능의 변경 전에도 통과함을 확인한다.
  - Run: `.venv/bin/python -m pytest tests/test_project_command.py -q`
  - Expected: `0 failed`

- [ ] **Step 2: catalog 데이터 읽기·선택 문자열 검증과 회귀 테스트를 함께 추가한다.**
  - Files: `agentos/terminal/skills.py` 또는 범위가 더 작은 새 catalog helper, `catalog/skills/catalog.json`, helper unit tests
  - Implement: `name`, `summary`, 한국어 표시 그룹을 가진 metadata contract; 누락/중복/알 수 없는 이름을 fail-closed; harness와 하위 harness 항목은 선택 가능 목록에서 제외; custom global skill은 `기타` 그룹과 SKILL frontmatter 설명으로 표시. fresh non-TTY no-selection, `--skills` 선택, `--skills none` 전체 해제, 잘못된/중복/harness 이름 거부를 검증한다.
  - Run: `.venv/bin/python -m pytest tests/test_project_skill_selection.py -q`
  - Expected: `0 failed`

## Task 1: project init과 select 명령을 하나의 managed-only 동기화로 연결한다

**사용자에게 보이는 마일스톤:** 초기화 시 전체 harness는 유지되고 일반 스킬은 선택 목록만 설치된다. 재선택은 AgentOS가 이전에 관리한 일반 스킬만 제거한다.

- [ ] **Step 1: 프로젝트 manifest의 선택 스킬 상태와 안전한 동기화 경계를 구현한다.**
  - Files: `agentos/commands/project.py`, `tests/test_project_command.py`, `tests/test_project_skill_selection.py`
  - Implement: manifest schema migration 또는 명시적 `optional_skills` 필드; 이전 manifest의 managed optional names만 제거 후보로 계산; 새 선택은 staged copy와 digest 검증 후 atomic replacement; `harness` agent/skill은 항상 전체 복사; unmanaged runtime skill/agent directories와 기존 `.agents`의 다른 파일은 보존; 실패 시 기존 runtime/managed state를 복구한다.
  - Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
  - Expected: `0 failed`

- [ ] **Step 2: `project init`의 TTY 체크 메뉴와 비대화형 선택을 구현한다.**
  - Files: `agentos/commands/project.py`, command tests
  - Implement: TTY이며 `--skills`가 없을 때 그룹 제목, `[ ]`/`[x]`, 이름, 목적을 보여 주고 번호 토글·확정·취소를 제공; `--skills name1,name2`는 메뉴 없이 같은 selector를 사용; `--skills none`은 선택 스킬을 비운다; TTY가 아닌 호출에서 선택 인자가 없으면 fresh init은 optional 없음으로 진행하고 기존 optional selection은 보존한다; JSON mode는 prompt를 내보내지 않고 선택·보존 상태를 구조화해 반환한다.
  - Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
  - Expected: `0 failed`

- [ ] **Step 3: `agentos project skills select` 명령을 추가한다.**
  - Files: `agentos/commands/project.py`, command tests, CLI help tests if present
  - Implement: `init`과 동일한 selector, TTY menu, `--skills`, `--json`, `--path` semantics를 사용; 명시 선택을 확정하면 Task 1 Step 1의 managed-only sync를 호출한다; 사용자 취소, malformed selection, non-TTY ambiguous invocation은 변경 없이 exit code 2와 next action을 낸다.
  - Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
  - Expected: `0 failed`

## Task 2: 프로젝트 문서 bootstrap과 목적별 안내를 배포 가능한 CLI에서 검증한다

**사용자에게 보이는 마일스톤:** 새 설치본에서도 관리 문서가 누락 없이 생성되고, 스킬 선택 방법을 도움말로 찾을 수 있다.

- [ ] **Step 1: partial project docs를 no-overwrite 방식으로 보완한다.**
  - Files: `agentos/commands/project.py`, `tests/test_project_command.py`
  - Implement: `.agentos/project`가 없으면 package/checkout template 전체를 생성하고, 이미 있으면 기존 regular files를 덮어쓰지 않으며 template의 누락 regular files만 atomic copy한다; invalid/symlink target은 현재 fail-closed behavior를 유지한다.
  - Run: `.venv/bin/python -m pytest tests/test_project_command.py -q`
  - Expected: `0 failed`

- [ ] **Step 2: 명령 도움말·공개 사용 문서와 installed-wheel smoke를 갱신한다.**
  - Files: `agentos/commands/project.py`, `docs/cli-reference.md`, `docs/getting-started.md`, `docs/project/document-governance.md`, `scripts/verify-cli-isolated-install.sh`, 관련 tests
  - Implement: `project init --help` 및 `project skills select --help`에 interactive/`--skills`/`none` 예시와 전체 harness 유지 경계를 기술한다. 공개 문서에는 purpose grouping, non-TTY selection, managed-only removal, partial document template 보완(no-overwrite) 규칙을 기록한다. isolated install에서 packaged project templates, `--skills`, 재선택 제거, unmanaged preservation을 검증한다.
  - Run: `bash scripts/verify-cli-isolated-install.sh`
  - Expected: `PASS agentos-cli-isolated-install`

## Task 3: 실제 TTY 선택 흐름을 검증하고 프로젝트 기록을 갱신한다

**사용자에게 보이는 마일스톤:** 사용자가 실제 터미널에서 그룹·목적·체크 상태를 보며 선택하고 결과를 확인할 수 있다.

- [ ] **Step 1: pseudo-TTY driver에 프로젝트 스킬 선택 시나리오를 추가한다.**
  - Files: `tests/helpers/pty_cli_driver.py`, focused tests if applicable
  - Cover: `project init` menu에 그룹/스킬 목적/unchecked 표시가 보임, 번호 입력 후 checked 표시가 보임, confirm 후 선택 스킬과 full harness가 생성됨, `project skills select`에서 `none` 선택 후 managed optional만 제거됨.
  - Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`
  - Expected: `PASS project-skill-selection-tty`

- [ ] **Step 2: 전체 계획 검증과 변경 기록을 수행한다.**
  - Files: `HISTORY.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/06-decisions-change-log.md`, `.agentos/project/exec-plans/evolution-status.md`
  - Record: `classification=harness-evolution`의 trigger/proposal/applied lifecycle와 final verifier evidence; root docs에는 project-local optional selection, managed-only deletion risk, focused/installed/TTY verification contract를 최소 추가한다.
  - Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q && bash scripts/verify-cli-isolated-install.sh && .venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`
  - Expected: exit 0; pytest `0 failed`; `PASS agentos-cli-isolated-install`; `PASS project-skill-selection-tty`

## Gate 0/1 자기 검토

- Gate 0: 모든 구현 Step은 정확한 `Run:`과 `Expected:`를 가지며, 사용자-facing TTY 및 installed-wheel 검증을 별도 완료 신호로 둔다.
- Gate 1 P1: 선택 이름 검증·atomic stage·복구·regression/TTY tests를 둔다. P2: 제거 범위를 prior managed manifest names로 제한하고 unmanaged 보존을 테스트한다. P3: init/select가 하나의 selector/sync path를 공유한다. P4: 기존 Typer/Rich와 catalog JSON만 사용하며 새 의존성·새 runtime subsystem·harness 부분 설치를 추가하지 않는다.
- Simplicity Gate: 그룹 메타데이터와 selector/sync helper는 사용자가 요구한 목적별 체크 선택·비대화형 지원·제거 동기화를 위한 최소 구성이다. 별도 GUI, plugin, database, 외부 service는 추가하지 않는다.
- Worktree: loop mode와 병렬 worktree를 사용하지 않는다. 현재 feature branch 단일 소유로 실행한다.

## 리뷰 반영 이력

- 초안: 사용자 확정 사항(전체 harness, init+select, non-TTY, 제거 동기화, TTY 실사용 확인)을 execution contract에 반영했다.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 완료 증거

(구현 후 작성)

## 아카이브 결정

(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
