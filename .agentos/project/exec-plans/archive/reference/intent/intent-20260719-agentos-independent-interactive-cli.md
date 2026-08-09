# Intent Sheet: AgentOS 독립 대화형 CLI

> **상태:** 완료

**날짜:** 2026-07-19
**요청자 의도 요약:** pi와 Hermes의 검증된 CLI 구조를 참고해 AgentOS의 자체 대화형 CLI와 안전한 hook/input lifecycle을 구현할 수 있는 전체 실행 계획을 만든다.

## 가설

> 설치 위치와 현재 디렉터리에 의존하지 않는 AgentOS CLI shell, 공통 typed event stream, 선언형 hook/input lifecycle을 도입하면 개발자는 더 쉽게 AgentOS를 대화형·자동화 방식으로 사용하고 harness 개선에 필요한 안전한 관측값을 얻을 수 있다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?

- [ ] Run: `uv sync --group dev && .venv/bin/python -m pytest tests/test_cli_contract.py tests/test_interactive_cli.py tests/test_cli_hooks.py -q` Expected: `PASS (all focused CLI contract tests)`
- [ ] Run: `bash scripts/verify-cli-isolated-install.sh` Expected: `PASS agentos-cli-isolated-install`
- [ ] Run: `bash scripts/verify-cli-user-flow.sh` Expected: `PASS interactive-cli-acceptance`
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_cli_hooks.py tests/test_llm_core.py -q` Expected: `PASS cli-hook-secret-regression`
- [ ] Run: `bash scripts/verify-public-test-suite.sh` Expected: `PASS agentos-public-suite`

## 범위 제약 (Scope Fence)

- 포함: `agentos` 대화형 shell, command/event/session/hook contract, isolated package install, built-in declarative hooks, docs and explicit automated/user-flow verification.
- 제외: pi/Hermes 코드 이식, TypeScript/Bun TUI, gateway/messenger, arbitrary local hook code, AgentOS-owned OAuth/API-key storage, provider credential parsing.

## 기술 스택 제약

- Python 3.11+, Typer, Rich, Python standard library; 기존 provider/secret redaction 경계를 유지한다.
- real provider/billing smoke는 기본 test path에서 제외하고 mock/fake CLI와 synthetic sentinel을 사용한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 사용자 요청은 계획과 문서 승인 범위이며 현재 feature branch에서 작업한다.
- ownership: `feature/agentos-independent-cli-plan`

## 우선순위

- 완전한 구현: 독립 설치, interactive/automation parity, hook safety, user acceptance를 한 계획의 완료 기준으로 고정한다. 이후 gateway/TUI/third-party hooks는 별도 계획이다.
