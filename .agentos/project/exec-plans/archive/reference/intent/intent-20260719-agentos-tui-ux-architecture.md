# Intent Sheet: AgentOS TUI UX Architecture

> **상태:** 완료

**날짜:** 2026-07-19  
**요청자 의도 요약:** pi/Hermes의 외형 복제가 아니라 핵심 아키텍처 인사이트를 추출해 AgentOS에 맞는 Python TUI 구조와 라이브러리 적용 계획을 만든다.

## 가설

> AgentOS의 현재 `input()` 기반 interactive CLI를 Python TUI 앱 구조로 재설계하면, 사용자는 현재 상태·가능한 명령·세션 흐름·복구 방법을 화면에서 즉시 이해하고 더 쉽게 대화할 수 있을 것이다.

## Plan Quality Gate

> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"

- [ ] Run: `.venv/bin/python -m pytest tests/test_cli_contract.py tests/test_interactive_cli.py tests/test_cli_hooks.py -q && echo "PASS agentos-tui-focused-suite"` Expected: `PASS agentos-tui-focused-suite`
- [ ] Run: `AGENTOS_TEST_SECRET=SENTINEL_SECRET .venv/bin/python -m pytest tests/test_interactive_cli.py tests/test_cli_hooks.py -q -k "tui or interactive or redaction or recovery" && echo "PASS agentos-tui-secret-recovery-suite"` Expected: `PASS agentos-tui-secret-recovery-suite`
- [ ] Run: `bash scripts/verify-cli-user-flow.sh` Expected: `PASS interactive-cli-acceptance`
- [ ] Run: `bash scripts/verify-cli-isolated-install.sh` Expected: `PASS agentos-cli-isolated-install`
- [ ] Run: `rg -q "REQ-CLI-003" .agentos/project/02-product-scope-and-requirements.md && rg -q "AgentOS TUI" docs/cli-reference.md && echo "PASS agentos-tui-docs-aligned"` Expected: `PASS agentos-tui-docs-aligned`

*판단자가 누구든 동일한 결과를 낸다. "잘 되면"은 기준이 아니다.*

## 범위 제약 (Scope Fence)

- 포함: Python TUI 라이브러리 선택, TUI 앱 shell, 입력 composer, slash command catalog, footer/status, session picker/resume, sanitized event rendering, docs/project 및 CLI reference 갱신, focused tests.
- 제외: pi TypeScript/Bun runtime 이식, Hermes gateway/provider/backup/ops 기능 복제, 신규 credential 저장, API key 입력/저장, arbitrary third-party hook 실행, provider billing-affecting smoke.

## 기술 스택 제약

- Python 3.11+와 기존 Typer/Rich CLI를 유지한다.
- Textual, prompt_toolkit, Urwid는 공식 문서와 reference code를 근거로 비교한다.
- 이 계획의 구현 라이브러리는 Textual로 고정한다. prompt_toolkit과 Urwid는 fallback 구현이 아니라 구조 참고 근거로만 사용하며, Textual dependency preflight가 실패하면 별도 reviewed plan으로 재계획한다.
- raw token, raw key, raw environment, raw provider stderr는 UI/stdout/stderr/log/test artifact에 노출하지 않는다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 요청은 단일 계획 문서 작성이며, 구현 실행 전에는 현재 feature branch에서 충분하다.
- ownership: `feature/agentos-tui-plan`

## 우선순위

- 프로덕션 수준의 안정성과 엣지 케이스 처리 우선: TUI는 user-facing command surface이므로 pseudo-TTY, redaction, isolated install 검증까지 계획에 포함한다.
