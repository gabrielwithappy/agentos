# 공통 AgentOS 하네스 base 구조 구현 계획

> **상태:** 진행 중<br>
> **작성일:** 2026-08-29<br>
> reviewed: true<br>
> user_request: 사용자별 profile은 현재 단계에서 도입하지 않고, 모든 사용자가 동일한 하네스 agent와 핵심 하네스 skill 구조를 사용하도록 정리한다.<br>
> active_agent: codex<br>
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: feature/2026-08-29-common-agentos-base-resources)<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** AgentOS의 setup과 project init이 동일한 package-owned 하네스 base와 manifest에서 하네스 agent·핵심 skill만 설치·투영하도록 만든다.

**사용자 결과 요약:** 사용자는 별도 profile 설정 없이 어디서 실행하든 동일한 하네스 agent·핵심 skill 구조와 버전을 얻고, 프로젝트 초기화 후 status로 일관성을 확인한다.

**의존성 분석:** 외부 서비스·토큰 없음. package build 검증에는 기존 build backend 의존성이 필요하다.

**장기 적용 표면:**

- Traceability Surface: 이 active plan, Intent Sheet, Gate 2 review artifacts, lifecycle board
- Durable Result Surface: AgentOS package resource bundle, setup/project init 코드, manifest schema, 회귀 테스트, getting-started 문서

**진행 상태:** 계획 리뷰 완료, 구현 실행 대기

**아키텍처:** package-owned 하네스 base를 canonical source로 두고, source checkout은 개발 편의를 위한 동일 resource 경로로만 사용한다. setup은 사용자 상태에 하네스 agent와 `.agents/skills/harness` 핵심 skill을 설치하고, project init은 같은 base의 digest를 프로젝트 snapshot과 `.agents` runtime surface에 반영한다. 일반 catalog skill은 기존 설치·투영 경로를 유지하되 이번 base 정합성 범위에는 포함하지 않는다. 사용자별 profile/override 계층은 추가하지 않는다.

**기술 스택:** Python 3.11+, Typer, pathlib/shutil, importlib.resources, JSON manifest, pytest, Hatchling

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 진행 중 |
| 완료됨 | 요구사항 수렴, 기존 setup/project init 경로 조사, profile 및 일반 catalog skill 범위 제외 확정 |
| 현재 위치 | Task 1 공통 base resolver/manifest 구현 |
| 다음 단계 | focused base 및 setup/project init 검증 |
| 완료 신호 | 공통 base 설치·투영·status·package smoke 검증이 모두 PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 하네스 base 고정 | setup과 project init이 같은 하네스 agent/core skill 목록과 digest를 사용 | package resource bundle, manifest helper | `pytest tests/test_common_base_resources.py -q` |
| 2. setup/project init 정합 | 새 사용자 상태와 프로젝트 `.agents`가 동일한 하네스 구조를 가짐 | `agentos/commands/setup.py`, `agentos/commands/project.py`, `agentos/terminal/paths.py` | setup/project-init focused tests |
| 3. 불일치 진단 | source/package 차이나 누락 리소스가 명확한 오류/status로 표시됨 | status/doctor output, docs | isolated package smoke 및 public suite |

## 리뷰 반영 이력

- Intent Sheet에서 사용자별 profile/override, 일반 catalog skill, provider/auth, 서버 PATH 자동화는 이번 범위에서 제외했다.
- Gate 2 리뷰 증거: `.agents/traces/reviews/2026-08-29-common-agentos-base-resources/`
- 독립 리뷰 결과: plan-reviewer PASS, principle-auditor PASS/CLEAN, usability-reviewer PASS

## 파일 구조

- 수정: `agentos/commands/setup.py` — 공통 base agent 설치와 재실행 정책
- 수정: `agentos/commands/project.py` — canonical base discovery, project projection, manifest/status
- 수정: `agentos/terminal/paths.py`, `agentos/terminal/skills.py` — 공통 resource 경로와 digest helper
- 수정: `pyproject.toml` — package-owned base resource 포함
- 수정: `tests/test_setup_bootstrap.py`, `tests/test_project_command.py`, `tests/test_conversation_bootstrap.py` — 하네스 base 목록과 일반 catalog skill 비혼입 검증
- 생성: `tests/test_common_base_resources.py` — source/package 경로의 하네스 agent/core skill 동일성 회귀 테스트
- 수정: `docs/getting-started.md` — 공통 base 동작과 profile 비지원 범위 안내

## 의존성 분석

- 외부 의존성: 없음
- 환경 의존성: wheel smoke에는 `build`와 Hatchling이 필요하며, 없으면 설치형 검증을 blocked로 기록한다.
- 보안 경계: 기존 symlink 차단, atomic write, 사용자 파일 보존, raw credential 비노출을 유지한다.

## Task 0: 리뷰·실행 전제 고정

**사용자에게 보이는 마일스톤:** 구현 전에 공통 base의 canonical source와 제외 범위를 승인 가능한 형태로 고정한다.

- [ ] Step 0.1: Intent Sheet와 이 계획의 목적·범위·Expected 기준을 대조한다.
  - Run: `test -f .agentos/project/exec-plans/archive/reference/intent/intent-20260829-common-agentos-base-resources.md && rg -q "profile/override" .agentos/project/exec-plans/archive/reference/intent/intent-20260829-common-agentos-base-resources.md`
  - Expected: `exit 0`
