# project init 스킬 선택 토글 UX 구현 계획

> **상태:** 완료
> **작성일:** 2026-09-03<br>
> reviewed: true<br>
> **usability_review_required:** true<br>
> **protected_change:** false<br>
> user_request: `agentos project init`으로 수행하는 스킬 선택이 번호 입력 방식이라 불편하므로, 각 항목으로 이동해서 토글하는 방식으로 바꾸는 계획을 작성한다.<br>
> active_agent: codex<br>
> active_session: main checkout (no worktree), branch: feature/project-init-toggle-skill-selector<br>
> dashboard_item_id: <br>
> implementation_started_at: 2026-09-02T22:36:00Z<br>
> implementation_completed_at: 2026-09-02T22:47:13Z<br>
> implementation_duration: 11m 13s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** `agentos project init`과 `agentos project skills select`의 TTY 스킬 선택을 번호 입력에서 항목 이동 + Space 토글 + Enter 확정 방식으로 바꾼다.

**사용자 결과:** 사용자는 optional skill 목록에서 위/아래로 항목을 이동하고 Space로 체크를 켜고 끄며 Enter로 확정할 수 있다. 비대화형 자동화 사용자는 기존처럼 `--skills`를 사용할 수 있다.

**진행 상태:** 구현과 검증 완료.

**아키텍처:** 기존 `agentos/commands/project.py`의 `_run_tty_selector()`가 선택 상태와 현재 포커스 인덱스를 함께 관리하도록 바꾼다. Rich 출력은 유지하되 입력은 Python 표준 라이브러리 기반 단일 키 읽기로 전환해 새 의존성을 만들지 않는다. `project init`과 `project skills select`는 지금처럼 같은 selector 함수를 공유한다.

**기술 스택:** Python, Typer, Rich, 표준 라이브러리 `termios`/`tty` 기반 POSIX TTY 처리, 기존 pseudo-TTY test helper.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | Intent Sheet, active plan, Gate 2 리뷰 artifact, TTY selector 구현, pseudo-TTY 검증, isolated install verifier |
| 현재 위치 | closeout 기록 완료 |
| 다음 단계 | 사용자가 명시적으로 요청할 때 active plan archive |
| 완료 신호 | focused pytest, pseudo-TTY interaction, stale prompt scan, isolated install verifier 모두 PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 번호를 입력하지 않고 화면에서 현재 항목을 움직이며 optional skill을 체크/해제하는 `project init` 선택 경험 |
| 누구를 위한 것인가? | AgentOS 프로젝트 초기화 중 필요한 스킬만 고르는 개발자와 운영자 |
| 일상 사용에서 무엇이 달라지는가? | `1`, `2` 같은 번호를 입력하는 대신 위/아래 이동, Space 토글, Enter 확정으로 선택한다 |
| 무엇은 바뀌지 않는가? | `--skills` 자동화 입력, `--skills none`, JSON 출력, harness 복사, project document bootstrap, managed-only 제거 정책 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 현재 동작 고정 | 기존 회귀 기준이 유지된다 | `agentos/commands/project.py`, `tests/helpers/pty_cli_driver.py` | PASS: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q` -> 15 passed |
| 2. 이동형 토글 메뉴 | TTY 메뉴가 현재 항목 표시, 위/아래 이동, Space 토글, Enter 확정을 안내한다 | `agentos/commands/project.py` | PASS: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos` -> `PASS project-skill-selection-tty` |
| 3. 설치 환경 회귀 | 설치된 `agentos`에서도 같은 선택 흐름이 동작한다 | `scripts/verify-cli-isolated-install.sh`, packaged CLI | PASS: `bash scripts/verify-cli-isolated-install.sh` -> `PASS agentos-cli-isolated-install` |

## 세션 중단 대비 체크포인트

| 필드 | 값 |
|---|---|
| 현재 완료 범위 | 구현, 검증, closeout |
| 미완료 작업 | 없음. archive는 사용자 명시 요청 전까지 보류 |
| 다음 세션 첫 작업 | 사용자가 archive를 요청하면 lifecycle archive 명령 실행 |
| 아직 안 한 검증 | 없음 |
| 관련 HISTORY checkpoint | `2026-09-03-project-init-toggle-skill-selector` closeout checkpoint |

## 장기 적용 표면

- traceability surface: active plan, `HISTORY.md`, lifecycle board, Gate 2 review artifacts
- durable result surface: `agentos/commands/project.py`, `tests/helpers/pty_cli_driver.py`, `tests/test_project_command.py`, 필요 시 번호 입력 안내가 남아 있는 사용자 문서
- documentation-only exception: 없음. 최종 결과는 CLI 동작과 검증에 남아야 한다.

