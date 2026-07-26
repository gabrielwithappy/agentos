# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-07-26T06:37:18Z

## Active Plans
- older active plans omitted=0
- `구현 완료 (closeout 재검토 대기)` [AgentOS TUI 요청·결과 분리 구현 계획](.agentos/project/exec-plans/active/2026-07-26-tui-request-result-separation.md) | progress: 마일스톤 0-6 구현 및 테스트 완료. closeout 본문 갱신으로 fresh Gate 2 재검토와 archive 결정만 남았다.
- `구현 계획 (Gate 2 통과)` [executor-neutral writing-plans 계약 구현 계획](.agentos/project/exec-plans/active/2026-07-26-executor-neutral-writing-plans.md) | reviewed | progress: executor-neutral 실행 방식 계약 계획 초안 작성 완료, Gate 2 리뷰 대기 중. 실제 harness 계약 변경은 사용자 승인 후에만 실행한다.

## Archived Plans
- archive summary: completed=26, parked=5
- older archived plans omitted=11
- `완료` [AgentOS 프로젝트 작업 하네스 문서 전환 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-project-work-harness-document-pivot.md) | reviewed_evidence=invalid | progress: Intent Sheet와 문서 전환 계획을 작성했다. 계획 header의 Gate 2 상태와 reviewer artifact가 실행 가능 여부의 기준이며, root project 문서는 아직 변경하지 않았다.
- `완료` [AgentOS read 도구 + 최소 에이전틱 루프 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-agentos-read-tool-execution-loop.md) | progress: 8개 마일스톤 구현·검증 완료, 전체 테스트 스위트 358 passed(회귀 없음)
- `완료` [AgentOS 부트스트랩 컨텍스트 안전장치 및 가시성 개선 구현 계획](.agentos/project/exec-plans/archive/2026-07-25-agentos-bootstrap-context-safety-and-visibility.md) | progress: 계획 초안 작성, Gate 2 리뷰 대기 중 (사용자 지시에 따라 하네스 에이전트 핵심 리뷰로 진행)
- `완료` [AgentOS PI형 세션 런타임 TUI 아키텍처 구현 계획](.agentos/project/exec-plans/archive/2026-07-24-agentos-pi-session-runtime-tui-architecture.md) | reviewed_evidence=invalid | outcome: 사용자는 TUI에서 이전 대화를 실제 다음 답변의 문맥으로 유지하고, 세션 재개와 branch가 올바른 대화 경로를 이어가며, provider 지연/실패 시 명확한 복구를 받는다. | progress: native predecessor(2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport)가 완료되어 `predecessor_completion_commit: 923d35e`가 기록되었고 sha…
- `완료` [AgentOS pi 스타일 부트스트랩 컨텍스트 주입 구현 계획](.agentos/project/exec-plans/archive/2026-07-24-agentos-pi-bootstrap-context.md) | progress: 계획 초안 작성, Gate 2 리뷰 대기 중 (핵심 하네스 서브에이전트만 최소 리뷰 — 사용자 지시에 따름)
- `구현 계획 (리뷰 대기)` [AgentOS TUI — pi TUI 클로닝 Phase 6: 입력 상호작용 기반 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-tui-pi-clone-phase6.md) | outcome: 사용자는 `/capabilities`에서 이식 기능의 준비 상태를 확인하고, slash command와 지원하는 argument를 Tab으로 완성하며, 기존 메시지 포커스 이동과 충돌 없는 단축키 안내를 받는다. | progress: 계획 초안 작성 완료, Gate 2 리뷰 대기. Phase 5가 완료 전이면 Task 0에서 중단한다.
- `리뷰 대기 (완료 후 '완료'로 변경)` [AgentOS TUI — pi/hermes TUI 클론 (Phase 5: 설정 관리 UI `/settings`) 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-tui-pi-clone-phase5.md) | progress: 계획 초안 작성, Gate 2 리뷰 대기 중 (아직 서브에이전트 리뷰를 요청하지 않음 — 이 세션의 목적은 계획 문서 작성까지)
- `완료` [AgentOS TUI Codex Slash Login 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-tui-codex-slash-login.md) | reviewed_evidence=invalid | outcome: 사용자는 TUI에서 Codex 로그인 시작, 현재 인증 상태 확인, 로그아웃까지 처리하는 핵심 흐름을 얻게 된다. 다만 실제 계정 승인 자체는 여전히 Codex CLI와 외부 브라우저/승인 화면에서 계속될 수 있으며, TUI는 그 진행 상태와 다음… | progress: 계획 범위를 core orchestration으로 축소했고, Gate 2 지적을 반영해 command 경계와 provider별 동작 규칙을 명시하는 revision 단계다. 현재 저장소에는 `/login`과 `/logout` slash command…
- `완료` [AgentOS pi-style LLM runtime 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-pi-style-llm-runtime.md) | reviewed_evidence=invalid | progress: core foundation 범위로 축소한 revision을 기준으로 구현과 검증을 완료했다. Codex는 external-CLI compatibility path를 canonical path로 유지한다.
- `완료` [AgentOS pi-style LLM runtime native auth/transport 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-pi-style-llm-runtime-native-auth-transport.md) | reviewed_evidence=invalid | progress: core foundation은 완료됐고, native OAuth/transport 범위는 아직 구현되지 않았다. 이번 계획은 deferred 범위를 implementation-ready execution plan으로 구체화하는 단계다.
- `완료` [AgentOS LLM 호출 런타임 아키텍처 개선 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-llm-invocation-runtime-architecture.md) | reviewed_evidence=invalid | outcome: 사용자는 설치된 `agentos` command를 기본 경로로 써야 하는지, `uv run`이 실제 병목인지, 후속 daemon 분리를 진행해도 되는지를 benchmark와 복구 절차로 명확히 판단할 수 있다. 바뀌지 않는 경계는 현재 `codex`… | progress: 측정 우선의 invocation runtime surface, typed invocation contract, launcher/recovery guidance, docs/project boundary, focused tests, isolated in…
- `완료` [AgentOS LLM Codex Streaming Structure 구현 계획](.agentos/project/exec-plans/archive/2026-07-23-agentos-llm-codex-streaming-structure.md) | reviewed_evidence=invalid | outcome: 사용자는 `agentos run --once --provider codex --json`과 TUI에서 Codex 응답이 프로세스 종료 후 한꺼번에 나타나는 대신, 생각 중 표시와 도구 실행 표시, 답변 텍스트를 더 빨리 보게 된다. 바뀌지 않는 경계… | progress: Gate 2 리뷰를 현재 plan hash 기준으로 재기록해 닫은 뒤, `CodexCliProvider`를 live stdout streaming 구조로 전환하고 focused/full verification까지 완료했다.
- `완료` [AgentOS TUI — pi/hermes TUI 클론 (Phase 4: 메시지 포커스 이동 및 클립보드 복사) 구현 계획](.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase4.md) | reviewed_evidence=invalid | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [AgentOS TUI — pi/hermes TUI 클로닝 Phase 3 구현 계획](.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase3.md) | progress: 계획 초안 작성 완료, Gate 2 리뷰 대기 중
- `완료` [AgentOS TUI — pi TUI 격차 해소 (Phase 2) 구현 계획](.agentos/project/exec-plans/archive/2026-07-22-tui-pi-clone-phase2.md) | reviewed_evidence=invalid | progress: 완료 — 마일스톤 1~6 구현 및 검증 완료
- `완료` [AgentOS TUI (Pi TUI Parity) 개선 구현 계획](.agentos/project/exec-plans/archive/2026-07-21-tui-ux-improvement.md) | progress: Gate 2 3차 리뷰까지 완료 — `plan-reviewer`/`principle-auditor`/`usability-reviewer` 모두 PASS. 구현 착수 대기 중
- `완료` [[TUI Transcript] 구현 계획](.agentos/project/exec-plans/archive/2026-07-21-tui-transcript-improvement.md) | progress: 완료
- `완료` [AgentOS TUI — pi TUI 격차 해소 (Phase 1) 구현 계획](.agentos/project/exec-plans/archive/2026-07-21-tui-pi-clone-phase1.md) | progress: 계획 초안 작성, Gate 2 리뷰 대기 중
- `완료` [AgentOS TUI 개선 1차 반복: 스트리밍 응답 및 기본 메뉴 구현](.agentos/project/exec-plans/archive/2026-07-20-tui-improvement.md) | progress: 구현 완료 및 fresh verification PASS
- `완료` [AgentOS TUI UX Architecture 구현 계획](.agentos/project/exec-plans/archive/2026-07-19-agentos-tui-ux-architecture.md) | reviewed_evidence=invalid | progress: 구현 완료 및 fresh verification PASS

## Reference Docs
- older reference docs omitted=0
- `리뷰 대기 (완료 후 '완료'로 변경)` [[계획 제목] 구현 계획](.agentos/project/exec-plans/TEMPLATE.md) | progress: 계획 초안 작성, 리뷰 대기 중 (상황에 따라 1줄 요약)
