# Intent Sheet: project init 스킬 선택 토글 UX

**날짜:** 2026-09-03  
**요청자 의도 요약:** `agentos project init`의 optional skill 선택이 번호 입력 방식이라 불편하므로, 항목을 이동하며 토글하는 TTY 선택 방식으로 바꾸는 계획을 작성한다.

## 가설
> `project init`과 `project skills select`의 TTY 스킬 선택을 번호 입력에서 현재 항목 이동 + 토글 방식으로 바꾸면, 사용자는 번호를 외우거나 입력하지 않고 화면의 선택 상태를 보며 더 빠르게 스킬을 고를 수 있다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?
- [ ] Run: `.venv/bin/python -m pytest tests/test_project_command.py tests/test_project_skill_selection.py -q`  
  Expected: exit code 0이며 `0 failed`
- [ ] Run: `.venv/bin/python tests/helpers/pty_cli_driver.py --project-skill-selection .venv/bin/agentos`  
  Expected: `PASS project-skill-selection-tty`
- [ ] Run: `bash scripts/verify-cli-isolated-install.sh`  
  Expected: `PASS agentos-cli-isolated-install`

## 범위 제약 (Scope Fence)
- 포함: `agentos project init`과 `agentos project skills select`의 TTY optional skill 선택 UI, 관련 pseudo-TTY 검증, stale 번호 입력 안내 제거 검증.
- 제외: `--skills` 비대화형 입력 계약, optional skill catalog 구조, harness 전체 복사 정책, project document bootstrap, provider/runtime/hook 동작.

## 기술 스택 제약
- Python/Typer/Rich 기반 기존 CLI 구조를 유지한다.
- 새 외부 패키지를 추가하지 않고, 필요한 TTY key handling은 Python 표준 라이브러리로 처리한다.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout에서 새 브랜치 `feature/project-init-toggle-skill-selector`를 만들었고, 병렬 작업이나 격리된 build surface가 없다.
- ownership: one branch = current agent owner

## 우선순위
- 프로덕션 수준의 안정성과 엣지 케이스 처리 우선. 기존 `--skills` 자동화 계약과 재실행 안전성을 유지하면서 TTY UX만 좁게 바꾼다.
