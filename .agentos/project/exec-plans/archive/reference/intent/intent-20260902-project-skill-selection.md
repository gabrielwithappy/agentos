# Intent Sheet: 프로젝트별 스킬 선택과 동기화

**날짜:** 2026-09-02  
**요청자 의도 요약:** 새 프로젝트는 전체 하네스를 유지하되, 목적별 스킬 목록에서 필요한 항목만 선택해 설치·동기화할 수 있어야 한다.

## 가설

> `agentos project init`과 전용 선택 명령에서 목적별 스킬의 이름·용도를 보여 주고 동일한 선택 목록을 프로젝트 매니페스트에 동기화하면, 필요한 기능을 잃지 않으면서 프로젝트의 `.agents/skills` 복잡도를 줄일 수 있다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점과 실제 TTY 확인으로 통과하는가?

- [ ] Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`  
  Expected: `0 failed`
- [ ] Run: `bash scripts/verify-cli-isolated-install.sh`  
  Expected: `PASS agentos-cli-isolated-install`
- [ ] Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`  
  Expected: `PASS project-skill-selection-tty`

## 범위 제약 (Scope Fence)

- 포함: 전체 harness 복사 유지, 선택 가능한 일반 스킬의 목적별 그룹·설명, `project init` 대화형 선택, `project skills select`, 비대화형 `--skills` 선택, 이전 AgentOS 관리 선택 스킬의 제거 동기화, 누락된 프로젝트 문서 템플릿 보완, 회귀·설치·TTY 검증.
- 제외: `agentos setup`의 전역 기본 스킬 설치 정책 변경, harness 하위 스킬의 부분 설치, 새 외부 CLI/TUI 의존성 추가, 사용자가 직접 만든 프로젝트 스킬의 제거.

## 기술 스택 제약

- 기존 Python, Typer, Rich, Textual, pytest 및 표준 라이브러리만 사용한다.
- 대화형 선택은 TTY에서만 실행하며, 비대화형 호출은 `--skills`로 명시한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 checkout에서 새 기능 브랜치 `bugfix/project-init-docs-and-skill-selection`를 이미 만들었고 병렬 소유 충돌이 없다.
- ownership: 이 브랜치와 현재 작업 세션

## 우선순위

- 프로덕션 수준의 안정성과 엣지 케이스 처리 우선: 사용자 소유 스킬을 보존하고, 명시적으로 선택한 AgentOS 관리 스킬만 제거한다.
