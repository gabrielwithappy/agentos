# AgentOS Observability (대시보드 연동) 아키텍처 설계 계획

> **상태:** 완료
> **작성일:** 2026-07-27<br>
> reviewed: true (리뷰 증거 파일 생성 전까지 절대 true로 변경 불가)<br>
> active_agent: antigravity<br>
> active_session: d01ec827-63ba-4019-bfea-9a4f7b1d576e<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg0PE3k<br>
> implementation_started_at: 2026-07-27T08:00:00Z<br>
> implementation_completed_at: 2026-07-27T08:09:00Z<br>
> implementation_duration: 9 minutes<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- AgentOS 에이전트 실행 계획 및 상태를 외부 대시보드(GitHub Projects, Linear 등)와 동기화하기 위한 단순 알림 객체(Notifier) 및 어댑터 기반 Built-in 관측성 아키텍처 설계 및 구축.

**사용자 결과 요약:** 
- 시스템은 에이전트 작업 시 별도 도구 호출 없이 백그라운드에서 투명하게 프로젝트 상태를 대시보드에 연동/동기화할 수 있게 되어 마찰력이 줄어들고 투명성이 확보됩니다. API 토큰 등 초기 설정만 마치면 이후 과정은 자동으로 이루어지며, 통신 실패 시에도 메인 실행을 방해하지 않고 경고 로깅으로 안전하게 처리됩니다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 대상 대시보드 API (GitHub Projects, Linear 등), 환경 변수(`GITHUB_TOKEN`, `LINEAR_API_KEY`) 필요.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 리뷰 증거 파일, 이 계획 문서의 완료 증거
- Durable Result Surface: `agentos/observability/` 디렉터리 내 단순 알림(Notifier) 및 어댑터 플러그인 코드, 사용자 설정 가이드 문서

**진행 상태:** 계획 재작성 (P4 심플리시티 원칙 준수를 위한 리팩터링 완료)

**아키텍처:** 
- 비동기 단순 알림 객체 (DashboardNotifier) 및 플러그인 어댑터 (fire-and-forget 방식)

**기술 스택:** 
- AgentOS Hooking 시스템, 대상 외부 대시보드 REST API/SDK, Python `asyncio` (논블로킹 백그라운드 태스크)

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 초기 개념 설계, 서브 에이전트 리뷰 피드백 반영(P4 원칙에 맞춘 구조 단순화) |
| 현재 위치 | 2차 하네스 리뷰 진행 및 반영 완료 |
| 다음 단계 | 마일스톤 1 (비동기 Notifier 뼈대 구축) 구현 |
| 완료 신호 | 테스트 환경에서 상태 변경 알림이 Mock 대시보드 API 어댑터까지 직통으로 전달되며, 네트워크 에러 시 OS 중단 없이 로깅 처리됨을 확인 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 알림 시스템 구축 | OS 백그라운드 비동기 통신 준비 완료 | `agentos/observability/notifier.py` | `Run:` `uv run pytest tests/test_notifier.py` / `Expected:` 100% PASS |
| 2. 상태 훅 연동 | 파일 저장 등 OS 상태 변경 시 알림 자동 발송 | `agentos/terminal/hooks.py` | `Run:` `OBSERVABILITY_ENABLED=1 agentos run --json event-type grep "TASK_STATE_CHANGED"` / `Expected:` 상태 변경 알림 발송 로그 확인 |
| 3. 대시보드 어댑터 | 실제 GitHub 등 대시보드 UI 연동 토큰 가이드 제공 및 작동 | `agentos/observability/adapters/`, `docs/observability-setup.md` | `Run:` `uv run pytest tests/test_adapters.py` / `Expected:` Mock API 전송 100% PASS |
| 4. 에러 복구 강화 | 토큰 만료나 인터넷 단절 시 에러 메시지만 출력하고 작업 정상 진행 | `agentos/observability/notifier.py` | `Run:` `uv run pytest tests/test_notifier_error_recovery.py` / `Expected:` 예외 발생 시 에이전트 크래시 없이 경고 출력만 수행(PASS) |

---

## 1. 아키텍처 개요 및 배경
본 문서는 AgentOS 환경 내에서 동작하는 다양한 에이전트(Codex, Claude, Antigravity 등)의 실행 계획과 상태를 외부 대시보드와 동기화하기 위한 통합 관측성(Observability) 아키텍처를 구현하는 과정을 정의합니다. 
기존 레퍼런스를 통해 도출된 각 프레임워크의 장단점과 AgentOS의 단순성(P4 Simplicity) 원칙을 결합하여, 과도한 Pub/Sub 모델 대신 명시적이고 단순한 **백그라운드 알림(Notifier) & 어댑터 직접 호출** 방식을 채택합니다.

