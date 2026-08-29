# project init 하네스 리소스 적용 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-29<br>
> reviewed: true<br>
> user_request: `agentos project init` 후 하네스 에이전트와 하네스 스킬이 프로젝트에 실제 적용되도록 수정<br>
> active_agent: Codex<br>
> active_session: project-init-harness-activation<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-08-29T02:55:00Z<br>
> implementation_completed_at: 2026-08-29T03:26:24Z<br>
> implementation_duration: 약 31분<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `agentos project init`이 하네스 에이전트·스킬을 프로젝트의 실제 `.agents` 런타임 표면에 안전하게 적용하도록 만든다.

**사용자 결과:** 프로젝트 초기화 후 `agentos harness --project-root .`와 AgentOS 세션이 프로젝트 로컬 하네스 리소스를 사용할 수 있다.

**진행 상태:** 구현 완료, 검증 완료

**아키텍처:** 프로젝트 초기화는 기존 메타데이터 snapshot을 유지하되, 관리 대상인 `.agents/agents/harness`와 `.agents/skills/harness` 및 전역 스킬을 원자적으로 갱신한다. 세션 bootstrap과 tool read boundary는 프로젝트 로컬 스킬을 우선하고, 없는 경우 기존 전역 스킬로 fallback한다.

계획의 reader-first 사용자 진행 섹션은 설명용 표면이며 approval, protected-path, reviewer authority, prompt hierarchy를 변경하지 않는다.

**기술 스택:** Python 3.11+, Typer, pathlib/shutil, JSON manifest, pytest, 기존 AgentOS atomic filesystem helpers

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 실행 대기 |
| 완료됨 | 원인 분석, 브랜치 생성, Intent Sheet 작성 |
| 현재 위치 | Gate 2 리뷰 PASS, 구현 실행 대기 |
| 다음 단계 | 프로젝트 초기화·세션 경로를 수정하고 회귀 테스트 실행 |
| 완료 신호 | 임시 프로젝트에서 init 후 `.agents` 리소스가 존재하고 bootstrap status가 로컬 스킬을 표시하며 전체 검증이 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `agentos project init`만으로 해당 프로젝트에서 사용할 하네스 에이전트와 스킬이 설치된다. |
| 누구를 위한 것인가? | AgentOS를 프로젝트 단위로 초기화하는 개발자와 그 프로젝트에서 동작하는 에이전트 런타임 |
| 일상 사용에서 무엇이 달라지는가? | 초기화 후 별도 수동 복사 없이 로컬 `.agents` 리소스를 읽고 하네스 명령을 실행할 수 있다. |
| 무엇은 바뀌지 않는가? | 전역 설치 상태, vendor 설정 병합, 기존 사용자 파일 삭제 정책은 바뀌지 않는다. |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 초기화 적용 | 임시 프로젝트에 `.agents/agents/harness`와 `.agents/skills/harness`가 생성됨 | `agentos/commands/project.py` | `pytest -q tests/test_project_command.py` |
| 2. 런타임 연결 | 새 세션이 프로젝트 로컬 스킬을 bootstrap함 | `agentos/terminal/sessions.py`, `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py` | `pytest -q tests/test_conversation_bootstrap.py tests/test_project_command.py` |
| 3. 문서·회귀 고정 | 사용법과 전체 계약이 현재 동작을 설명함 | `docs/getting-started.md`, 테스트 파일 | `python3 -m pytest -q` 및 `scripts/verify-public-test-suite.sh` |

## 장기 적용 표면

- traceability surface: 이 active plan, `.agentos/project/exec-plans/README.md`, 구현 closeout, HISTORY 기록(현재 checkout에는 `HISTORY.md`가 없어 별도 기록은 보류)
- durable result surface: `agentos/commands/project.py`, 세션 bootstrap 경로, 회귀 테스트, `docs/getting-started.md`
- documentation-only exception: 없음

## 파일 구조

- 수정: `agentos/commands/project.py` — 프로젝트 관리 리소스의 source discovery, 안전한 `.agents` 설치, manifest/status payload
- 수정: `agentos/terminal/sessions.py` — 프로젝트 로컬 스킬을 bootstrap 입력으로 선택
- 수정: `agentos/terminal/interaction.py`, `agentos/terminal/tui/app.py` — 프로젝트 로컬 스킬 read boundary 허용
- 수정: `tests/test_project_command.py` — init 산출물 및 재실행/보존 회귀 테스트
- 수정: `tests/test_conversation_bootstrap.py` 또는 세션 관련 테스트 — local skill bootstrap 회귀 테스트
- 수정: `docs/getting-started.md` — 실제 project init 동작과 사용법 반영

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: Python 런타임, 패키지 리소스, 기존 filesystem safety helpers, planned test commands

## Task 0: 리뷰·실행 전제 고정

**파일:**
- 참조: `.../archive/reference/intent/intent-20260829-project-init-harness-activation.md`
- 수정: 이 계획 문서

