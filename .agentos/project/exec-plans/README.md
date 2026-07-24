# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-07-24T04:02:56Z

## Active Plans
- older active plans omitted=0
- `완료` [AgentOS PI형 세션 런타임 TUI 아키텍처 구현 계획](.agentos/project/exec-plans/active/2026-07-24-agentos-pi-session-runtime-tui-architecture.md) | reviewed_evidence=invalid | outcome: 사용자는 TUI에서 이전 대화를 실제 다음 답변의 문맥으로 유지하고, 세션 재개와 branch가 올바른 대화 경로를 이어가며, provider 지연/실패 시 명확한 복구를 받는다. | progress: native predecessor(2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport)가 완료되어 `predecessor_completion_commit: 923d35e`가 기록되었고 sha…
- `구현 계획 (리뷰 대기)` [AgentOS TUI — pi TUI 클로닝 Phase 6: 입력 상호작용 기반 구현 계획](.agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase6.md) | outcome: 사용자는 `/capabilities`에서 이식 기능의 준비 상태를 확인하고, slash command와 지원하는 argument를 Tab으로 완성하며, 기존 메시지 포커스 이동과 충돌 없는 단축키 안내를 받는다. | progress: 계획 초안 작성 완료, Gate 2 리뷰 대기. Phase 5가 완료 전이면 Task 0에서 중단한다.
- `리뷰 대기 (완료 후 '완료'로 변경)` [AgentOS TUI — pi/hermes TUI 클론 (Phase 5: 설정 관리 UI `/settings`) 구현 계획](.agentos/project/exec-plans/active/2026-07-23-tui-pi-clone-phase5.md) | progress: 계획 초안 작성, Gate 2 리뷰 대기 중 (아직 서브에이전트 리뷰를 요청하지 않음 — 이 세션의 목적은 계획 문서 작성까지)
- `완료` [AgentOS pi-style LLM runtime native auth/transport 구현 계획](.agentos/project/exec-plans/active/2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md) | reviewed_evidence=invalid | progress: core foundation은 완료됐고, native OAuth/transport 범위는 아직 구현되지 않았다. 이번 계획은 deferred 범위를 implementation-ready execution plan으로 구체화하는 단계다.
- `완료` [AgentOS LLM 호출 런타임 아키텍처 개선 구현 계획](.agentos/project/exec-plans/active/2026-07-23-agentos-llm-invocation-runtime-architecture.md) | reviewed_evidence=invalid | outcome: 사용자는 설치된 `agentos` command를 기본 경로로 써야 하는지, `uv run`이 실제 병목인지, 후속 daemon 분리를 진행해도 되는지를 benchmark와 복구 절차로 명확히 판단할 수 있다. 바뀌지 않는 경계는 현재 `codex`… | progress: 측정 우선의 invocation runtime surface, typed invocation contract, launcher/recovery guidance, docs/project boundary, focused tests, isolated in…
- `완료` [AgentOS LLM Codex Streaming Structure 구현 계획](.agentos/project/exec-plans/active/2026-07-23-agentos-llm-codex-streaming-structure.md) | reviewed_evidence=invalid | outcome: 사용자는 `agentos run --once --provider codex --json`과 TUI에서 Codex 응답이 프로세스 종료 후 한꺼번에 나타나는 대신, 생각 중 표시와 도구 실행 표시, 답변 텍스트를 더 빨리 보게 된다. 바뀌지 않는 경계… | progress: Gate 2 리뷰를 현재 plan hash 기준으로 재기록해 닫은 뒤, `CodexCliProvider`를 live stdout streaming 구조로 전환하고 focused/full verification까지 완료했다.

