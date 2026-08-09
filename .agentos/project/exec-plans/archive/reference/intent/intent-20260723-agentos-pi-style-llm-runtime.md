# Intent Sheet: AgentOS pi-style LLM runtime

> **상태:** 완료

**날짜:** 2026-07-23  
**요청자 의도 요약:** AgentOS의 LLM 호출을 `pi`처럼 provider registry, transport, event stream 중심 구조로 바꾸고, AgentOS가 Codex account-login token을 직접 소유하는 방식까지 허용한다.

## 가설
> AgentOS가 Codex CLI subprocess wrapper 중심 구조를 버리고 `pi`식 provider registry + native auth + streaming transport + event stream 구조를 도입하면, TUI 응답 지연이 줄고 provider 확장, cancellation, usage, tool event 처리가 명확해질 것이다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?

- [ ] Run: `uv run pytest tests/test_llm_core.py tests/test_codex_provider.py tests/test_cli_contract.py tests/test_tui_cli.py -q` Expected: pytest PASS
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET uv run pytest -k "redact or secret or auth" -q` Expected: pytest PASS and no raw sentinel in captured AgentOS surfaces
- [ ] Run: `rg -q "AgentOS-owned Codex account-login" .agentos/project/reference/decisions/0004-agentos-llm-credential-strategy.md && rg -q "provider registry" .agentos/project/03-system-contract.md && echo "PASS docs-auth-boundary-updated"` Expected: `PASS docs-auth-boundary-updated`
- [ ] Run: `uv run python -m agentos.cli llm status --provider codex --json` Expected: sanitized JSON object with provider, auth status, source, and no raw token fields
- [ ] Run: `AGENTOS_CODEX_INTEGRATION=1 uv run python -m agentos.cli run --once --provider codex --json "say hi in one short sentence"` Expected: JSONL begins streaming before final done event, exits 0 when authenticated, or emits sanitized actionable auth error when unauthenticated

*판단자가 누구든 동일한 결과를 낸다. "잘 되면"은 기준이 아니다.*

## 범위 제약 (Scope Fence)

- 포함: AgentOS LLM runtime architecture, Codex account-login ownership docs, OAuth/token store contract, provider registry, native Codex transport, event stream, TUI/CLI consumers, focused tests, CLI docs.
- 제외: API key adapter, arbitrary third-party provider expansion beyond mock and codex, pi TypeScript source copy/paste, public server/web UI, unrelated TUI Phase 기능, plugin/MCP auth.

## 기술 스택 제약

- Python 3.12+, Typer, Textual, pytest, existing `uv` environment.
- `pi`는 read-only design reference로만 사용한다.
- Codex account-login token 저장은 AgentOS-owned encrypted/permissioned local store 또는 최소 0600 JSON store로 시작하되, raw token 출력은 모든 surface에서 금지한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 checkout에서 새 feature branch를 생성했고 사용자 요청은 계획 문서 작성이다.
- ownership: branch `docs/agentos-pi-llm-architecture-plan`

## 우선순위

- 완전한 구현 계획 우선: credential boundary 변경이 포함되므로 MVP라도 문서 승인, secret regression, rollback path가 선행되어야 한다.
