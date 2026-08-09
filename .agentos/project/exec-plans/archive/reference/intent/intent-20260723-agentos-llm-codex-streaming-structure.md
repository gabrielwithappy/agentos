# Intent Sheet: AgentOS LLM Codex Streaming Structure

> **상태:** 완료

**날짜:** 2026-07-23  
**요청자 의도 요약:** AgentOS의 `codex` 응답 지연을 줄이면서, 현재 subprocess wrapper 중심 LLM 구조를 더 명확한 스트리밍 구조로 정리한다.

## 가설
> AgentOS가 현재 `codex exec --json`의 전체 완료 후 재생 구조를 버리고, Codex CLI compatibility path는 유지한 채 stdout line stream을 실시간 event stream으로 바꾸면 첫 응답 지연이 줄고 provider 책임이 더 분명해질 것이다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `uv run pytest tests/test_codex_provider.py -k "stream_jsonl_success_events or live_stream or reasoning_and_tool_call_items or failure_event_is_sanitized" -q` Expected: `pytest PASS`
- [ ] Run: `uv run pytest tests/test_cli_contract.py -k "run_json" -q` Expected: `pytest PASS`
- [ ] Run: `uv run pytest tests/test_tui_cli.py -k "loading or codex" -q` Expected: `pytest PASS`
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_codex_provider.py tests/test_cli_contract.py tests/test_tui_cli.py -k "secret or redact or stderr" -q` Expected: `pytest PASS and no raw sentinel/raw provider stderr in captured AgentOS surfaces`
- [ ] Run: `uv run pytest tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py tests/test_tui_cli.py -q` Expected: `pytest PASS`

*판단자가 누구든 동일한 결과를 낸다. "잘 되면"은 기준이 아니다.*

## 범위 제약 (Scope Fence)

- 포함: `codex` provider의 subprocess 실행 경계, stdout line streaming, event parsing/normalization 구조, CLI/TUI consumer compatibility, focused tests, CLI 문서.
- 제외: native OAuth/transport, provider 추가 확장, auth store schema 변경, `.agents/` protected path 수정, unrelated TUI Phase work, API key adapter.

## 기술 스택 제약

- Python 3.12+, Typer, Textual, pytest, existing `uv` environment.
- `codex`는 계속 external CLI compatibility path를 사용한다.
- 실시간 스트리밍 구현은 provider stdout parsing 개선으로만 달성하고, native network transport는 도입하지 않는다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 checkout에서 feature branch `feature/llm-structure-improvement`를 이미 생성했고, 이번 작업은 같은 저장소 안의 LLM/TUI/CLI 구조 개선이다.
- ownership: branch `feature/llm-structure-improvement`

## 우선순위

- 둘 다 하되, 지연 개선이 먼저 보이도록 진행: 사용자 체감 개선은 first-token latency 감소로 먼저 닫고, 그 과정에서 provider 책임 분리와 테스트 구조를 함께 정리한다.
