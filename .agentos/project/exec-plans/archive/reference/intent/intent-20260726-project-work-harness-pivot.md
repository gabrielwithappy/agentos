# Intent Sheet: AgentOS 프로젝트 작업 하네스 전환

> **상태:** 완료

**날짜:** 2026-07-26
**요청자 의도 요약:** AgentOS의 제품 목표를 독립 coding-agent runtime에서 vendor-neutral project work harness로 전환하는 프로젝트 문서 변경 계획을 작성하고, 하네스 리뷰를 통과시킨다.

## 가설

> AgentOS가 vendor별 대화·도구·세션 구현을 소유하지 않고, 프로젝트 작업 계약·검증·증거·안전 경계를 소유하도록 문서 계약을 전환하면, 사용자는 Codex·Claude·OpenCode 등 실행자를 바꿔도 동일한 작업 운영 경험을 유지하면서 신규 vendor 기능은 원본 CLI에서 즉시 사용할 수 있다.

## Plan Quality Gate

> 계획 실행 완료 후, 프로젝트 root 문서와 결정 기록이 하나의 제품 방향을 설명하고, 실행 계획의 Gate 2 리뷰 증거가 자동 검사되는가?

- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-26-project-work-harness-document-pivot.md`
  Expected: `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`
- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && rg -q '^> reviewed: true' .agentos/project/exec-plans/active/2026-07-26-project-work-harness-document-pivot.md && echo 'PASS project-work-harness-plan-registered'`
  Expected: `PASS project-work-harness-plan-registered`
- [ ] Run: `rg -q 'vendor-neutral project work harness' .agentos/project/{01-project-charter.md,02-product-scope-and-requirements.md,03-system-contract.md} && rg -q '0006-agentos-vendor-neutral-project-work-harness.md' .agentos/project/{00-project-index.md,06-decisions-change-log.md} && echo 'PASS project-doc-pivot-aligned'`
  Expected: `PASS project-doc-pivot-aligned`

## 범위 제약 (Scope Fence)

- 포함: `.agentos/project/00-project-index.md`, `01-project-charter.md`, `02-product-scope-and-requirements.md`, `03-system-contract.md`, `04-safety-risk-verification.md`, `05-agent-operating-contract.md`, `06-decisions-change-log.md`, 새 `reference/decisions/0006-agentos-vendor-neutral-project-work-harness.md`, 그리고 이 실행 계획의 lifecycle/review artifacts.
- 제외: `agentos/**`, `tests/**`, `docs/**`, `config/**`, `.agents/**`의 구조·규칙·스킬 변경, provider 인증/전송 구현, TUI 구현, vendor CLI 설치·실행, API key 또는 OAuth 동작, 기존 코드의 삭제·마이그레이션.
- 문서 전환 뒤의 runtime 정합화는 별도 reviewed implementation plan 없이는 시작하지 않는다.

## 기술 스택 제약

- Markdown과 기존 Python lifecycle/review-artifact helper만 사용한다.
- 외부 network, credential, plugin, MCP, live vendor runtime은 사용하지 않는다.
- 현재 dirty worktree의 tool-execution-loop 변경은 사용자 소유 작업으로 보존한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 checkout에서 문서 계획만 작성하며, `docs/project-work-harness-pivot-plan` 브랜치가 이 계획의 단일 소유 브랜치다.
- ownership: one branch = one owner. 별도 병렬 worktree를 만들지 않는다.

## 우선순위

- 문서 우선 전환과 안정성 우선. 새 runtime 기능이나 자동화 엔진을 추가하지 않고, 후속 구현이 안전하게 판단할 수 있는 제품·요구사항·시스템·안전 계약을 먼저 확정한다.
