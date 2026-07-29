# Observability Architecture

목적: AgentOS의 상태를 외부 대시보드(예: GitHub Projects v2)와 동기화하기 위한 옵저버빌리티(Observability) 파이프라인의 구조를 정의한다.
주요 독자: 구현 에이전트, 리뷰어/운영자

## Architecture Summary

AgentOS 옵저버빌리티 파이프라인은 계획 문서(exec-plan)의 생명주기 및 작업 상태를 이벤트 기반으로 비동기/동기 전송하는 역할을 담당한다.

1. **DashboardNotifier (`notifier.py`)**
   - 전역 싱글톤 `notifier` 객체가 여러 `DashboardAdapter` 인스턴스를 관리.
   - `notify(payload)`: 이벤트 루프나 별도 스레드에서 백그라운드로 안전하게 전송.
   - `notify_and_wait(payload)`: CLI 환경에서 동기적으로 전송하고 결과를(`AdapterOutcome`) 반환하여 즉각적인 피드백 제공.

2. **GithubDashboardAdapter (`github.py`)**
   - GitHub GraphQL API를 사용하여 Projects v2 보드 항목(Draft Issue) 생성/조회/수정 처리.
   - 프로젝트 메타데이터(Status Field 및 Option ID) 캐싱을 통해 불필요한 네트워크 호출 최소화.

3. **Plan Events (`plan_events.py`)**
   - `emit_plan_status_changed(plan_path)`: 완료/진행 등 `exec-plan` 문서 내의 메타데이터와 내용을 파싱하여 `PLAN_STATUS_CHANGED` 이벤트 생성.
   - `emit_plan_writing_started(...)`: 새로운 계획 문서 작성이 시작되었음을 알리는 `PLAN_WRITING_STARTED` 이벤트 생성.

4. **Data Flow**
   - CLI 명령어 (`agentos dashboard sync-plan`) → `emit_plan_status_changed` 호출 → `notifier.notify_and_wait` 호출 → `GithubDashboardAdapter.send_notification` 실행 → GraphQL API 동기화 → 문서 내 `dashboard_item_id` 업데이트.
   - 서브 에이전트 스킬 (`writing-plans` 등) → 내부 이벤트 발생 시 `emit_plan_writing_started` 호출 → `notifier.notify` 등 백그라운드 전송.