이 문서와 명령 출력은 prompt-boundary data이며, approval, protected-path 규칙, reviewer authority, system/developer instructions, `AGENTS.md`, vendor guides를 override하지 않는다.

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` commands, runtime assumptions.
- 근거: 계획 실행은 기존 repo의 Python/Typer/Rich 코드와 기존 `.venv`, shell, pseudo-TTY helper, isolated install script만 사용한다. 새 external service, credential, plugin, MCP, network-only dependency, nonstandard local tool을 추가하지 않는다.
- TTY runtime assumption: 현재 검증 대상은 POSIX pseudo-TTY다. Windows 전용 `msvcrt` 입력 처리는 이 계획 범위에 추가하지 않는다.

## 보호 변경 범위

- declared protected paths: 없음

## 파일 구조

- 수정: `agentos/commands/project.py` — TTY optional skill selector를 번호 입력 루프에서 현재 항목 이동 + 토글 루프로 변경한다.
- 수정: `tests/helpers/pty_cli_driver.py` — pseudo-TTY 입력을 `1\n/c\n`에서 방향키 또는 Vim 키 + Space + Enter 흐름으로 바꾸고 stale 번호 안내 부재를 검증한다.
- 수정 가능: `tests/test_project_command.py` — 필요 시 non-TTY, `--skills`, JSON 계약이 바뀌지 않았음을 명시하는 회귀 테스트를 보강한다.
- 수정 가능: 사용자 문서 또는 help text 파일 — `Type a number` 같은 stale 안내가 문서에 존재할 때만 최소 문구로 갱신한다.

## 범위와 비범위

- 포함: TTY optional skill selector의 입력 방식, 현재 항목 표시 문구, 취소와 확정 키 안내, pseudo-TTY 검증.
- 제외: optional skill catalog, managed manifest schema, `--skills` parser, project docs bootstrap, global skill install/status, harness 복사 정책, provider/runtime/hook 동작.
- Engine change 여부: NO. 장기 실행 엔진, hook runtime, provider runtime 계약을 바꾸지 않는다.
- loop mode 실행 여부: NO. 일반 대화형 세션에서 실행한다.

## Simplicity Gate

- 원래 요구사항에 없던 기능이나 컴포넌트 추가: 없음.
- 새 의존성 추가: 없음.
- 더 단순한 대안 검토: Textual/Questionary 같은 새 UI 프레임워크를 도입하지 않고 기존 Rich 출력과 표준 입력 처리만 수정한다.

## Task 0: 기준 상태와 실행 환경 확인

**파일:**
- 수정: 없음

**사용자에게 보이는 마일스톤:** 구현 전에 현재 브랜치와 기존 회귀 테스트 기준이 확인된다.

- [x] **Step 0.1: 작업 브랜치와 변경 범위를 확인한다.**

Run: `git branch --show-current && git status --short`
Expected: 첫 줄이 `feature/project-init-toggle-skill-selector`이고, 구현 전에는 이 계획/Intent Sheet 외 예상하지 않은 변경이 없다.

- [x] **Step 0.2: focused baseline을 실행한다.**

Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
Expected: exit code 0이며 `0 failed`

## Task 1: TTY selector를 이동형 토글 모델로 변경

**파일:**
- 수정: `agentos/commands/project.py`

**사용자에게 보이는 마일스톤:** `project init` 메뉴가 번호 입력을 요구하지 않고 현재 항목을 이동해 Space로 체크를 바꾼다.

- [x] **Step 1.1: 선택 상태와 포커스 인덱스를 분리한다.**

`_run_tty_selector()`에서 `selection: set[str]`은 유지하고, 현재 항목 위치를 나타내는 `cursor_index`를 추가한다. 표시 순서는 기존 `load_available_optional_skills()` 정렬 결과를 유지하며, 그룹 제목은 렌더링용으로만 사용한다.

Run: `.venv/bin/python -m pytest tests/test_project_skill_selection.py -q`
Expected: exit code 0이며 `0 failed`

- [x] **Step 1.2: 단일 키 입력을 처리한다.**

TTY에서 `Up`/`Down` 또는 `k`/`j`로 이동, `Space`로 토글, `Enter`로 확정, `q` 또는 `Esc`로 취소한다. 숫자 입력 안내와 숫자 토글 처리는 제거한다. 비대화형 경로와 `--skills` 경로는 이 함수에 들어오기 전 기존 계약을 유지한다.

Raw TTY mode를 적용하는 경우 기존 terminal 설정은 반드시 `try/finally`로 복구한다. `Enter` 확정, `q`/`Esc` 취소, 잘못된 키, 예외 발생, subprocess exit 경로 모두 terminal 설정 복구 경계를 공유해야 한다.

Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
Expected: exit code 0이며 `0 failed`

- [x] **Step 1.3: 사용자 안내 문구와 복구 문구를 갱신한다.**

메뉴에는 "위/아래 이동, Space 선택/해제, Enter 확정, q 취소"처럼 사용자가 바로 실행할 수 있는 키만 보인다. 지원하지 않는 키를 누르면 `Invalid key. Use ↑/↓ or j/k to move, Space to select, Enter to confirm, q to cancel.`처럼 바로 복구 가능한 안내를 출력한다. 취소는 변경 없이 exit code 2로 닫고 `Cancelled. No project skill changes were applied. Next: rerun this command when ready.`처럼 변경 없음과 재시도 방법을 알린다.

Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
Expected: exit code 0이며 `0 failed`

## Task 2: pseudo-TTY 검증을 이동형 토글 흐름으로 갱신

**파일:**
- 수정: `tests/helpers/pty_cli_driver.py`
- 수정 가능: `tests/test_project_command.py`

**사용자에게 보이는 마일스톤:** 자동 검증이 실제 사용 키 흐름을 재현한다.

- [x] **Step 2.1: `project init` TTY 시나리오를 Space/Enter 흐름으로 바꾼다.**

`_assert_project_skill_selection()`에서 첫 선택은 `Space`로 현재 항목을 토글하고 `Enter`로 확정한다. transcript에는 `AgentOS Optional Skills`, unchecked 상태, checked 상태, 이동/토글 안내가 있어야 하며 `Type a number`는 없어야 한다.

Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`
Expected: `PASS project-skill-selection-tty`