- [ ] Step 0.2: Gate 2 독립 review artifacts를 생성하고 plan hash를 고정한다.
  - Run: `test -f .agents/traces/reviews/2026-08-29-common-agentos-base-resources/plan-reviewer.json && test -f .agents/traces/reviews/2026-08-29-common-agentos-base-resources/principle-auditor.json`
  - Expected: 두 reviewer artifact 존재 및 PASS/CLEAN

## Task 1: 공통 base source와 manifest 정합화

**사용자에게 보이는 마일스톤:** setup과 project init이 동일한 공통 agent·skill 집합을 식별한다.

- [x] Step 1.1: package-owned 하네스 agent/core skill 경로와 source-checkout 개발 경로를 하나의 resolver로 통합한다.
  - Run: `./.venv/bin/python -m pytest -q tests/test_common_base_resources.py`
  - Expected: source/package resolver와 하네스 agent/core skill 목록·digest 동일성 테스트 PASS
- [x] Step 1.2: 공통 base manifest schema에 agent·skill 목록, digest, schema version을 기록하고 누락/변조를 fail-closed 처리한다.
  - Run: `./.venv/bin/python -m pytest -q tests/test_project_command.py -k "manifest or status"`
  - Expected: current/stale/invalid 상태 테스트 PASS

## Task 2: setup과 project init의 동일 base 적용

**사용자에게 보이는 마일스톤:** 새 상태와 기존 프로젝트 초기화가 같은 하네스 agent/core skill 구조를 얻는다.

- [x] Step 2.1: `agentos setup`이 하네스 agent와 핵심 하네스 skill을 사용자 상태에 설치하며, 일반 catalog skill의 기존 정책과 custom resource 보존을 유지한다.
  - Run: `./.venv/bin/python -m pytest -q tests/test_setup_bootstrap.py tests/test_common_base_resources.py`
  - Expected: setup/install 및 보존 회귀 테스트 PASS
- [x] Step 2.2: `agentos project init`/`agentos proj init`이 동일 base를 프로젝트 `.agents`에 적용하고 snapshot manifest와 digest를 일치시킨다.
  - Run: `./.venv/bin/python -m pytest -q tests/test_project_command.py tests/test_conversation_bootstrap.py`
  - Expected: project init, alias, project-local skill bootstrap 테스트 PASS

## Task 3: 사용자 확인·패키지 검증

**사용자에게 보이는 마일스톤:** 설치 위치와 무관한 공통 동작을 사용자가 확인할 수 있다.

- [x] Step 3.1: command/status/help 문구에 공통 base와 profile 비지원 범위를 명확히 한다.
  - Run: `rg -n "공통 base|project-local|profile|proj init|project status" docs/getting-started.md agentos`
  - Expected: 공통 base 확인 명령과 현재 profile 비지원 경계가 검색됨
- [ ] Step 3.2: source, isolated package, public suite와 harness manifest를 검증한다.
  - Run: `build_dir=$(mktemp -d) && ./.venv/bin/python -m build --wheel --outdir "$build_dir" && bash scripts/verify-public-test-suite.sh && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: wheel 생성, `PASS agentos-public-suite`, manifest `PASS`

## 구현 결과

- `agentos/terminal/base_resources.py`를 추가해 source checkout/package bundle resolver, digest, manifest, atomic 설치를 공통화했다.
- `agentos setup`이 `AGENTOS_HOME/core/.agents` 아래 공통 harness agent/core skill과 `agentos.harness-base/v1` manifest를 설치한다.
- `project init`/`proj init`이 동일 base를 프로젝트 `.agents/agents/harness` 및 `.agents/skills/harness`에 투영하고 snapshot manifest에 digest를 기록한다.
- Codex/Claude setup hook 계약을 유지하고 Codex Stop mapping을 복구했다.
- 임시 새 환경에서 setup → project init → status를 실행해 전역/프로젝트 harness digest 일치 및 `status=current`를 확인했다.
- `python -m build`는 현재 `.venv`에 `build` 모듈이 없어 실행할 수 없었고, 동등한 `uv build --wheel` 및 isolated install smoke는 통과했다.

## 사용 방법

```bash
AGENTOS_HOME="$HOME/.agentos" agentos setup
agentos project init
agentos project status --json
```

`project status --json`에서 `state: current`, `agents: ["harness"]`, `skills`의 `harness`를 확인한다. 사용자별 profile/override는 현재 지원하지 않는다.

## 완료 증거

- `54 passed` — `tests/test_common_base_resources.py`, setup/project/bootstrap focused suite
- `PASS agentos-cli-isolated-install` — package 설치 후 setup, project init, status 포함 isolated smoke
- `PASS agentos-public-suite`
- harness manifest `--check` PASS
- 임시 setup/project init 검증: `PASS setup-project-init-harness-resources`
- 잔여 환경 blocker: `.venv/bin/python -m build` → `No module named build`

## 아카이브 결정

사용자가 명시적으로 archive를 요청하기 전까지 active plan으로 유지한다.
