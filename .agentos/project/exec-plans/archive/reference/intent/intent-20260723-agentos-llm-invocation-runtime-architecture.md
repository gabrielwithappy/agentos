# Intent Sheet: AgentOS LLM 호출 런타임 아키텍처 개선

> **상태:** 완료

**날짜:** 2026-07-23  
**요청자 의도 요약:** `uv run agentos ...` 중심 실행 경로와 현재 LLM 호출 결합 구조가 만드는 체감 지연의 근본 원인을, `pi` TUI 구조를 참고해 아키텍처 수준에서 줄이는 실행 계획을 만든다.

## 가설
> AgentOS에서 느려 보이는 원인은 단일 `codex` 호출 시간만이 아니라, CLI 부트스트랩, 입력 훅/세션 파일 I/O, provider 호출 경계가 한 경로에 결합된 구조에 있다. `pi`처럼 app layer, agent/runtime layer, AI integration layer를 분리하고, 설치된 `agentos` entrypoint와 재사용 가능한 invocation runtime을 canonical path로 두면 체감 첫 응답 시간을 줄이고 이후 확장도 단순해질 것이다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"

- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-07-23-agentos-llm-invocation-runtime-architecture.md`
  Expected: `PASS gate2-review-check reviewers=plan-reviewer,principle-auditor,usability-reviewer`
- [ ] Run: `test -f .agents/traces/research/2026-07-23-agentos-llm-invocation-runtime-architecture.md && echo "PASS invocation-runtime-research-recorded"`
  Expected: `PASS invocation-runtime-research-recorded`
- [ ] Run: `grep -q "pi-coding-agent" .agentos/project/exec-plans/active/2026-07-23-agentos-llm-invocation-runtime-architecture.md && grep -q "uv run" .agentos/project/exec-plans/active/2026-07-23-agentos-llm-invocation-runtime-architecture.md && grep -q "runtime daemon" .agentos/project/exec-plans/active/2026-07-23-agentos-llm-invocation-runtime-architecture.md && echo "PASS invocation-architecture-plan-written"`
  Expected: `PASS invocation-architecture-plan-written`

## 범위 제약 (Scope Fence)
- 포함: `references/pi`의 관련 문서/코드 구조 조사, AgentOS 현재 CLI/TUI/LLM 호출 경계 조사, 재사용 가능한 리서치 문서 작성, 새 execution plan 작성, Gate 2 reviewer 3종 artifact 생성.
- 제외: 실제 runtime daemon 구현, native OAuth/transport 구현, pi TypeScript/Bun runtime 이식, 외부 provider credential 정책 변경, 기존 active native auth/transport plan의 구현 실행.

## 기술 스택 제약
- 기존 Python/Typer/Textual 코드베이스를 유지한다.
- `pi`는 read-only 아키텍처 근거로만 사용한다.
- 현재 `codex` external CLI compatibility path 경계는 유지한 채 계획을 세운다.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout에서 별도 기능 브랜치를 생성해 계획 문서와 review artifact만 작성하면 충분하다.
- ownership: `feature/agentos-llm-invocation-architecture-plan`

## 우선순위
- 프로덕션 수준의 구조 정리와 검증 가능한 개선 계획 우선
