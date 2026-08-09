# Intent Sheet: AgentOS Codex account-login adapter

> **상태:** 완료

**날짜:** 2026-07-18  
**요청자 의도 요약:** mock-only LLM Core MVP 다음 단계로 Codex account-login/session 위임을 실제 provider adapter로 구현하기 위한 실행 계획을 작성한다.

## 가설

> Codex CLI의 공식 ChatGPT login/session을 AgentOS provider adapter 뒤에 위임하면, AgentOS는 API key 저장이나 자체 OAuth client 없이도 실제 Codex account-login 기반 LLM 응답을 sanitized JSONL 계약으로 사용할 수 있을 것이다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?

- [ ] Run: `.venv/bin/python -m pytest tests/test_cli.py tests/test_llm_core.py tests/test_codex_provider.py -q` Expected: all selected tests pass.
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_codex_provider.py -q -k "redaction or subprocess_env or unsupported_or_unauthenticated"` Expected: selected tests pass and captured stdout/stderr excludes sentinel except explicit verifier labels.
- [ ] Run: `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli llm status --json --provider codex` Expected: sanitized JSON reports `provider:"codex"`, `mode:"account-login"`, and does not expose raw token, auth file, raw environment, or raw Codex stderr.
- [ ] Run: `AGENTOS_CODEX_INTEGRATION=1 .venv/bin/python -m agentos.cli run --json --once "Reply with OK." --provider codex` Expected: sanitized JSONL includes `start`, at least one `message_delta`, and `done`; no raw secret, auth file contents, raw environment, or raw Codex stderr.
- [ ] Run: `! rg -q "OPENAI_API_KEY|AGENTOS_LLM_API_KEY|ANTHROPIC_API_KEY|refresh_token|access_token" agentos tests && echo "PASS no-agentos-secret-storage"` Expected: `PASS no-agentos-secret-storage`.

*판단자가 누구든 동일한 결과를 낸다. "잘 되면"은 기준이 아니다.*

## 범위 제약 (Scope Fence)

- 포함: `agentos/llm` provider registry, Codex CLI subprocess adapter, `agentos llm status/login/logout --provider codex`, `agentos run --json --once ... --provider codex`, focused fake-CLI tests, opt-in real Codex integration checks, docs/project update.
- 제외: AgentOS 자체 OAuth client 등록, raw token/auth file parsing, API key 입력/import/storage/API-key adapter, persistent credential store 생성, VS Code extension 구현, ACP/app-server protocol 도입, broad provider registry, model catalog, gateway, daemon, marketplace, automatic failover.

## 기술 스택 제약

- Python 3.11+, Typer, pytest, dataclasses/typing, JSONL stdout events.
- Codex real provider path는 installed `codex` CLI에 위임한다.
- Official source: `https://developers.openai.com/codex/auth` checked on 2026-07-18.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 checkout은 이미 feature branch이며, 계획 작성은 문서 산출물 중심이다.
- ownership: `feature/agentos-codex-account-login-plan`

## 우선순위

- MVP 우선: Codex CLI session delegation과 secret-safe JSONL bridge만 구현한다. 자체 OAuth, token parsing, app-server/ACP, VS Code bridge는 별도 계획으로 둔다.
