# Intent Sheet: YOLO 도구 실행 모드

> **상태:** 완료

**날짜:** 2026-07-26  
**요청자 의도 요약:** 명시적으로 `--yolo`를 선택한 실행에서만 write/edit/bash 승인을 생략해 작업이 중단되지 않게 한다.

## 가설
> 실행 진입점에서 명시적 `--yolo` 정책을 runtime까지 전달하면, 사용자는 승인 없는 연속 작업을 선택적으로 사용할 수 있고 기본 실행의 안전 동작은 유지된다.

## Plan Quality Gate
- [ ] `uv run pytest -q tests/test_cli_contract.py tests/test_conversation_runtime.py tests/test_tui_cli.py -k 'yolo or approval or tool'` → Expected: PASS
- [ ] `uv run agentos --help` 및 `uv run agentos run --help` → Expected: 두 도움말에 `--yolo` 표시
- [ ] `uv run pytest -q` → Expected: 전체 PASS

## 범위 제약
- 포함: `agentos --yolo`, `agentos run --yolo`, runtime 승인 정책 전달, CLI/TUI 회귀 테스트와 사용 안내.
- 제외: 기본 승인 정책 변경, 인증 변경, 도구 자체 변경, 무한 루프 허용.

## Worktree Decision
- 필요 여부: 불필요. 현재 작업 브랜치에서 기존 도구 수정과 연속성을 유지한다.

## 우선순위
- 명시적 자율 실행의 안정성과 기본 모드 무회귀를 우선한다.