## 2. 데이터 플로우 (Data Flow) 및 오류 복구 (Error Recovery)
1. **상태 변경**: 에이전트가 SSOT 문서를 수정.
2. **트리거**: AgentOS Gate 검증 후 `DashboardNotifier`를 호출하여 상태 변경을 알림.
3. **비동기 전송**: `DashboardNotifier`가 활성화된 어댑터를 비동기 백그라운드 태스크(fire-and-forget)로 직접 호출.
4. **플러그인 동기화**: 어댑터가 대상 API(GitHub/Linear 등)를 호출.
5. **오류 복구**: API 호출 실패(토큰 만료, 통신 에러 등) 시 메인 프로세스는 절대 중단되지 않으며, 비동기 스레드 내에서 예외를 캐치하여 CLI와 `agentos.log`에 `[Observability Warning]` 형태의 경고만 남깁니다.

---

## Task 및 구현 세부 단계 (Implementation Steps)

### Task 1: 비동기 Notifier 뼈대 구축
- [x] Step 1.1: `agentos/observability/notifier.py` 파일 생성 및 `DashboardNotifier` 클래스 구현 (단순한 리스트 기반 어댑터 관리 및 fire-and-forget 비동기 실행).
- [x] Step 1.2: 알림 전송을 위한 기본 데이터 구조(상태 변경 내역) 정의.
- **검증**: `Run:` `uv run pytest tests/test_notifier.py` / `Expected:` 알림 발송 및 Mock 어댑터 수신 성공.

### Task 2: OS 상태 변경 및 런타임 라이프사이클 훅 연동
- [x] Step 2.1: `agentos/terminal/hooks.py` 내 파일 I/O 변경점 감지부뿐만 아니라, **CLI 런타임 생명주기(강제 종료, `/goal` 모드 타임아웃, 예외 발생)**에도 훅을 걸어 `DashboardNotifier.notify()`를 호출하도록 로직 삽입.
- [x] Step 2.2: 환경 변수(`OBSERVABILITY_ENABLED=1`)에 따른 알림 기능 활성화 토글 추가.
- **검증**: `Run:` `OBSERVABILITY_ENABLED=1 agentos run --json test-task` / `Expected:` 강제 종료(SIGINT) 모사 시에도 백그라운드 예외 알림(Notify) 로그 출력 확인.

### Task 3: 대시보드 플러그인 어댑터 구현 및 토큰 가이드 작성
- [x] Step 3.1: 공통 `DashboardAdapter` 인터페이스 작성.
- [x] Step 3.2: `agentos/observability/adapters/github.py` 생성 및 `GITHUB_TOKEN` 기반 API 통신 로직 구현.
- [x] Step 3.3: 문서화 - 사용자 가이드(`docs/observability-setup.md`) 작성 (사용자 대상 토큰 획득 및 설정법 명시).
- **검증**: `Run:` `uv run pytest tests/test_adapters.py` / `Expected:` Mock 서버 대상 100% PASS.

### Task 4: 사용자 에러 복구 및 예외 처리 강화
- [x] Step 4.1: 어댑터 내 API 타임아웃, 401(인증 실패), 500 오류 시 예외를 흡수(Absorb)하고 메인 루프로 전파 차단.
- [x] Step 4.2: 콘솔에 `[Observability Warning] API 전송 실패: (원인)` 포맷의 안내 로그 추가.
- **검증**: `Run:` `uv run pytest tests/test_notifier_error_recovery.py` / `Expected:` 네트워크 차단 환경 모사 시 크래시 없이 경고 텍스트 반환 확인(PASS).

---

## 리뷰 반영 이력
- 2026-07-27 (Gate 2 1차 피드백 반영 완료): `plan-reviewer`, `principle-auditor`, `usability-reviewer` 피드백을 100% 수용하여 문서 구조 및 신뢰성/사용성 강화.
- 2026-07-27 (Gate 2 2차 독립 에이전트 리뷰 반영): `principle-auditor`의 P4(단순성) 위배 지적에 따라 불필요한 `EventBus`(Pub/Sub) 모델을 제거하고, 직관적인 `DashboardNotifier` (fire-and-forget) 패턴으로 아키텍처 단순화 및 파일명 변경(`events.py` -> `notifier.py`).

## 구현 결과
- `DashboardNotifier` 비동기 객체와 `GithubDashboardAdapter` 플러그인 완성 (파일 쓰기, CLI 종료, 에러 등에 훅 결합)
- 에러 복구 기능은 Thread-based fire-and-forget을 통해 메인 AgentOS 프로세스 안전성 확보

## 사용 방법
- `export OBSERVABILITY_ENABLED=1` 설정 후 `GITHUB_TOKEN`, `OBSERVABILITY_GITHUB_REPO`, `OBSERVABILITY_GITHUB_PROJECT_ID` 지정
- 자세한 내용은 `docs/observability-setup.md` 참조.

## 아카이브 결정
모든 마일스톤(Task 1~4) 100% 달성 및 회귀 검사 통과. 사용자 요청에 따라 Archive 폴더로 이동 후 PR(Merge) 진행 예정.
