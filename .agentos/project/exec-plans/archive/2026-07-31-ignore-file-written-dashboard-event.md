# 대시보드 FILE_WRITTEN 및 무분별한 카드 생성 방지 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-31<br>
> reviewed: true<br>
> user_request: 대시보드에 FILE_WRITTEN, CLI_EXIT 등 내부 텔레메트리 이벤트 카드가 무분별하게 생성되는 문제를 방지하기 위해 대시보드 알림 이벤트를 필터링하도록 개선한다.<br>
> active_agent: <br>
> active_session: <br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg00lBg<br>
> implementation_started_at: 2026-07-31T23:51:00+09:00<br>
> implementation_completed_at: 2026-07-31T23:52:00+09:00<br>
> implementation_duration: 1m<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:**
- 파일 작성(`FILE_WRITTEN`) 및 세션 종료/오류(`CLI_EXIT`, `CLI_EOF`, `CLI_ERROR`)와 같은 내부 텔레메트리 이벤트가 GitHub Projects v2 보드에 불필요한 노이즈 카드로 자동 생성되는 문제를 차단한다.

**사용자 결과 요약:**
- 사용자가 문서 및 파일 코드를 수정하거나 CLI 세션을 종료할 때 깃허브 대시보드에 `FILE_WRITTEN` 같은 불필요한 카드가 생성되지 않고, 실제 계획(exec-plan) 및 태스크 상태 이벤트만 깔끔하게 보드에 반영된다.

**의존성 분석:**
- 외부 의존성: 없음 (기존 `GithubDashboardAdapter` 필터링 로직 보완)

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, `.agentos/project/exec-plans/active/2026-07-31-ignore-file-written-dashboard-event.md`
- Durable Result Surface: `agentos/observability/adapters/github.py`, `tests/test_adapters.py`

**진행 상태:** 구현 완료 및 단위 테스트 검증 완료 (Done)

**아키텍처:**
- `GithubDashboardAdapter` 상단에 명시적 무시 대상 라이프사이클 이벤트 상수 정의: `_IGNORED_EVENTS = {"FILE_WRITTEN", "CLI_EOF", "CLI_EXIT", "CLI_ERROR"}`
- `GithubDashboardAdapter.send_notification` 시작 위치에서 `if event in _IGNORED_EVENTS: return` 구문으로 조기 리턴(Early return) 처리.

**기술 스택:**
- Python 3.11+, pytest

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 완료 |
| 완료됨 | 필터 로직 구현, 단위 테스트 작성 및 18개 테스트 PASS 검증 완료 |
| 현재 위치 | 구현 완료 (Done) |
| 다음 단계 | 계획 문서 동기화 |
| 완료 신호 | `pytest tests/test_adapters.py` 18개 PASS 및 `FILE_WRITTEN` 카드 생성 차단 확인 |

## 사용자 진행 계획

### 마일스톤 1: 무시 대상 라이프사이클 이벤트 필터 도입
- [x] `agentos/observability/adapters/github.py` 파일에 `_IGNORED_EVENTS = {"FILE_WRITTEN", "CLI_EOF", "CLI_EXIT", "CLI_ERROR"}` 정의
- [x] `send_notification()` 시작 위치에서 `event in _IGNORED_EVENTS` 체크 시 조기 리턴 로직 추가

### 마일스톤 2: 단위 테스트 작성 및 검증
- [x] `tests/test_adapters.py`에 `test_github_adapter_ignores_file_written_event` 및 `test_github_adapter_ignores_telemetry_events` 테스트 케이스 추가
- [x] `uv run pytest tests/test_adapters.py` 실행하여 전선 테스트 통과 검증 (18 passed)

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 무시 대상 라이프사이클 이벤트 필터 도입 | `FILE_WRITTEN` 등 무분별한 파일/세션 알림 시 깃허브 대시보드 카드 미생성 | `agentos/observability/adapters/github.py` | `Run:` `uv run pytest tests/test_adapters.py` / `Expected:` `PASS` |
| 2. 단위 테스트 추가 및 검증 | `FILE_WRITTEN` 알림 수신 시 GraphQL 호출 없이 무시됨을 검증하는 테스트 통과 | `tests/test_adapters.py` | `Run:` `uv run pytest tests/test_adapters.py -k test_github_adapter_ignores_file_written_event` / `Expected:` `1 passed` |

## 리뷰 반영 이력
- **1차 리뷰 반영:** `plan-reviewer` 피드백 반영: `user_request` 필드 상세 구체화, 구현 단계별 `- [ ]` 체크박스 명시, `_IGNORED_EVENTS` 대상 이벤트 목록(FILE_WRITTEN, CLI_EOF, CLI_EXIT, CLI_ERROR) 명확화.

## 구현 결과
- `GithubDashboardAdapter`에 `_IGNORED_EVENTS` 텔레메트리 필터를 도입하여 `FILE_WRITTEN`, `CLI_EOF`, `CLI_EXIT`, `CLI_ERROR` 수신 시 GitHub GraphQL API 호출을 조기 차단하도록 구현하였습니다.
- `tests/test_adapters.py`에 파라미터화 단위 테스트를 추가하고 `pytest` 18개 테스트 모음 통과를 검증하였습니다.

## 사용 방법
- 별도의 추가 조치 없이 파일 수정이나 터미널 세션 종료 시 `FILE_WRITTEN` 알림이 깃허브 대시보드에 불필요한 카드로 추가되지 않습니다.

## 아카이브 결정
- 모든 구현 및 자동화 단위 테스트 검증이 완료되었으므로 활성 계획 완료 상태로 관리합니다.
