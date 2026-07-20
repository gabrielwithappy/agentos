# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-07-19T22:48:18Z

## Active Plans
- older active plans omitted=0
- `완료` [AgentOS TUI UX Architecture 구현 계획](.agentos/project/exec-plans/active/2026-07-19-agentos-tui-ux-architecture.md) | reviewed | progress: 구현 완료 및 fresh verification PASS
- `완료` [AgentOS 독립 대화형 CLI 구현 계획](.agentos/project/exec-plans/active/2026-07-19-agentos-independent-interactive-cli.md) | reviewed | outcome: 사용자는 설치한 `agentos` 한 명령으로 대화형 세션을 시작하거나 단발 자동화를 실행하고, hook과 입력 처리 결과를 이해 가능한 상태·복구 안내와 함께 사용할 수 있다. | progress: ADR-0005와 root project 문서는 갱신되었고, Gate 2 reviewer evidence가 PASS/CLEAN으로 확보되었다. 구현과 fresh verification이 완료되었다.

## Archived Plans
- archive summary: completed=7, parked=3
- older archived plans omitted=0
- `완료` [프로젝트 문서 구조 리팩토링 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-project-docs-refactoring.md) | reviewed_evidence=missing | progress: 진행 요약, 완료됨, 현재 위치, 다음 단계, 완료 신호를 간단히 보여줌
- `NEEDS_CONTEXT (분석 handoff 완료)` [AgentOS LLM 구독 로그인·연결 전략 수립 계획](.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md) | reviewed_evidence=invalid | outcome: 프로젝트 오너는 구독 account-login, OAuth 브라우저 로그인, device-code 로그인, 기존 CLI 위임의 특징·장단점과 권장 적용 순서를 한 문서에서 검토하고, 다음 구현 계획의 범위를 승인할 수 있다. API key 방식은 비… | progress: 참조 프로젝트와 현재 CLI/VS Code 경계를 조사했고, 구현 전 전략 선택과 보안 게이트를 root docs/ADR로 handoff했다. 실제 provider approval은 `NEEDS_CONTEXT`로 남아 있으며, provider 승인…
- `구현 완료` [CI/CD 실패 복구 계획: 유닛 테스트 및 보안 검증 통과](.agentos/project/exec-plans/archive/2026-07-18-fix-ci-tests-and-boundary.md) | reviewed_evidence=missing | progress: 계획 작성 완료, 리뷰 진행 예정
- `완료` [CI(Pull Request) 테스트 실패 복구 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-fix-ci-pipeline.md) | reviewed_evidence=missing | progress: 계획 작성 완료, 리뷰 진행 예정
- `완료` [계획 문서 템플릿 생성 및 리뷰 강제화 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-create-plan-template.md) | reviewed_evidence=missing | progress: 계획 문서 생성 완료, 리뷰 및 승인 대기 중
- `완료 (Scope Exception 승인됨)` [AgentOS worktree 기본 위치 변경 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-agentos-worktree-location.md) | reviewed_evidence=missing | outcome: 개발자는 `--path` 없이 branch와 base만 지정해 worktree를 만들고, 출력된 경로·branch·상태로 생성 성공을 확인할 수 있다. | progress: helper/default-path 구현 검증과 manifest check는 통과했고, 전체 harness suite의 기존 전제 실패로 완료 보류.
- `완료` [AgentOS LLM Core MVP 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-agentos-llm-core-mvp.md) | reviewed | outcome: 사용자는 실제 Codex 계정 로그인 전에도 `agentos llm status`, mock login/logout, and `agentos run --json`으로 LLM 연결 계약과 secret redaction을 테스트할 수 있다. | progress: mock-only LLM runtime 구현과 검증 완료. 계획은 active에 남아 있으며 archive는 사용자 요청 시 수행한다.
- `완료` [AgentOS Codex account-login adapter 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-agentos-codex-account-login-adapter.md) | reviewed | outcome: 사용자는 API key를 AgentOS에 저장하지 않고도 기존 Codex CLI 로그인 상태를 통해 `agentos llm status --provider codex`와 `agentos run --json --once ... --provider co… | progress: 구현 완료. Gate 2 review, Codex adapter implementation, tests, docs alignment, and real Codex smoke checks passed.
- `완료` [가이드 문서 최신화 및 강화 구현 계획](.agentos/project/exec-plans/archive/2026-07-17-guide-enhancement.md) | reviewed_evidence=missing | outcome: 신규 사용자 및 기여자가 낡은 쉘 스크립트(`setup.sh`) 대신 최신 Python CLI 명령어로 AgentOS를 직관적으로 셋업하고 구동할 수 있다. | progress: 리뷰 대기
- `완료` [AgentOS CLI 구조 개편 및 AHA 잔재 제거 구현 계획](.agentos/project/exec-plans/archive/2026-07-17-aha-cli-refactoring.md) | reviewed_evidence=missing | outcome: 오래된 aha 기반 쉘 스크립트 참조를 모두 제거하고, Python CLI 구조(agentos skill, agentos agent 등)에 맞게 일관된 사용자 경험을 제공한다. 또한 불필요한 상태 확인용 레거시 기능을 제거하여 CLI를 단순화한다. | progress: 구현 완료

## Reference Docs
- older reference docs omitted=0
- `리뷰 대기 (완료 후 '완료'로 변경)` [[계획 제목] 구현 계획](.agentos/project/exec-plans/TEMPLATE.md) | progress: 계획 초안 작성, 리뷰 대기 중 (상황에 따라 1줄 요약)