**사용자에게 보이는 마일스톤:** 구현 범위와 PASS 기준이 고정된다.

- [x] **Step 1: Gate 2 리뷰 증거를 생성하고 계획 상태를 실행 대기로 전환한다.**

Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py --help`
Expected: `리뷰 artifact 검사 도구가 정상 실행된다.`

## Task 1: 프로젝트 리소스 실제 적용

**파일:**
- 수정: `agentos/commands/project.py`
- 수정: `tests/test_project_command.py`

**사용자에게 보이는 마일스톤:** `agentos project init --path <project>` 후 프로젝트 `.agents`에 하네스 리소스가 존재한다.

- [x] **Step 1: source checkout/package catalog에서 하네스 agent·skill source를 검증하고 관리 대상 목록을 정의한다.**

Run: `python3 -m pytest -q tests/test_project_command.py -k source`
Expected: `source discovery 및 목록 검증 회귀 테스트 통과`

- [x] **Step 2: 기존 사용자 `.agents` 하위 파일을 보존하면서 managed 하위 경로를 staging 후 원자적으로 설치한다.**

Run: `python3 -m pytest -q tests/test_project_command.py -k project_init`
Expected: `project init 관련 테스트 모두 통과`

- [x] **Step 3: manifest와 status가 skills·agents의 실제 digest와 일치하는지 검증한다.**

Run: `python3 -m pytest -q tests/test_project_command.py -k status`
Expected: `project status current/stale 상태 테스트 통과`

## Task 2: 세션과 도구의 로컬 skill 연결

**파일:**
- 수정: `agentos/terminal/sessions.py`
- 수정: `agentos/terminal/interaction.py`
- 수정: `agentos/terminal/tui/app.py`
- 수정: 관련 bootstrap/session 테스트

**사용자에게 보이는 마일스톤:** 초기화된 프로젝트에서 새 세션의 bootstrap skill 목록에 프로젝트 로컬 skill이 나타난다.

- [x] **Step 1: cwd의 `.agents/skills`를 우선하고 global fallback을 유지하는 resolver를 추가한다.**

Run: `python3 -m pytest -q tests/test_conversation_bootstrap.py tests/test_project_command.py`
Expected: `local skill 우선순위와 기존 global fallback 테스트 통과`

- [x] **Step 2: interactive/TUI read boundary를 resolver 결과와 일치시킨다.**

Run: `python3 -m pytest -q tests/test_interactive_cli.py tests/test_tui_cli.py`
Expected: `CLI/TUI 테스트 exit 0`

## Task 3: 문서와 최종 검증

**파일:**
- 수정: `docs/getting-started.md`

**사용자에게 보이는 마일스톤:** 초기화 후 실제로 무엇이 설치되고 어떻게 확인하는지 문서에 명시된다.

- [x] **Step 1: project init 설명을 `.agents` 실제 적용 동작에 맞게 갱신한다.**

Run: `rg -n "project init|\.agents/agents|\.agents/skills" docs/getting-started.md`
Expected: `실제 적용 경로와 확인 명령이 문서에 존재`

- [x] **Step 2: focused·full·public 검증을 실행한다.**

Run: `python3 -m pytest -q && scripts/verify-public-test-suite.sh`
Expected: `두 명령 모두 exit 0이며 public verifier가 PASS를 출력`

## 리뷰 반영 이력

- 초안: 프로젝트 init의 snapshot-only 동작과 runtime의 global-only 입력을 원인으로 기록했다.

## 구현 결과

`project init`이 전역 스킬 snapshot과 checkout의 하네스 에이전트·스킬을 `.agents/skills`와 `.agents/agents/harness`에 적용하도록 수정했다. 기존 `.agents`의 관리되지 않는 파일은 보존하며, 세션 bootstrap·CLI·TUI의 스킬 탐색은 project marker가 있는 경우 로컬을 우선하고 전역을 fallback으로 사용한다.

## 사용 방법

프로젝트 루트에서 다음을 실행한다.

```bash
agentos setup
agentos project init --path .
agentos project status
```

상태가 `current`이면 `.agents/skills`와 `.agents/agents/harness`가 적용된 상태이며, 새 AgentOS 세션과 `agentos harness --project-root .`에서 사용할 수 있다.

## 완료 증거

- `python3 -m pytest -q tests/test_project_command.py tests/test_conversation_bootstrap.py` → `31 passed`
- `python3 -m pytest -q tests` → `734 passed`
- `python3 -m pytest -q` → 저장소 내 동일 모듈명 `test_inspect.py` 중복으로 pytest collection error; 구현 제품 테스트와 무관한 기존 문서/catalog fixture 충돌
- `bash scripts/verify-public-test-suite.sh` → `PASS agentos-public-suite`
- `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` → `PASS 하네스 무결성 확인 완료`
- `git diff --check` → exit 0

## 아카이브 결정

구현과 검증은 완료했으며, 이 계획은 사용자가 명시적으로 archive를 요청하기 전까지 active에 남긴다.