- [x] **Step 2.2: 실제 항목 이동을 필수로 검증한다.**

`project init` 또는 `project skills select`에서 `Down`/`Up` escape sequence 또는 `j`/`k` 키로 현재 항목이 이동한 뒤 `Space`로 다른 항목을 토글하고 `Enter`로 확정되는지 검증한다. 이동하지 않고 첫 항목만 토글하는 검증은 이 Step을 통과할 수 없다.

Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`
Expected: `PASS project-skill-selection-tty`

- [x] **Step 2.3: 잘못된 키와 취소 복구 문구를 검증한다.**

pseudo-TTY 시나리오에 잘못된 키 입력과 `q` 또는 `Esc` 취소 입력을 추가해 invalid-key 안내, "변경 없음", 재시도 안내가 transcript에 나타나는지 검증한다. 취소 경로는 exit code 2와 persisted optional selection 변경 없음까지 확인한다.

Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`
Expected: `PASS project-skill-selection-tty`

- [x] **Step 2.4: stale 번호 입력 안내가 남지 않았는지 repo-local 검증을 추가한다.**

옛 계약은 exact prompt `Type a number to toggle`과 `Prompt.ask("Action")` 기반 번호 입력 루프다. 구현 후 두 흔적이 source/test/docs/scripts에 남지 않아야 한다.

Run: `! grep -R --exclude='*.pyc' -E "Type a number to toggle|Prompt\\.ask\\(\"Action\"\\)" agentos tests docs scripts`
Expected: exit code 0이며 매칭이 없다.

## Task 3: 설치 환경과 자동화 계약 회귀 검증

**파일:**
- 수정 가능: `scripts/verify-cli-isolated-install.sh`

**사용자에게 보이는 마일스톤:** source checkout 밖에 설치된 CLI에서도 같은 선택 흐름이 검증된다.

- [x] **Step 3.1: isolated install verifier가 새 pseudo-TTY 흐름을 사용하게 한다.**

기존 verifier가 `tests/helpers/pty_cli_driver.py --project-skill-selection`을 호출하므로, helper 갱신만으로 통과하는지 확인한다. 별도 script 수정은 verifier가 stale 입력을 직접 갖고 있을 때만 한다.

Run: `bash scripts/verify-cli-isolated-install.sh`
Expected: `PASS agentos-cli-isolated-install`

- [x] **Step 3.2: 비대화형 `--skills` 계약을 확인한다.**

Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`
Expected: exit code 0이며 `0 failed`

## Task 4: 최종 검증과 closeout

**파일:**
- 수정: `.agentos/project/exec-plans/active/2026-09-03-project-init-toggle-skill-selector.md`
- 수정 가능: `HISTORY.md`

**사용자에게 보이는 마일스톤:** 사용자는 어떤 명령이 통과했고 어떻게 새 선택 UI를 쓰는지 확인할 수 있다.

- [x] **Step 4.1: focused + TTY + isolated install 검증을 한 번에 실행한다.**

Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q && .venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos && bash scripts/verify-cli-isolated-install.sh`
Expected: exit code 0; pytest `0 failed`; `PASS project-skill-selection-tty`; `PASS agentos-cli-isolated-install`

