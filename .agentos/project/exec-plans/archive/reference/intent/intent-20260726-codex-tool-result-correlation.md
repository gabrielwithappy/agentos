# Intent Sheet: Codex 도구 결과 상관관계 복구

> **상태:** 완료

**날짜:** 2026-07-26  
**요청자 의도 요약:** AgentOS TUI에서 `list`를 비롯한 자체 도구가 실행 결과를 Codex에 정상 반환하도록 수정하고 회귀를 막는다.

## 가설

> Codex `function_call`의 `call_id`를 보존하고 그 결과를 Responses API의 `function_call_output` 항목으로 직렬화하면, TUI의 도구 호출이 결과 뒤 최종 응답까지 정상 진행된다.

## Plan Quality Gate

- [ ] Run: `uv run pytest -q tests/test_codex_transport.py tests/test_conversation_runtime.py tests/test_llm_tools.py` Expected: 모든 테스트 통과
- [ ] Run: `uv run pytest -q tests/test_tui_cli.py -k 'tool'` Expected: 선택된 TUI 도구 표시·흐름 테스트 통과
- [ ] Run: `git diff --check` Expected: 출력 없음, exit 0

## 범위 제약 (Scope Fence)

- 포함: `codex` 네이티브 Responses transport의 function call ID 보존, tool output 직렬화, runtime 메시지 메타데이터, 관련 회귀 테스트.
- 제외: 새 도구 추가·도구 권한 변경·Codex OAuth/인증 변경·`codex-cli` provider 변경·문서 UX 개편.

## 기술 스택 제약

- Python 표준 라이브러리와 기존 pytest만 사용한다. 실제 Codex 계정·네트워크 호출은 검증에 사용하지 않는다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 이미 이 작업용 `bugfix/codex-tool-call-arguments-lost` 브랜치에서 사용자 변경을 보존하며 작업 중이다.
- ownership: 현재 브랜치의 도구 실행 관련 변경만 수정한다.

## 우선순위

- 완전한 구현: API 계약을 구현하고 native transport 경계에서 회귀를 고정한다.
