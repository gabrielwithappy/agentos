# Intent Sheet: executor-neutral writing-plans contract

> **상태:** 완료

**날짜:** 2026-07-26  
**요청자 의도 요약:** exec-plan이 현재 세션의 직접 구현과 외부 vendor CLI handoff를 모두 명확하게 표현하되, AgentOS가 자기 자신에게 위임하는 구조가 되지 않게 한다.

## 가설
> `writing-plans` 템플릿과 리뷰 계약에 실행자 중립 Execution Contract를 추가하면, 사용자는 직접 구현 계획과 vendor-handoff 계획을 같은 검증·증거 규칙 아래에서 구별할 수 있고, 기존 계획은 `local-agent` 기본값으로 계속 실행할 수 있다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?
- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_executor_neutral_writing_plans_contract.sh` Expected: `PASS executor-neutral-writing-plans-contract`
- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/test_agent_contracts.sh` Expected: `PASS agent-contracts`
- [ ] Run: `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh` Expected: harness suite exit `0` with no `FAIL:` line
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` Expected: harness integrity PASS

## 범위 제약 (Scope Fence)
- 포함: `.agents/skills/harness/writing-plans/SKILL.md`, `.agentos/project/exec-plans/TEMPLATE.md`, `plan-review-checklist.md`, `plan-reviewer.md`, focused harness contract test 및 runner registration, 필요한 `HISTORY.md`/evolution status 기록.
- 제외: AgentOS runtime/CLI/TUI 구현, vendor CLI 프로세스 실행, PTY embedding, screen scraping, vendor credential·usage·tool-loop 소유, structured bridge 구현, plan lifecycle JSON schema 변경, 기존 active/archive plan의 일괄 migration.

## 기술 스택 제약
- 기존 Markdown, Bash, Python helper와 현재 harness test layout만 사용한다.
- 외부 network, credential, plugin, MCP, live vendor CLI는 사용하지 않는다.
- 새 실행 계약은 Markdown 계획 메타데이터/섹션 규약이며 runtime parser를 추가하지 않는다.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 사용자 소유 변경을 보존한 현재 checkout에서 문서·harness 계약 파일만 계획한다. 새 브랜치 `feature/executor-neutral-writing-plans`가 이미 생성됐다.
- ownership: `feature/executor-neutral-writing-plans` / 현재 Codex 세션

## 우선순위
- 완전한 구현: 직접 구현과 vendor-handoff의 안전·증거·호환성 경계를 테스트로 고정한다. 다만 실제 vendor 실행 자동화는 포함하지 않는다.
