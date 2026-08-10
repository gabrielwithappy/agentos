# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-08-10T16:02:04Z

## Active Plans
- older active plans omitted=0
- `구현 계획 (실행 대기)` [Knowledge Curator OKF v0.2 적용 구현 계획](.agentos/project/exec-plans/active/2026-08-11-knowledge-curator-okf-v02-adoption.md) | reviewed_evidence=invalid | progress: 참조 구현 비교와 후보 선별을 완료했고, 계획 Gate 2 리뷰 대기 중이다.

## Archived Plans
- archive summary: completed=62, parked=0
- older archived plans omitted=42
- `완료` [[Frontmatter 전환] 구현 계획 문서 메타데이터 포맷 변경](.agentos/project/exec-plans/archive/2026-08-11-exec-plan-frontmatter.md) | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [Stop 훅의 계획 리뷰 초점화 구현 계획](.agentos/project/exec-plans/archive/2026-08-10-stop-hook-review-focus.md) | reviewed_evidence=invalid | outcome: 사용자는 artifact 형식 누락 때문에 대화 종료가 막히지 않으며, 검증되지 않은 계획은 구현을 시작하려는 순간에만 명확한 복구 안내와 함께 차단된다. | progress: Intent Sheet와 현재 훅·실행 게이트 조사를 마쳤고, Gate 2 리뷰를 기다린다.
- `완료` [Knowledge Curator 독립 스킬 구현 계획](.agentos/project/exec-plans/archive/2026-08-10-knowledge-curator-standalone-skill.md) | reviewed_evidence=invalid | outcome: 사용자는 `catalog/skills/knowledge-curator/` 폴더를 원하는 skill root의 `knowledge-curator/`로 복사한 뒤, 그 복사본의 스킬 안내와 Python CLI로 knowledge Git checkout의… | progress: 독립 Gate 2 리뷰와 manifest integrity 검증 완료, 실행 대기 중.
- `완료` [Codex Stop hook 계약 복구 구현 계획](.agentos/project/exec-plans/archive/2026-08-10-codex-stop-hook-contract.md) | reviewed_evidence=invalid | outcome: Codex 세션 종료 때 `invalid stop hook JSON output` 오류가 출력되지 않는다. Claude Code의 Stop gate는 변경하지 않는다. | progress: 간단한 Gate 2 리뷰 대기.
- `완료` [AHA·스킬 양방향 장기지식 저장소 및 Git 연동 구현 계획](.agentos/project/exec-plans/archive/2026-08-09-aha-knowledge-skill-git.md) | reviewed_evidence=invalid | outcome: 사용자는 AgentOS 설치 여부와 관계없이 skill runtime 또는 `aha knowledge` 중 가능한 진입점을 선택해 지식을 작성·검토·publish하고, GitHub 저장소에서 상대 링크로 연결된 지식 graph를 탐색하며, 다른 프로… | progress: Gate 2 독립 리뷰 완료, Task 0 실행 대기 중
- `완료` [장기지식 저장·검토·publish·검색 흐름 구현 계획](.agentos/project/exec-plans/archive/2026-08-01-knowledge-base-lifecycle.md) | outcome: 사용자는 `docs/knowledge`에서 승인된 지식을 찾고, 에이전트 조사 결과를 inbox에서 검토·publish한 뒤 CLI로 재검색·인용할 수 있다. | progress: 구현·검증·main 병합·로컬 feature branch 삭제 완료. Stop hook 지적으로 current checkout의 리뷰 증거를 재생성 중.
- `완료` [AgentOS TUI 도구 로그 밀도 개선 구현 계획](.agentos/project/exec-plans/archive/2026-07-30-tui-tool-log-density.md) | outcome: 사용자는 완료된 도구 실행의 이름·성공/실패 요약을 바로 보고, `Ctrl+O`로 해당 턴을 포함한 모든 도구 활동의 호출 인자와 결과를 펼치거나 다시 접을 수 있다. | progress: raw provider stderr/raw environment 음성 검증과 light/dark/`NO_COLOR` 도구 활동 coverage를 보완한 뒤 fresh verification을 완료했다. 계획은 사용자의 명시적 archive 요청 전까…
- `완료` [AgentOS 전역 CLI화 및 안전한 프로젝트 부트스트랩 구현 계획](.agentos/project/exec-plans/archive/2026-07-29-global-cli-portable-project-bootstrap.md) | reviewed_evidence=invalid | outcome: 사용자는 `uv tool install agentos`로 CLI를 설치하고 `agentos --help`로 PATH를 확인한 뒤, source checkout 없이 `cd my-project && agentos setup`을 실행해 새 프로젝트에서… | progress: package-owned bridge와 portable project bootstrap을 구현하고 focused·isolated-install·public 검증을 완료했다.
- `완료` [Gemini 컨텍스트 주기적 재주입 훅 구현 계획](.agentos/project/exec-plans/archive/2026-07-29-gemini-context-reinjection-hook.md) | progress: Gate 2 3종 리뷰(plan-reviewer, principle-auditor, usability-reviewer) PASS 완료, 실행 대기 중
- `완료` [대시보드 카드 구현 소요 시간 표기 구현 계획](.agentos/project/exec-plans/archive/2026-07-29-dashboard-implementation-duration.md) | progress: Gate 2 3종 리뷰(plan-reviewer, principle-auditor, usability-reviewer) PASS 완료, 실행 대기 중
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
