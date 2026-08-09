# Intent Sheet: AgentOS TUI 도구 로그 밀도 개선

**날짜:** 2026-07-30  
**요청자 의도 요약:** pi의 도구 사용 표시 방식을 근거로 AgentOS TUI의 과도한 도구 로그를 줄이는 실행계획을 만든다.

## 가설

> 완료된 도구 실행은 기본적으로 짧은 상태 요약만 보이고, 사용자가 한 번의 단축키로 상세 호출·결과를 펼칠 수 있게 하면, 도구 실행의 성공·실패 여부를 잃지 않으면서 transcript의 세로 점유가 줄어들 것이다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 검증으로 통과하는가?

- [ ] Run: `.venv/bin/python -m pytest tests/test_tui_cli.py tests/test_tui_visual_contract.py -q`  
  Expected: `PASS` 및 새 도구 활동 기본 축약, `Ctrl+O` 펼치기/접기, 도구 결과 상관관계, 비밀값 리댁션 회귀 테스트 통과
- [ ] Run: `.venv/bin/python -m pytest tests/test_cli_contract.py tests/test_interactive_cli.py tests/test_cli_hooks.py tests/test_tui_cli.py -q && bash scripts/verify-tui-reference-boundary.sh && echo "PASS tui-tool-log-density-focused-suite"`  
  Expected: `PASS tui-tool-log-density-focused-suite`
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_tui_cli.py -q -k redact && echo "PASS tui-tool-log-density-redaction"`  
  Expected: `PASS tui-tool-log-density-redaction`

## 범위 제약 (Scope Fence)

- 포함: Textual TUI에서 `tool_call`과 그 대응 `tool_result`를 한 개의 축약 가능한 활동 블록으로 표시하는 UX, 전체 도구 상세를 전환하는 키보드 단축키, 안내 문서·요구사항 추적·회귀 테스트.
- 제외: 도구 실행 엔진, provider 이벤트 스키마, 세션 저장 형식, JSONL/`--once` 출력, 승인 정책, 도구 목록, tool renderer 플러그인 구조, pi 소스 복사.

## 기술 스택 제약

- Python 3, Textual, Rich, pytest를 기존 패턴대로 사용한다.
- pi는 read-only UX 근거이며 런타임 의존성이나 복사 대상이 아니다.
- raw token, raw key, raw environment, raw provider stderr는 기존 리댁션 경계를 유지한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 이 계획의 실행 소유자는 단일 feature branch(`plan/tui-tool-log-ux`)에서 순차적으로 작업하며 병렬 구현이나 별도 checkout이 필요하지 않다.
- ownership: `plan/tui-tool-log-ux` 브랜치의 계획 작성자가 계획 산출물을 소유한다.

## 우선순위

- MVP: 기본 축약·명시적 펼치기/접기·문서/테스트까지만 포함한다. 도구별 새로운 renderer, 영속 설정, 개별 블록 토글, 새로운 명령어는 후속 reviewed plan 없이는 추가하지 않는다.
