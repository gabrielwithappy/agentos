# Intent Sheet: AgentOS TUI Codex Slash Login

> **상태:** 완료

**날짜:** 2026-07-23  
**요청자 의도 요약:** AgentOS TUI에서 pi처럼 slash command로 Codex 로그인과 기본 인증 상태 관리를 시작할 수 있는 구조를 계획한다.

## 가설
> AgentOS TUI에 Codex 전용 `/login` slash command와 연관 `/status`, `/logout` 인증 surface를 추가하는 구현 계획을 만들면, 사용자는 TUI를 벗어나지 않고 Codex 인증 흐름을 시작·확인·종료할 수 있고 이후 native auth/transport 구현도 사용자 표면 기준으로 안정적으로 진행할 수 있다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?
- [ ] Run: `rg -q '"/login"' agentos/terminal/tui/commands.py && rg -q '"/status"' agentos/terminal/tui/commands.py && rg -q '"/logout"' agentos/terminal/tui/commands.py && echo "PASS tui-auth-commands-planned"` Expected: `PASS tui-auth-commands-planned`
- [ ] Run: `rg -q 'https://auth.openai.com/oauth/authorize' .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md && rg -q 'http://localhost:1455/auth/callback' .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md && rg -q 'https://auth.openai.com/codex/device' .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md && echo "PASS pi-oauth-reference-captured"` Expected: `PASS pi-oauth-reference-captured`
- [ ] Run: `rg -q 'uv run pytest tests/test_tui_cli.py -k "login or logout or status or codex"' .agentos/project/exec-plans/active/2026-07-23-agentos-tui-codex-slash-login.md && echo "PASS verification-contract-defined"` Expected: `PASS verification-contract-defined`

## 범위 제약 (Scope Fence)
- 포함: AgentOS TUI slash command 표면(`/login`, `/status`, `/logout`), TUI auth interaction/overlay 계획, Codex browser login/device-code/headless fallback 근거 반영, 관련 테스트와 CLI reference 계획
- 제외: 실제 native OAuth transport 구현, root docs/ADR 수정, provider registry 재설계, 타 provider 범용화, raw token 저장 정책 변경

## 기술 스택 제약
- Python 3.12+, Textual, Typer, pytest 유지
- OAuth 주소와 흐름 근거는 `/home/gabriel/agent/prj-agent/agentos-workspace/references/pi/packages/ai/src/auth/oauth/openai-codex.ts` 기준
- TUI 표면은 기존 `agentos llm login/status/logout --provider codex` CLI를 orchestration target으로 우선 사용하고, native auth/transport 구현 계획과 충돌하지 않게 설계

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout에서 계획 문서만 추가하며, 별도 병렬 구현을 시작하지 않는다
- ownership: `feature/tui-slash-login-plan`

## 우선순위
- MVP 우선. 먼저 Codex 전용 TUI auth surface 계획을 닫고, 범용 provider auth framework는 후속 계획으로 분리한다.
