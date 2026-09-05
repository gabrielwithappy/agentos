# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-09-05T03:46:36Z

## Active Plans
- older active plans omitted=0
- `완료` [redundant knowledge-curator 에이전트 제거 및 스킬 일원화 구현 계획](.agentos/project/exec-plans/active/2026-09-05-remove-redundant-knowledge-curator-agent.md) | reviewed_evidence=invalid | progress: 구현 및 전체 검증 완료

## Archived Plans
- archive summary: completed=31, parked=0
- older archived plans omitted=11
- `완료` [[Skill Catalog Viewer 생성] 구현 계획](.agentos/project/exec-plans/archive/skill-catalog-viewer-plan.md) | reviewed_evidence=invalid | outcome: 사용자는 “스킬 목록을 HTML로 보여줘”라고 요청하여 현재 카탈로그의 이름·요약·트리거·설명을 한 페이지에서 확인한다.
- `완료` [핵심 변경 중심의 계획 리뷰 개선 구현 계획](.agentos/project/exec-plans/archive/review-scope-filter-plan.md) | reviewed_evidence=invalid | outcome: agent는 계획의 핵심 실행 계약이 바뀐 경우에만 재리뷰하고, 기본 plan-reviewer와 principle-auditor는 유지하되 필요한 추가 reviewer만 실행하며, 일반 reviewer artifact는 전체 plan hash 변경으… | progress: 구현·검증·closeout 완료. 전체 legacy harness suite의 unrelated baseline 실패는 별도 기록했다.
- `완료` [하네스 스킬 계층 및 전체 Catalog 통합 구현 계획](.agentos/project/exec-plans/archive/harness-skill-catalog-hierarchy-plan.md) | reviewed_evidence=invalid | outcome: 사용자는 `agentos project init`으로 하네스 루트와 핵심 스킬을 적용한 뒤, 루트 `SKILL.md`의 안내를 따라 목적에 맞는 하위 하네스 스킬을 사용할 수 있으며 catalog viewer에서 전체 스킬을 한 곳에서 확인한다. | progress: Gate 2 리뷰와 비보호 구현 일부 완료, protected-path architect 승인 대기 중.
- `완료` [독립 프로젝트용 AgentOS 핵심 운영 스킬 구현 계획](.agentos/project/exec-plans/archive/agentos-core-guidance-skill-plan.md) | reviewed_evidence=invalid | outcome: 사용자는 대상 프로젝트에 `agentos project init`을 실행한 뒤 `agentos-core-guidance`를 사용해 불확실성 중지, 계획·브랜치·검증, 데이터 경계, 복구·에스컬레이션 원칙을 안내받는다. | progress: 구현·검증·Gate 2 closeout 완료.
- `완료` [setup 시 번들 제외 스킬 자동 정리 및 유령 카탈로그 제거 계획](.agentos/project/exec-plans/archive/2026-09-05-setup-prune-unbundled-skills.md) | reviewed_evidence=invalid | progress: 계획 초안 작성, 독립 리뷰 대기 중
- `완료` [manifest 거버넌스 기능 제거 구현 계획](.agentos/project/exec-plans/archive/2026-09-05-remove-manifest-governance.md) | progress: 계획 초안 작성, 구현 전 Gate 2 리뷰 대기 중
- `완료` [harness-loop, mcp, agent-token-info 레거시 하네스 스킬 제거 계획](.agentos/project/exec-plans/archive/2026-09-05-remove-legacy-harness-skills.md) | reviewed_evidence=invalid | progress: 계획 초안 작성, 독립 리뷰 대기 중
- `완료` [knowledge-curator harness 경로 정규화 구현 계획](.agentos/project/exec-plans/archive/2026-09-05-knowledge-curator-path-normalization.md) | reviewed_evidence=invalid | progress: 계획 초안 작성, 독립 리뷰 대기 중
- `완료` [프로젝트 문서 최신화 구현 계획](.agentos/project/exec-plans/archive/2026-09-04-update-project-docs.md) | reviewed_evidence=invalid | outcome: 최신 변경 사항과 의사 결정 내용이 `06-decisions-change-log.md` 문서에 깔끔하게 기록되어, 다음 작업 시 헷갈리지 않고 정확한 프로젝트 히스토리를 파악할 수 있다. | progress: 실행 대기
- `완료` [의미 중심 하네스 리뷰 효율화 구현 계획](.agentos/project/exec-plans/archive/2026-09-04-reviewer-semantic-efficiency.md) | reviewed_evidence=invalid | progress: 독립 코드베이스 조사와 Intent Sheet 작성이 끝났고, Gate 2 리뷰 및 protected architect 승인이 필요하다.
- `완료` [project init 스킬 카탈로그/설치 정합성 개선 구현 계획](.agentos/project/exec-plans/archive/2026-09-04-project-skill-catalog-install-alignment.md) | reviewed_evidence=invalid | progress: 완료. (검증 통과 및 사용 방법 업데이트 완료)
- `완료` [계획 리뷰어 오케스트레이션 구현 계획](.agentos/project/exec-plans/archive/2026-09-04-plan-reviewer-orchestrator.md) | reviewed_evidence=invalid | outcome: 계획 리뷰가 `plan-reviewer → principle-auditor → (필요 시 usability-reviewer)` 순서로 한 번씩 진행되고, 충돌·실패·재리뷰 사유와 다음 행동을 하나의 artifact/check 출력에서 확인할 수 있다… | progress: 1차 독립 리뷰 FAIL 후 계획 수정, fresh Gate 2 재리뷰 대기 중
- `완료` [계획문서 frontmatter metadata 표준화 구현 계획](.agentos/project/exec-plans/archive/2026-09-04-plan-frontmatter.md) | reviewed_evidence=invalid | outcome: 계획을 열었을 때 상태, 리뷰 여부, 담당 에이전트, 실행 시점, 계획 식별 정보를 문서 상단에서 한눈에 확인할 수 있으며, 기존 계획도 깨지지 않는다. | progress: 계획 초안 작성, 독립 리뷰 대기 중
- `완료` [project init 스킬 선택 토글 UX 구현 계획](.agentos/project/exec-plans/archive/2026-09-03-project-init-toggle-skill-selector.md) | reviewed_evidence=invalid | outcome: 사용자는 optional skill 목록에서 위/아래로 항목을 이동하고 Space로 체크를 켜고 끄며 Enter로 확정할 수 있다. 비대화형 자동화 사용자는 기존처럼 `--skills`를 사용할 수 있다. | progress: 구현과 검증 완료.
- `완료` [프로젝트별 스킬 선택 및 동기화 구현 계획](.agentos/project/exec-plans/archive/2026-09-02-project-skill-selection.md) | reviewed_evidence=invalid | outcome: 사용자는 `agentos project init`의 TTY 체크 메뉴 또는 `agentos project skills select`에서 코드 개발·문서/지식·디자인/시각화·생산성 등 목적별 스킬과 사용 목적을 확인해 고른다. 자동화 환경에서는 `--… | progress: Intent Sheet 작성 및 구현 계획 초안 완료, Gate 2 리뷰 대기 중
- `완료` [하네스 기준선 정렬 및 로컬 리뷰 서명 제거 구현 계획](.agentos/project/exec-plans/archive/2026-09-02-harness-baseline-and-review-signing.md) | reviewed_evidence=invalid | outcome: 운영자는 존재하지 않는 AHA/MCP 도구 때문에 전체 하네스가 실패하지 않으며, `.agentos/secret.key` 없이 리뷰 증거를 확인·복구할 수 있다. | progress: 기준선 재현과 첫 독립 리뷰 완료. reviewer 지적을 반영한 재리뷰 대기.
- `완료` [`project init` 프로젝트 문서 bootstrap 구현 계획](.agentos/project/exec-plans/archive/2026-08-31-project-init-project-documents.md) | reviewed_evidence=invalid | outcome: 사용자는 한 번의 `agentos project init`으로 런타임 하네스와 장기 프로젝트 문서의 starter 구조를 얻고, 부분·충돌 상태에서는 무엇이 부족한지와 다음 행동을 명확히 확인한다. | progress: 구현·검증·Gate 2 closeout 완료
- `완료` [YouTube Transcript (yt-dlp 기반) 스킬 구현 계획](.agentos/project/exec-plans/archive/2026-08-30-youtube-transcript-skill.md) | reviewed_evidence=missing | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [project init 하네스 리소스 적용 구현 계획](.agentos/project/exec-plans/archive/2026-08-29-project-init-harness-activation.md) | reviewed_evidence=missing | outcome: 프로젝트 초기화 후 `agentos harness --project-root .`와 AgentOS 세션이 프로젝트 로컬 하네스 리소스를 사용할 수 있다. | progress: 구현 완료, 검증 완료
- `완료` [공통 AgentOS 하네스 base 구조 구현 계획](.agentos/project/exec-plans/archive/2026-08-29-common-agentos-base-resources.md) | reviewed_evidence=missing | progress: 계획 리뷰 완료, 구현 실행 대기

## Reference Docs
- older reference docs omitted=0
- `구현 계획 (리뷰 대기)` [[계획 제목] 구현 계획](.agentos/project/exec-plans/TEMPLATE.md) | progress: 계획 초안 작성, 리뷰 대기 중 (상황에 따라 1줄 요약)
