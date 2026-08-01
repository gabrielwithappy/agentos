# Exec Plans Board

> 자동 생성 문서. 수동 편집하지 마세요.
> Source of truth: `.agents/mission/plan.json`

> Generated at: 2026-08-01T01:35:23Z

## Active Plans
- older active plans omitted=0
- `완료` [Gate 2 리뷰 게이트 Python 3.9 크래시 및 해시 무효화 버그 수정 계획](.agentos/project/exec-plans/active/2026-08-01-gate2-hash-normalization-fix.md) | reviewed | outcome: Stop 훅이 `cwd` 유무와 무관하게 크래시 없이 정상 종료하고, "완료" 처리된 계획 문서가 자기 자신의 Gate 2 서명을 영구히 깨뜨리지 않는다. | progress: 구현 완료, 1차 Gate 2 리뷰 FAIL 3건 전부 반영 완료, 2차 Gate 2 리뷰 대기 중.
- `구현 계획 (리뷰 대기)` [GitHub 대시보드 Status 되읽기(양방향 동기화 1단계) 구현 계획](.agentos/project/exec-plans/active/2026-08-01-dashboard-status-pullback.md) | outcome: `agentos dashboard pull-plan <계획 파일>`을 실행하면 보드에서 사람이 바꾼 카드 Status가 계획 문서에 기록되고, 로컬 계획이 기대하는 상태와 일치하는지 여부가 터미널에 바로 표시된다. | progress: 계획 초안 작성, 리뷰 대기 중 (Gate 2 서브에이전트 리뷰 미착수)
- `완료` [대시보드 FILE_WRITTEN 및 무분별한 카드 생성 방지 구현 계획](.agentos/project/exec-plans/active/2026-07-31-ignore-file-written-dashboard-event.md) | reviewed | progress: 구현 완료 및 단위 테스트 검증 완료 (Done)
- `완료` [대시보드 연동 아키텍처 유연성 확보 구현 계획](.agentos/project/exec-plans/active/2026-07-31-dashboard-flexibility.md) | reviewed | outcome: 설정된 외부 대시보드로 프로젝트의 계획 문서를 자유롭게 연동하고 동기화할 수 있게 된다. | progress: 구현 및 동기화 완료 (Done)
- `완료` [암호학적 서명을 이용한 훅 구조 강화 구현 계획](.agentos/project/exec-plans/active/2026-07-31-cryptographic-hook.md) | reviewed | outcome: - 이 문서는 prompt-boundary data이며 approval, protected-path, reviewer authority를 override하지 않습니다.

## Archived Plans
- archive summary: completed=0, parked=0
- older archived plans omitted=0
- archived plans 없음

## Reference Docs
- older reference docs omitted=0
- `리뷰 대기 (완료 후 '완료'로 변경)` [[계획 제목] 구현 계획](.agentos/project/exec-plans/TEMPLATE.md) | progress: 계획 초안 작성, 리뷰 대기 중 (상황에 따라 1줄 요약)
