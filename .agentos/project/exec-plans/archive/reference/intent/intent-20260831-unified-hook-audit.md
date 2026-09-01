# Intent Sheet: unified hook 동작 감사 및 수정

**날짜:** 2026-08-31
**요청자 의도 요약:** 현재 동작 중인 pre-tool 및 stop hook이 질문·확인 대기와 실제 완료를 잘못 구분하지 않는지 점검하고, 발견된 문제를 회귀 테스트와 함께 수정할 실행계획을 작성한다.

## 가설
> hook 입력 계약과 판단 로직을 실제 vendor bridge 경로까지 동일하게 검증하고 문맥 오탐을 회귀 테스트로 고정하면, 작업 중인 에이전트의 정상적인 질문·확인 대기를 차단하지 않으면서 위험 명령과 근거 없는 완료 주장은 계속 차단할 수 있을 것이다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"

- [ ] Run: `python3 -m pytest -q tests/test_setup_bootstrap.py tests/test_cryptographic_hook.py`  Expected: `관련 hook 회귀 테스트가 모두 exit 0`
- [ ] Run: `python3 -m pytest -q tests/test_unified_hooks.py`  Expected: `허용/차단 및 질문/완료 판정 테스트가 모두 통과`
- [ ] Run: `python3 .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`  Expected: `PASS 하네스 무결성 확인 완료`
- [ ] Run: `bash scripts/verify-public-test-suite.sh`  Expected: `PASS agentos-public-suite`

## 범위 제약 (Scope Fence)
- 포함: `.codex/hooks.json`, `.agents/hooks/scripts/`, `.agents/hooks/adapters/`, `agentos/commands/setup.py`, `agentos/commands/vendor_hook.py`, hook 관련 테스트, hook 문서 및 manifest 반영
- 포함: 실제 payload 계약, fail-open/fail-closed 경계, 질문·확인 대기·완료 주장 판정, pre-bash/pre-write/post-bash/stop bridge 동등성 감사
- 제외: knowledge-curator 기능, LLM transport, 새 외부 서비스·MCP·credential 연동, 기존 사용자 변경의 정리·삭제, hook 목적과 무관한 하네스 구조 개편

## 기술 스택 제약
- Python 3, Bash, JSON, pytest, 기존 AgentOS hook bridge와 manifest 도구
- 외부 의존성 없음

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout의 기존 변경을 보존하면서 단일 hook 감사 계획을 작성하고, 새 기능 브랜치에서 후속 실행한다.
- ownership: `feature/audit-unified-hooks`

## 우선순위
- 프로덕션 수준의 안전성과 오탐 회귀 방지 우선. 위험 명령 차단을 약화하지 않고, 확인 질문을 완료 주장으로 오인하지 않는 최소 수정만 허용한다.