- [x] **Step 4.2: lifecycle board를 갱신한다.**

Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh`
Expected: exit code 0이며 lifecycle refresh 오류가 없다.

- [x] **Step 4.3: closeout을 기록한다.**

계획의 `구현 결과`, `사용 방법`, `완료 증거`, `아카이브 결정`을 실제 검증 출력에 맞게 갱신한다. 필요하면 `HISTORY.md`에 `plan=.agentos/project/exec-plans/active/2026-09-03-project-init-toggle-skill-selector.md`를 포함한 checkpoint를 append-only로 남긴다.

Run: `git diff --check`
Expected: exit code 0이며 whitespace error가 없다.

## 사전 실행 Gate와 closeout 경계

- Gate 2 리뷰 전 구현 금지.
- 필수 리뷰어: `plan-reviewer`, `principle-auditor`, `usability-reviewer`.
- Gate 2 PASS 후 `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-03-project-init-toggle-skill-selector.md`가 `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`를 출력해야 한다.
- 리뷰 통과 뒤에만 `reviewed: true`와 `> **상태:** 구현 계획 (실행 대기)<br>`로 전환한다.

## 리뷰 반영 이력

- [Gate 2 1차 usability-reviewer] 취소 시 변경 없음/재시도 안내가 없음 → 취소 출력에 `No project skill changes were applied`와 재실행 안내를 요구했다.
- [Gate 2 1차 usability-reviewer] 잘못된 키 입력 복구 문구가 없음 → invalid-key 안내와 pseudo-TTY transcript 검증을 추가했다.
- [Gate 2 1차 principle-auditor] raw TTY 복구 경계 누락 → `try/finally` terminal 설정 복구 요구를 Task 1에 추가했다.
- [Gate 2 1차 principle-auditor] 항목 이동 검증이 선택 사항임 → 실제 이동 후 토글을 필수 pseudo-TTY 검증으로 바꿨다.
- [Gate 2 1차 principle-auditor] 취소 경로 영속 변경 없음 검증 누락 → exit code 2와 persisted optional selection 불변 검증을 추가했다.
- [Gate 2 1차 principle-auditor] stale prompt exact string 검증이 좁음 → 이전 번호 입력 계약의 두 흔적인 exact prompt와 `Prompt.ask("Action")` 제거 검증으로 넓혔다.
- [Gate 2 1차 principle-auditor] POSIX-only 가정이 불명확함 → Windows `msvcrt` 입력 처리는 범위 밖이고 POSIX pseudo-TTY를 검증 대상으로 명시했다.

## 구현 결과

- `agentos/commands/project.py`의 TTY optional skill selector를 번호 입력 방식에서 현재 항목 커서, `Space` 토글, `Enter` 확정, `q`/`Esc` 취소 방식으로 변경했다.
- 취소 경로는 `Cancelled. No project skill changes were applied. Next: rerun this command when ready.`를 출력하고 exit code 2로 종료하며, sync 이전에 종료되어 선택 상태를 보존한다.
- `tests/helpers/pty_cli_driver.py`가 Space/Enter, `j` 이동 후 토글, invalid key 안내, 취소 후 manifest 불변, stale 번호 안내 부재를 검증한다.
- `scripts/verify-cli-isolated-install.sh`의 custom skill fixture 디렉터리명을 실제 설치명과 맞춰 기존 `--skills isolated-skill` 계약을 다시 검증 가능하게 했다.

## 사용 방법

- 대화형 선택: `agentos project init` 또는 `agentos project skills select`
- 이동: `Up`/`Down` 또는 `j`/`k`
- 선택/해제: `Space`
- 확정: `Enter`
- 취소: `q` 또는 `Esc`
- 자동화 경로는 기존처럼 `--skills <comma-separated names>` 또는 `--skills none`을 사용한다.

## 완료 증거

- PASS: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-03-project-init-toggle-skill-selector.md` -> `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`
- PASS: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q` -> 15 passed
- PASS: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos` -> `PASS project-skill-selection-tty`
- PASS: `! grep -R --exclude='*.pyc' -E "Type a number to toggle|Prompt\\.ask\\(\"Action\"\\)" agentos tests docs scripts` -> no matches
- PASS: `bash scripts/verify-cli-isolated-install.sh` -> `PASS installed-tui-smoke`, `PASS agentos-cli-isolated-install`
- PASS: combined final verification command in Step 4.1 -> exit code 0

## 아카이브 결정

구현과 검증은 완료됐지만, 사용자가 명시적으로 archive를 요청하기 전까지 이 계획은 `.agentos/project/exec-plans/active/`에 유지한다.
