# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-08-23T07:45:25Z

## Active Plans
- 현재 실행 중인 계획 없음
- older active plans omitted=0

## Archived Plans
- archive summary: completed=8, parked=0
- older archived plans omitted=0
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
