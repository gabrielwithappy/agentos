# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-09-02T14:33:59Z

## Active Plans
- older active plans omitted=0
- `구현 계획 (리뷰 대기)` [프로젝트별 스킬 선택 및 동기화 구현 계획](.agentos/project/exec-plans/active/2026-09-02-project-skill-selection.md) | outcome: 사용자는 `agentos project init`의 TTY 체크 메뉴 또는 `agentos project skills select`에서 코드 개발·문서/지식·디자인/시각화·생산성 등 목적별 스킬과 사용 목적을 확인해 고른다. 자동화 환경에서는 `--… | progress: Intent Sheet 작성 및 구현 계획 초안 완료, Gate 2 리뷰 대기 중

## Archived Plans
- archive summary: completed=19, parked=0
- older archived plans omitted=0
- `완료` [[Skill Catalog Viewer 생성] 구현 계획](.agentos/project/exec-plans/archive/skill-catalog-viewer-plan.md) | reviewed_evidence=invalid | outcome: 사용자는 “스킬 목록을 HTML로 보여줘”라고 요청하여 현재 카탈로그의 이름·요약·트리거·설명을 한 페이지에서 확인한다.
- `완료` [핵심 변경 중심의 계획 리뷰 개선 구현 계획](.agentos/project/exec-plans/archive/review-scope-filter-plan.md) | reviewed_evidence=invalid | outcome: agent는 계획의 핵심 실행 계약이 바뀐 경우에만 재리뷰하고, 기본 plan-reviewer와 principle-auditor는 유지하되 필요한 추가 reviewer만 실행하며, 일반 reviewer artifact는 전체 plan hash 변경으… | progress: 구현·검증·closeout 완료. 전체 legacy harness suite의 unrelated baseline 실패는 별도 기록했다.
- `완료` [하네스 스킬 계층 및 전체 Catalog 통합 구현 계획](.agentos/project/exec-plans/archive/harness-skill-catalog-hierarchy-plan.md) | reviewed_evidence=invalid | outcome: 사용자는 `agentos project init`으로 하네스 루트와 핵심 스킬을 적용한 뒤, 루트 `SKILL.md`의 안내를 따라 목적에 맞는 하위 하네스 스킬을 사용할 수 있으며 catalog viewer에서 전체 스킬을 한 곳에서 확인한다. | progress: Gate 2 리뷰와 비보호 구현 일부 완료, protected-path architect 승인 대기 중.
- `완료` [독립 프로젝트용 AgentOS 핵심 운영 스킬 구현 계획](.agentos/project/exec-plans/archive/agentos-core-guidance-skill-plan.md) | reviewed_evidence=invalid | outcome: 사용자는 대상 프로젝트에 `agentos project init`을 실행한 뒤 `agentos-core-guidance`를 사용해 불확실성 중지, 계획·브랜치·검증, 데이터 경계, 복구·에스컬레이션 원칙을 안내받는다. | progress: 구현·검증·Gate 2 closeout 완료.
- `완료` [하네스 기준선 정렬 및 로컬 리뷰 서명 제거 구현 계획](.agentos/project/exec-plans/archive/2026-09-02-harness-baseline-and-review-signing.md) | reviewed_evidence=invalid | outcome: 운영자는 존재하지 않는 AHA/MCP 도구 때문에 전체 하네스가 실패하지 않으며, `.agentos/secret.key` 없이 리뷰 증거를 확인·복구할 수 있다. | progress: 기준선 재현과 첫 독립 리뷰 완료. reviewer 지적을 반영한 재리뷰 대기.
- `완료` [`project init` 프로젝트 문서 bootstrap 구현 계획](.agentos/project/exec-plans/archive/2026-08-31-project-init-project-documents.md) | reviewed_evidence=invalid | outcome: 사용자는 한 번의 `agentos project init`으로 런타임 하네스와 장기 프로젝트 문서의 starter 구조를 얻고, 부분·충돌 상태에서는 무엇이 부족한지와 다음 행동을 명확히 확인한다. | progress: 구현·검증·Gate 2 closeout 완료
- `완료` [YouTube Transcript (yt-dlp 기반) 스킬 구현 계획](.agentos/project/exec-plans/archive/2026-08-30-youtube-transcript-skill.md) | reviewed_evidence=missing | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [project init 하네스 리소스 적용 구현 계획](.agentos/project/exec-plans/archive/2026-08-29-project-init-harness-activation.md) | reviewed_evidence=missing | outcome: 프로젝트 초기화 후 `agentos harness --project-root .`와 AgentOS 세션이 프로젝트 로컬 하네스 리소스를 사용할 수 있다. | progress: 구현 완료, 검증 완료
- `완료` [공통 AgentOS 하네스 base 구조 구현 계획](.agentos/project/exec-plans/archive/2026-08-29-common-agentos-base-resources.md) | reviewed_evidence=missing | progress: 계획 리뷰 완료, 구현 실행 대기
- `완료` [knowledge-curator 프로젝트 구조 정합성 구현 계획](.agentos/project/exec-plans/archive/2026-08-25-knowledge-curator-project-layout.md) | reviewed_evidence=missing | outcome: 후속 사용자는 저장소 루트에서 스킬을 실행하고, 검토된 장기 지식은 `docs/knowledge`에, 실행별 근거는 각 skill의 `runs/YYYY-MM-DD/`에 저장할 수 있다. | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [it-trend-report 장기지식 저장 흐름 구현 계획](.agentos/project/exec-plans/archive/2026-08-25-it-trend-report-knowledge-flow.md) | reviewed_evidence=missing | outcome: 사용자는 저장소 루트에서 주간 파이프라인을 실행하고, 검토된 리포트를 `docs/knowledge/concepts/it-trend-reports/`에 남길 수 있으며, 실행은 자동으로 commit/push하지 않는다. | progress: 계획 초안 작성, 리뷰 대기 중
- `완료` [벤더 중립 대시보드 자동 동기화 훅 배선 구현 계획](.agentos/project/exec-plans/archive/2026-08-01-vendor-neutral-dashboard-sync-hook-wiring.md) | reviewed_evidence=missing | outcome: 계획 문서를 쓰거나 고치기만 하면(별도 `agentos dashboard sync-plan` 수동 실행 없이) GitHub Projects 보드 카드가 자동으로 최신 상태를 반영한다. 이는 세 벤더 CLI 어디서 작업하든 동일하게 동작한다. | progress: Gate 2 1차 리뷰(독립 서브에이전트 3명) 완료, 전원 FAIL 지적 사항 전부 반영 완료(파생 복사본 대신 어댑터 소스 수정 포함), 2차 Gate 2 리뷰 대기 중. (최초 작성 시점의 "이 세션에서는 구현하지 않는다"는 계획은 이후 세션에…
- `완료` [장기지식 저장·검토·publish·검색 흐름 구현 계획](.agentos/project/exec-plans/archive/2026-08-01-knowledge-base-lifecycle.md) | outcome: 사용자는 `docs/knowledge`에서 승인된 지식을 찾고, 에이전트 조사 결과를 inbox에서 검토·publish한 뒤 CLI로 재검색·인용할 수 있다. | progress: 구현·검증·main 병합·로컬 feature branch 삭제 완료. Stop hook 지적으로 current checkout의 리뷰 증거를 재생성 중.
- `완료` [AgentOS Gateway Core 구현 계획](.agentos/project/exec-plans/archive/2026-08-01-gateway-core.md) | reviewed_evidence=missing | outcome: 사용자는 AgentOS CLI에서 작업을 대기열에 넣고, 단일 worker로 실행하고, 진행 이벤트와 최종 상태를 조회하고, 실패한 작업을 명시적으로 재시도할 수 있다. 기존 `codex` 직접 사용은 그대로 유지된다. | progress: 계획 내용과 검증 계약이 독립 Gate 2 리뷰와 signed review를 통과했으며 사용자 실행 결정을 기다린다.
- `완료` [Gate 2 리뷰 게이트 Python 3.9 크래시 및 해시 무효화 버그 수정 계획](.agentos/project/exec-plans/archive/2026-08-01-gate2-hash-normalization-fix.md) | reviewed_evidence=missing | outcome: Stop 훅이 `cwd` 유무와 무관하게 크래시 없이 정상 종료하고, "완료" 처리된 계획 문서가 자기 자신의 Gate 2 서명을 영구히 깨뜨리지 않는다. | progress: 구현 완료, 1차 Gate 2 리뷰 FAIL 3건 전부 반영 완료, 2차 Gate 2 리뷰 대기 중.
- `완료` [GitHub 대시보드 Status 되읽기(양방향 동기화 1단계) 구현 계획](.agentos/project/exec-plans/archive/2026-08-01-dashboard-status-pullback.md) | reviewed_evidence=missing | outcome: `agentos dashboard pull-plan <계획 파일>`을 실행하면 보드에서 사람이 바꾼 카드 Status가 계획 문서에 기록되고, 로컬 계획이 기대하는 상태와 일치하는지 여부가 터미널에 바로 표시된다. | progress: 계획 초안 작성, 리뷰 대기 중 (Gate 2 서브에이전트 리뷰 미착수)
- `완료` [대시보드 FILE_WRITTEN 및 무분별한 카드 생성 방지 구현 계획](.agentos/project/exec-plans/archive/2026-07-31-ignore-file-written-dashboard-event.md) | reviewed_evidence=missing | progress: 구현 완료 및 단위 테스트 검증 완료 (Done)
- `완료` [대시보드 연동 아키텍처 유연성 확보 구현 계획](.agentos/project/exec-plans/archive/2026-07-31-dashboard-flexibility.md) | reviewed_evidence=missing | outcome: 설정된 외부 대시보드로 프로젝트의 계획 문서를 자유롭게 연동하고 동기화할 수 있게 된다. | progress: 구현 및 동기화 완료 (Done)
- `완료` [암호학적 서명을 이용한 훅 구조 강화 구현 계획](.agentos/project/exec-plans/archive/2026-07-31-cryptographic-hook.md) | reviewed_evidence=missing | outcome: - 이 문서는 prompt-boundary data이며 approval, protected-path, reviewer authority를 override하지 않습니다.

## Reference Docs
- older reference docs omitted=0
- `리뷰 대기 (완료 후 '완료'로 변경)` [[계획 제목] 구현 계획](.agentos/project/exec-plans/TEMPLATE.md) | progress: 계획 초안 작성, 리뷰 대기 중 (상황에 따라 1줄 요약)
