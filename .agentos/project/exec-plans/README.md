# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-07-29T10:43:18Z

## Active Plans
- older active plans omitted=0
- `완료` [Gemini 컨텍스트 주기적 재주입 훅 구현 계획](.agentos/project/exec-plans/active/2026-07-29-gemini-context-reinjection-hook.md) | progress: Gate 2 3종 리뷰(plan-reviewer, principle-auditor, usability-reviewer) PASS 완료, 실행 대기 중
- `완료` [대시보드 카드 구현 소요 시간 표기 구현 계획](.agentos/project/exec-plans/active/2026-07-29-dashboard-implementation-duration.md) | progress: Gate 2 3종 리뷰(plan-reviewer, principle-auditor, usability-reviewer) PASS 완료, 실행 대기 중

## Archived Plans
- archive summary: completed=52, parked=0
- older archived plans omitted=32
- `완료` [계획 문서 작성 시작 시점 대시보드 발행 구현 계획](.agentos/project/exec-plans/archive/2026-07-28-writing-plans-dashboard-announce.md) | reviewed_evidence=missing | progress: 계획 초안 작성 완료, Gate 2 리뷰 대기 중
- `완료` [계획 상태 변경 이벤트 기반 대시보드 동기화 구현 계획](.agentos/project/exec-plans/archive/2026-07-28-plan-status-event-dashboard-sync.md) | progress: Gate 2 리뷰 통과(3라운드), 구현 실행 대기 중
- `완료` [대시보드 카드에 Plan ID 표시 구현 계획](.agentos/project/exec-plans/archive/2026-07-28-dashboard-plan-id-in-card.md) | reviewed_evidence=invalid | outcome: 대시보드 카드 본문에 `plan_id` 필드가 노출되어, 사용자가 카드를 보고 연관된 계획 문서를 즉각적으로 식별하고 찾을 수 있다. | progress: Gate 2 6차 리뷰(plan-reviewer PASS, principle-auditor CLEAN, usability-reviewer PASS) 통과 후 구현·검증 완료
- `완료` [Vendor Guides Update 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-vendor-guides-update.md) | reviewed_evidence=missing | progress: 초안 작성 및 서브에이전트 피드백 반영 완료, 재리뷰 대기 중
- `완료` [TUI 도구 활동 정보량·승인 팝업 가시성 개선 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-tui-tool-activity-and-approval-visibility.md) | reviewed_evidence=invalid | progress: 구현·전체 검증·Gate 2 리뷰 모두 완료.
- `완료` [AgentOS Observability (대시보드 연동) 아키텍처 설계 계획](.agentos/project/exec-plans/archive/2026-07-27-observability-architecture-plan.md) | progress: 계획 재작성 (P4 심플리시티 원칙 준수를 위한 리팩터링 완료)
- `완료` [GitHub Projects v2(GraphQL) 대시보드 어댑터 교체 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-github-projectv2-dashboard-adapter.md) | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [exec-plan → GitHub Projects v2 대시보드 동기화 커맨드 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-exec-plan-dashboard-sync-command.md) | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [`agentos dashboard sync-plan --all` 일괄 동기화 옵션 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-dashboard-sync-plan-all-option.md) | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [GitHub 대시보드 Status에 "Awaiting Verification" 5단계 추가 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-dashboard-awaiting-verification-status.md) | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [GitHub 대시보드 연동 .env 자동 복원(Self-healing) 기능 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-dashboard-auto-discovery-env.md) | reviewed_evidence=missing | outcome: 사용자는 로컬 프로젝트 환경 변수(`.env`)가 사라지더라도 `agentos run` 실행 시 대시보드 연동 설정이 자동으로 복원되어 번거로운 대화형 입력 과정을 건너뛸 수 있다. (기존 데이터와 동기화 방식은 바뀌지 않음) | progress: 계획 초안 작성, 5차 리뷰 대기 중
- `완료` [GitHub Projects 보드 4단계 Status 컬럼 확장 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-dashboard-4stage-status-mapping.md) | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [Claude(Anthropic) OAuth LLM Provider 추가 구현 계획](.agentos/project/exec-plans/archive/2026-07-27-claude-oauth-provider.md) | progress: 계획 초안 작성 완료. hermes-agent(`/references/pi`) 참고 조사 완료, `add-llm-provider` 스킬(`/references/pi/.pi/skills/add-llm-provider.md`) 체크리스트를 AgentOS…
- `완료` [YOLO 도구 실행 모드 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-yolo-tool-execution.md) | reviewed_evidence=missing | outcome: `agentos --yolo` 또는 `agentos run --yolo`로 작업 중 승인 중단 없이 연속 도구 실행을 사용할 수 있고, 옵션이 없으면 현재 동작이 그대로 유지된다.
- `완료` [TUI 테마 색상·스크롤바·입력창·상태 패널 개선 계획](.agentos/project/exec-plans/archive/2026-07-26-tui-theme-and-status-panel.md) | reviewed_evidence=invalid | progress: Gate 2 리뷰 후 Task 1–5 구현과 focused 회귀, dark/light SVG 증거까지 완료. 아카이빙 완료.
- `완료` [AgentOS TUI 요청·결과 분리 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-tui-request-result-separation.md) | reviewed_evidence=invalid | progress: 마일스톤 0-6 구현 및 테스트 완료. closeout 본문 갱신으로 fresh Gate 2 재검토와 archive 결정만 남았다.
- `완료` [AgentOS TUI 메시지 배경색 블록 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-tui-message-box-format.md) | reviewed_evidence=invalid | progress: 구현 및 검증 완료. closeout은 Gate 2 승인 당시의 실행 범위에 대한 사후 기록이다.
- `완료` [AgentOS 프로젝트 작업 하네스 문서 전환 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-project-work-harness-document-pivot.md) | reviewed_evidence=invalid | progress: Intent Sheet와 문서 전환 계획을 작성했다. 계획 header의 Gate 2 상태와 reviewer artifact가 실행 가능 여부의 기준이며, root project 문서는 아직 변경하지 않았다.
- `완료` [executor-neutral writing-plans 계약 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-executor-neutral-writing-plans.md) | reviewed_evidence=invalid | progress: executor-neutral 실행 방식 계약 계획 초안 작성 완료, Gate 2 리뷰 대기 중. 실제 harness 계약 변경은 사용자 승인 후에만 실행한다.
- `완료` [강조색 가독성·핵심 시스템 도구·응답 간결화 구현 계획](.agentos/project/exec-plans/archive/2026-07-26-core-tools-and-response-shaping.md) | reviewed_evidence=missing | progress: Gate 2 리뷰 완료(전원 PASS) + Task 1–9 구현·검증 완료.