## Archived Plans
- archive summary: completed=18, parked=3
- older archived plans omitted=1
- `완료` [AgentOS TUI Codex Slash Login 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-tui-codex-slash-login.md) | reviewed_evidence=invalid | outcome: 사용자는 TUI에서 Codex 로그인 시작, 현재 인증 상태 확인, 로그아웃까지 처리하는 핵심 흐름을 얻게 된다. 다만 실제 계정 승인 자체는 여전히 Codex CLI와 외부 브라우저/승인 화면에서 계속될 수 있으며, TUI는 그 진행 상태와 다음… | progress: 계획 범위를 core orchestration으로 축소했고, Gate 2 지적을 반영해 command 경계와 provider별 동작 규칙을 명시하는 revision 단계다. 현재 저장소에는 `/login`과 `/logout` slash command…
- `완료` [AgentOS pi-style LLM runtime 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-pi-style-llm-runtime.md) | reviewed_evidence=invalid | progress: core foundation 범위로 축소한 revision을 기준으로 구현과 검증을 완료했다. Codex는 external-CLI compatibility path를 canonical path로 유지한다.
- `완료` [AgentOS TUI — pi/hermes TUI 클론 (Phase 4: 메시지 포커스 이동 및 클립보드 복사) 구현 계획](.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase4.md) | reviewed_evidence=invalid | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [AgentOS TUI — pi/hermes TUI 클로닝 Phase 3 구현 계획](.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase3.md) | progress: 계획 초안 작성 완료, Gate 2 리뷰 대기 중
- `완료` [AgentOS TUI — pi TUI 격차 해소 (Phase 2) 구현 계획](.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase2.md) | reviewed_evidence=invalid | progress: 완료 — 마일스톤 1~6 구현 및 검증 완료
- `완료` [AgentOS TUI (Pi TUI Parity) 개선 구현 계획](.agentos/project/exec-plans/archive/2026-07-21-tui-ux-improvement.md) | progress: Gate 2 3차 리뷰까지 완료 — `plan-reviewer`/`principle-auditor`/`usability-reviewer` 모두 PASS. 구현 착수 대기 중
- `완료` [[TUI Transcript] 구현 계획](.agentos/project/exec-plans/archive/2026-07-21-tui-transcript-improvement.md) | progress: 완료
- `완료` [AgentOS TUI — pi TUI 격차 해소 (Phase 1) 구현 계획](.agentos/project/exec-plans/archive/2026-07-21-tui-pi-clone-phase1.md) | progress: 계획 초안 작성, Gate 2 리뷰 대기 중
- `완료` [AgentOS TUI 개선 1차 반복: 스트리밍 응답 및 기본 메뉴 구현](.agentos/project/exec-plans/archive/2026-07-20-tui-improvement.md) | progress: 구현 완료 및 fresh verification PASS
- `완료` [AgentOS TUI UX Architecture 구현 계획](.agentos/project/exec-plans/archive/2026-07-19-agentos-tui-ux-architecture.md) | reviewed_evidence=invalid | progress: 구현 완료 및 fresh verification PASS
- `완료` [AgentOS 독립 대화형 CLI 구현 계획](.agentos/project/exec-plans/archive/2026-07-19-agentos-independent-interactive-cli.md) | reviewed_evidence=invalid | outcome: 사용자는 설치한 `agentos` 한 명령으로 대화형 세션을 시작하거나 단발 자동화를 실행하고, hook과 입력 처리 결과를 이해 가능한 상태·복구 안내와 함께 사용할 수 있다. | progress: ADR-0005와 root project 문서는 갱신되었고, Gate 2 reviewer evidence가 PASS/CLEAN으로 확보되었다. 구현과 fresh verification이 완료되었다.
- `완료` [프로젝트 문서 구조 리팩토링 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-project-docs-refactoring.md) | reviewed_evidence=missing | progress: 진행 요약, 완료됨, 현재 위치, 다음 단계, 완료 신호를 간단히 보여줌
- `NEEDS_CONTEXT (분석 handoff 완료)` [AgentOS LLM 구독 로그인·연결 전략 수립 계획](.agentos/project/exec-plans/archive/2026-07-18-llm-auth-api-adoption-analysis.md) | reviewed_evidence=invalid | outcome: 프로젝트 오너는 구독 account-login, OAuth 브라우저 로그인, device-code 로그인, 기존 CLI 위임의 특징·장단점과 권장 적용 순서를 한 문서에서 검토하고, 다음 구현 계획의 범위를 승인할 수 있다. API key 방식은 비… | progress: 참조 프로젝트와 현재 CLI/VS Code 경계를 조사했고, 구현 전 전략 선택과 보안 게이트를 root docs/ADR로 handoff했다. 실제 provider approval은 `NEEDS_CONTEXT`로 남아 있으며, provider 승인…
- `구현 완료` [CI/CD 실패 복구 계획: 유닛 테스트 및 보안 검증 통과](.agentos/project/exec-plans/archive/2026-07-18-fix-ci-tests-and-boundary.md) | reviewed_evidence=missing | progress: 계획 작성 완료, 리뷰 진행 예정
- `완료` [CI(Pull Request) 테스트 실패 복구 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-fix-ci-pipeline.md) | reviewed_evidence=missing | progress: 계획 작성 완료, 리뷰 진행 예정
- `완료` [계획 문서 템플릿 생성 및 리뷰 강제화 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-create-plan-template.md) | reviewed_evidence=missing | progress: 계획 문서 생성 완료, 리뷰 및 승인 대기 중
- `완료 (Scope Exception 승인됨)` [AgentOS worktree 기본 위치 변경 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-agentos-worktree-location.md) | reviewed_evidence=missing | outcome: 개발자는 `--path` 없이 branch와 base만 지정해 worktree를 만들고, 출력된 경로·branch·상태로 생성 성공을 확인할 수 있다. | progress: helper/default-path 구현 검증과 manifest check는 통과했고, 전체 harness suite의 기존 전제 실패로 완료 보류.
- `완료` [AgentOS LLM Core MVP 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-agentos-llm-core-mvp.md) | reviewed | outcome: 사용자는 실제 Codex 계정 로그인 전에도 `agentos llm status`, mock login/logout, and `agentos run --json`으로 LLM 연결 계약과 secret redaction을 테스트할 수 있다. | progress: mock-only LLM runtime 구현과 검증 완료. 계획은 active에 남아 있으며 archive는 사용자 요청 시 수행한다.
- `완료` [AgentOS Codex account-login adapter 구현 계획](.agentos/project/exec-plans/archive/2026-07-18-agentos-codex-account-login-adapter.md) | reviewed | outcome: 사용자는 API key를 AgentOS에 저장하지 않고도 기존 Codex CLI 로그인 상태를 통해 `agentos llm status --provider codex`와 `agentos run --json --once ... --provider co… | progress: 구현 완료. Gate 2 review, Codex adapter implementation, tests, docs alignment, and real Codex smoke checks passed.
- `완료` [가이드 문서 최신화 및 강화 구현 계획](.agentos/project/exec-plans/archive/2026-07-17-guide-enhancement.md) | reviewed_evidence=missing | outcome: 신규 사용자 및 기여자가 낡은 쉘 스크립트(`setup.sh`) 대신 최신 Python CLI 명령어로 AgentOS를 직관적으로 셋업하고 구동할 수 있다. | progress: 리뷰 대기

## Reference Docs
- older reference docs omitted=0
- `리뷰 대기 (완료 후 '완료'로 변경)` [[계획 제목] 구현 계획](.agentos/project/exec-plans/TEMPLATE.md) | progress: 계획 초안 작성, 리뷰 대기 중 (상황에 따라 1줄 요약)
