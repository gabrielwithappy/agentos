# Intent Sheet: AgentOS PI-style session runtime TUI

> **상태:** 완료

**날짜:** 2026-07-24
**요청자 의도 요약:** AgentOS 대화형 TUI가 매 턴 독립 `codex exec`를 호출하는 구조를 PI처럼 세션 컨텍스트를 소유하고 지속하는 런타임으로 전환할 수 있는 최종 구현 계획을 만든다.

## 가설

> AgentOS가 TUI/CLI 밖에 provider-independent conversation runtime을 두고, 사용자/assistant/tool 메시지와 provider continuation handle을 분리해 소유하면, 대화 문맥이 매 턴 유실되지 않고 first-event 지연과 복구 경로를 측정 가능한 방식으로 개선할 수 있다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점과 opt-in 실사용 검증으로 통과하는가?

- [ ] Run: `uv run pytest tests/test_conversation_runtime.py tests/test_context_builder.py tests/test_tui_cli.py tests/test_cli_contract.py -q` Expected: `pytest PASS` and conversation context, branch, resume, cancel, and TUI/CLI parity regressions pass.
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest tests/test_conversation_runtime.py tests/test_context_builder.py tests/test_tui_cli.py tests/test_cli_contract.py -q` Expected: `pytest PASS` and captured user/session/provider continuation data contains no raw sentinel, token, provider stderr, or raw response body.
- [ ] Run: `uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --assert-session-runtime` Expected: `PASS session-runtime-benchmark` only when the session-aware native path meets the committed first-event and bootstrap thresholds; otherwise explicit non-PASS stop-gate output.
- [ ] Run: `AGENTOS_CODEX_INTEGRATION=1 uv run pytest tests/test_codex_session_integration.py -q` Expected: opt-in real account-login smoke emits sanitized start/message_delta/done across two linked turns, or is explicitly skipped when opt-in is absent.

## 범위 제약 (Scope Fence)

- 포함: provider-independent conversation/session runtime, durable message/context model, native Codex continuation transport integration, TUI and one-shot CLI orchestration, session resume/branch/compaction policy, migration and latency benchmarks, docs/project and operator documentation.
- 제외: API key input/import/storage, raw credential parsing, AgentOS OAuth client registration outside the separately reviewed native auth/transport plan, PI TypeScript/Bun runtime port, a daemon that permanently owns user credentials, arbitrary third-party hooks, changes to session retention/delete/prune confirmations.

## 기술 스택 제약

- Python 3.12+, existing Typer/Textual/pytest/uv stack.
- Existing `LLMEvent` JSONL contract and redaction boundary remain public compatibility constraints.
- The native Codex transport/auth predecessor must be completed or its reviewed implementation must be explicitly merged before its owned files are changed.

## Worktree Decision

- 필요 여부: 불필요.
- 이유: existing feature branch `feature/agentos-llm-invocation-architecture-plan` is already isolated from `main`; the immediate deliverable is documentation and review artifacts only.
- ownership: follow-up implementation uses the reviewed active plan and its file-ownership table.

## 우선순위

- 완전한 구현: interactive multi-turn correctness, recovery, redaction, and measured latency take precedence over a prompt-history-only workaround.
