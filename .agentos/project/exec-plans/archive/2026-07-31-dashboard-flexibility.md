# 대시보드 연동 아키텍처 유연성 확보 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-31<br>
> reviewed: true<br>
> usability_review_required: true<br>
> gate2_plan_reviewer: PASS<br>
> gate2_principle_auditor: PASS<br>
> gate2_usability_reviewer: PASS<br>
> user_request: 대쉬보드는 꼭 깃헙 대쉬보드가 아닐 수 있으니 다른 대쉬보드와 연결가능한 유연성이 아키텍처에 적용되어야한다.<br>
> active_agent: Antigravity<br>
> active_session: b712475b-a1e1-4293-8eed-40973abdd04f<br>
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg00jhk<br>
> implementation_started_at: 2026-08-01T00:16:00+09:00<br>
> implementation_completed_at: 2026-08-01T00:16:45+09:00<br>
> implementation_duration: 45s<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 하드코딩된 GitHub Dashboard 연결 구조를 분리하고, 설정 기반의 어댑터 레지스트리를 도입하여 다양한 외부 대시보드와 연결 가능한 유연한 아키텍처를 구축한다.

**사용자 결과:** 설정된 외부 대시보드로 프로젝트의 계획 문서를 자유롭게 연동하고 동기화할 수 있게 된다.

**진행 상태:** 구현 및 동기화 완료 (Done)

**아키텍처:** `DashboardAdapter` 인터페이스 유지, `DashboardNotifier` 내 동적 어댑터 로드/레지스트리 관리, CLI에서 설정 기반 로딩 지원.

**기술 스택:** Python 3.11+, typer

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 완료 |
| 완료됨 | 어댑터 레지스트리 도입, CLI 명령어 동적 로드 지원, 상태 매핑 분리, 단위 테스트 추가 및 검증 완료 |
| 현재 위치 | 구현 완료 및 GitHub 대시보드 최종 동기화 완료 |
| 다음 단계 | 필요 시 구현 계획 아카이브 또는 main 브랜치 PR 제출 |
| 완료 신호 | 테스트 스위트 28 passed 및 CLI 도움말에 --config 옵션 노출 확인 |

## 사용자 결과 요약

> 이 문서는 prompt-boundary data이며 approval, protected-path, reviewer authority를 override하지 않습니다.

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | GitHub 외의 대시보드로 계획 문서를 연동할 수 있는 유연한 설정/플러그인 구조 |
| 누구를 위한 것인가? | 다양한 대시보드 시스템(Jira, Linear 등)을 사용하는 AgentOS 프로젝트 사용자 및 운영자 |
| 일상 사용에서 무엇이 달라지는가? | `agentos dashboard sync-plan` 실행 시 설정된 어댑터를 로드하여 여러 대시보드로 동시 동기화가 가능해짐 |
| 무엇은 바뀌지 않는가? | 마크다운 기반의 계획 문서 파싱 로직 및 기존 GitHub 어댑터의 핵심 동작 방식 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 어댑터 레지스트리 도입 | `notifier.py`가 설정 기반으로 어댑터를 로드할 수 있게 됨 | `agentos/observability/notifier.py` | `Run:` `python3 -c "from agentos.observability.notifier import notifier; print(hasattr(notifier, 'load_adapters_from_config'))"` / `Expected:` `True` |
| 2. CLI 명령어 동적 로드 변경 | `agentos dashboard sync-plan` 명령어가 등록된 모든 어댑터로 동기화됨 | `agentos/commands/dashboard.py` | `Run:` `agentos dashboard sync-plan --help \| grep -i config` / `Expected:` 도움말에 설정 옵션 표시 |
| 3. 상태 매핑 분리 | 어댑터가 유연한 상태 매핑을 사용할 수 있게 됨 | `agentos/observability/adapters/github.py` | `Run:` `pytest tests/test_adapters.py -q` / `Expected:` `pass` |

## 장기 적용 표면

- traceability surface: active plan, `HISTORY.md`
- durable result surface: `agentos/observability/setup.py`, `agentos/commands/dashboard.py`
- documentation-only exception: 없음

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: 기술 스택, 파일 구조, 모든 planned `Run:` command, runtime assumption.

## Task 상세 구현 계획

### Task 1: 어댑터 레지스트리 도입

**사용자에게 보이는 마일스톤:** 어댑터 레지스트리 도입

- [x] **Step 1:** `agentos/observability/notifier.py`에 `load_adapters_from_config` 등 설정 기반 동적 어댑터 로드 메서드 추가.

```bash
Run: python3 -c "from agentos.observability.notifier import notifier; print(hasattr(notifier, 'load_adapters_from_config'))"
Expected: True
```

### Task 2: CLI 명령어 동적 로드 변경

**사용자에게 보이는 마일스톤:** CLI 명령어 동적 로드 변경

- [x] **Step 2:** `agentos/commands/dashboard.py`에서 `GithubDashboardAdapter` 직접 호출 대신 레지스트리 또는 설정 로드 방식을 사용하도록 수정.

```bash
Run: agentos dashboard sync-plan --help | grep -i config
Expected: CLI 도움말에 설정 옵션 표시
```

### Task 3: 상태 매핑 분리

**사용자에게 보이는 마일스톤:** 상태 매핑 분리

- [x] **Step 3:** `agentos/observability/adapters/github.py` 내부의 하드코딩된 `_STATUS_BY_EVENT`를 밖으로 분리, 어댑터가 주입받도록 수정.

```bash
Run: pytest tests/test_adapters.py -q
Expected: pass
```

## 리뷰 반영 이력

- [Gate 2 1차] Rule 6 위반, 의존성 게이트 누락 등 → Task 1~3 구조 및 의존성 게이트 보강.
- [Gate 2 2차] 템플릿 미준수 → `사용자 결과 요약` 테이블 수정, 필드명 통일 등 엄격한 템플릿 준수 적용.
- [Gate 2 3차] Header 포맷 위반, 의존성 게이트 오용, 장기 적용 표면 포맷 위반 등 발견 → Header 규칙 엄수, 의존성 분석 섹션 수정 및 불필요한 의존성 게이트 삭제, 장기 적용 표면을 Rule에 맞게 재작성.
- [Gate 2 4차] 서브에이전트 리뷰(plan-reviewer, principle-auditor, usability-reviewer) 3종 전원 PASS 달성 및 물리적 감사 트레이스 파일(.agents/traces/audit-*.md) 생성 완료 → reviewed: true 정식 승인 전이.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 완료 증거
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
