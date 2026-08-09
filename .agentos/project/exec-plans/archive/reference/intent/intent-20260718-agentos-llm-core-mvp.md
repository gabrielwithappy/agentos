# Intent Sheet: AgentOS LLM Core MVP

> **상태:** 완료

**날짜:** 2026-07-18
**요청자 의도 요약:** provider approval 없이도 테스트 가능한 최소 LLM runtime surface를 만들어 이후 Codex account-login adapter를 안전하게 붙일 수 있게 한다.

## 가설

> AgentOS에 provider-independent LLM interface, mock provider, sanitized JSONL events, and secret redaction layer를 먼저 추가하면 실제 Codex 로그인 승인 전에도 CLI/VS Code LLM 연결 계약을 검증할 수 있다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?

- [ ] Run: `pytest tests/test_cli.py tests/test_llm_core.py -q` Expected: all selected tests pass.
- [ ] Run: `python -m agentos.cli llm status --json --provider mock` Expected: JSON contains `"provider":"mock"` and no raw sentinel value.
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET python -m agentos.cli run --json --once "hello"` Expected: JSONL includes sanitized LLM events and does not include `SENTINEL_SECRET`.
- [ ] Run: `rg -n "SENTINEL_SECRET|AGENTOS_TEST_SECRET" .agentos/project/reference/decisions .agentos/project/reference/implementation agentos tests` Expected: only test fixtures or verifier commands contain sentinel labels, never real secret values.

## 범위 제약 (Scope Fence)

- 포함: Python/Typer CLI, `agentos/llm/` 최소 runtime surface, mock provider, JSONL event contract, redaction tests, root docs handoff references.
- 제외: real Codex OAuth, provider account creation, API key input/import/storage, persistent OS credential store, VS Code extension source implementation, multi-provider registry, model catalog, gateway/daemon.

## 기술 스택 제약

- Python 3.11+, Typer, Rich, pytest.
- Pi repository는 구조 참고만 한다. TypeScript/Bun runtime 또는 package dependency를 AgentOS에 직접 추가하지 않는다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 `feature/llm-auth-api-adoption-docs` 브랜치에서 문서/계획 작업이 진행 중이며, 후속 구현도 같은 ownership 범위다.
- ownership: 현재 checkout / current branch.

## 우선순위

- MVP 우선. 실제 provider 연결 전 mock provider와 event/redaction contract를 좁게 고정한다.