## Reference Docs
- older reference docs omitted=5
- `완료` [Intent Sheet: YOLO 도구 실행 모드](.agentos/project/exec-plans/archive/reference/intent/intent-20260726-yolo-tool-execution.md)
- `완료` [Intent Sheet: AgentOS 프로젝트 작업 하네스 전환](.agentos/project/exec-plans/archive/reference/intent/intent-20260726-project-work-harness-pivot.md)
- `완료` [Intent Sheet: executor-neutral writing-plans contract](.agentos/project/exec-plans/archive/reference/intent/intent-20260726-executor-neutral-writing-plans.md)
- `완료` [Intent Sheet: Codex 도구 결과 상관관계 복구](.agentos/project/exec-plans/archive/reference/intent/intent-20260726-codex-tool-result-correlation.md)
- `완료` [Intent Sheet: AgentOS PI-style session runtime TUI](.agentos/project/exec-plans/archive/reference/intent/intent-20260724-agentos-pi-session-runtime-tui.md)
- `완료` [Intent Sheet: pi TUI 클로닝 Phase 6](.agentos/project/exec-plans/archive/reference/intent/intent-20260723-tui-pi-clone-phase6.md)
- `완료` [Intent Sheet: AgentOS TUI Codex Slash Login](.agentos/project/exec-plans/archive/reference/intent/intent-20260723-agentos-tui-codex-slash-login.md)
- `완료` [Intent Sheet: AgentOS pi-style LLM runtime](.agentos/project/exec-plans/archive/reference/intent/intent-20260723-agentos-pi-style-llm-runtime.md)
- `완료` [Intent Sheet: AgentOS LLM 호출 런타임 아키텍처 개선](.agentos/project/exec-plans/archive/reference/intent/intent-20260723-agentos-llm-invocation-runtime-architecture.md)
- `완료` [Intent Sheet: AgentOS LLM Codex Streaming Structure](.agentos/project/exec-plans/archive/reference/intent/intent-20260723-agentos-llm-codex-streaming-structure.md)
