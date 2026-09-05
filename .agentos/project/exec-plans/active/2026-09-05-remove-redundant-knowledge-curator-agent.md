---
status: 완료
date: 2026-09-05
reviewed: true
usability_review_required: false
user_request: "knowledge-curator 에이전트 제거 및 스킬로 일원화 (옵션 A)"
active_agent: antigravity
active_session: 5fa9bd2b-76e8-4d7a-ab2b-db1530676b28
dashboard_item_id:
implementation_started_at: 2026-09-05T03:45:00Z
implementation_completed_at: 2026-09-05T03:46:30Z
implementation_duration: 1m 30s
next_action: archive plan
---

# redundant knowledge-curator 에이전트 제거 및 스킬 일원화 구현 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

> **상태 문구 관용구:** 구현과 자동 검증(테스트 스위트 등)은 모두 끝났지만 사람의 수동 확인(예: 실제 브라우저 로그인, 외부 서비스 UI 조회)만 남은 경우, `status:` 문구에 정확히 `"(사용자 실사용 확인 대기)"`를 포함시킨다. 이 문구는 `agentos dashboard sync-plan`이 보드 Status를 `In Progress`가 아니라 `Awaiting Verification`으로 정확히 분류하는 데 쓰인다(`agentos/observability/plan_parser.py`의 `status_to_board_status()` 참고).

**목표:** 
- 지식 관리 기능에 대해 불일치 레거시 프롬프트와 중복성을 가진 `.agents/agents/harness/knowledge-curator.md` 에이전트를 제거하고, `knowledge-curator` 스킬로 일원화하여 P4 단순성을 달성한다.

**사용자 결과 요약:** 
- 불필요한 하네스 에이전트가 정리되어 코어 하네스 에이전트 목록이 명확해지며, 지식 큐레이션 및 관리 작업은 독립 실행형 스킬(`knowledge-curator`)을 통해 일관되게 수행됩니다.

**의존성 분석:**
- 외부 의존성(API, 토큰, 환경 등): 없음

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `.agents/agents/harness/knowledge-curator.md` 삭제, `.agents/agents/README.md`, `config/public-boundary.json`

**진행 상태:** 구현 및 전체 검증 완료

**아키텍처:** 
- AgentOS 하네스 코어 에이전트 목록 정리
- `knowledge-curator` 스킬 단독 지원 구조 확립

**기술 스택:** 
- AgentOS 하네스 에이전트 및 스킬 카탈로그
- Bash, Python, Git

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 구현 완료 |
| 완료됨 | 에이전트 삭제, README.md 갱신, public-boundary.json 갱신, 회귀 테스트 통과 |
| 현재 위치 | 커밋 및 푸시 |
| 다음 단계 | 아카이브 |
| 완료 신호 | Gate 2 PASS, 전체 테스트 27/27 PASS, test_knowledge_skill 10/10 PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 에이전트 삭제 및 참조 정리 | 중복 에이전트 삭제 및 인덱스/경계 설정 동기화 | `.agents/agents/harness/knowledge-curator.md`, `.agents/agents/README.md`, `config/public-boundary.json` | `Run:` `git status && ./scripts/verify-public-test-suite.sh` / `Expected:` `PASS=27 FAIL=0` 및 린트/경계 검증 통과 |
| 2. 회귀 검증 및 히스토리 기록 | 하네스 전체 계약 테스트 통과 및 영속 기록 | `HISTORY.md` | `Run:` `pytest tests/test_knowledge_skill.py` / `Expected:` `passed` |

## 리뷰 반영 이력
- `plan-reviewer` Gate 2 Triage PASS (`gate2-327c8d36c7280ad9b3faddd5a9e48f9dc6b8cb4b6e1652c4a2f7a66352d85210`)
- `principle-auditor` P1-P4 원칙 감사 PASS (P4 단순성 증대, Complexity Delta: DECREASE)
- `plan-reviewer` 최종 심사(final adjudication) non-blocking PASS

## 사전 실행 Gate와 closeout 경계

Gate 2 artifact는 구현 Task가 아니라 이 lifecycle section에서 확인한다. 기능 Task 안에 reviewer artifact 생성·self-signing·approval·closeout 기록을 넣지 않는다. `plan-reviewer`와 `principle-auditor`의 독립 PASS를 먼저 확인하고, `usability_review_required: true`인 계획에는 `usability-reviewer` PASS도 확인한다.
※ 주의 (Bootstrap Safety): 하네스/체커/리뷰어 자체를 변경하는 계획일 경우, Task 0(사전 게이트)에 아직 구현되지 않은 미래의 스키마나 필드를 assertion 조건으로 포함하지 마라. (현재 환경의 유효성만 검증하고, 새 스키마/기능 검증은 반드시 구현 후 Task에서 수행할 것)

## 구현 결과
- `.agents/agents/harness/knowledge-curator.md` 파일 삭제 완료.
- `.agents/agents/README.md` 내 `Harness Core Agents` 목록에서 `knowledge-curator` 제거 완료.
- `config/public-boundary.json`에서 `.agents/agents/harness/knowledge-curator.md` 경로 제거 완료.
- `bash ./scripts/verify-public-test-suite.sh` 통과 (`PASS agentos-public-suite`).
- `bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh` 통과 (`PASS=27 FAIL=0`).
- `pytest tests/test_knowledge_skill.py` 통과 (`10 passed in 3.91s`).

## 사용 방법
- 지식 관리(OKF 초기화, 검사, 검증, 백업, 동기화 등)는 `.agents/skills/harness/knowledge-curator/` 스킬 및 내장 스크립트(`scripts/knowledge.py`)를 통해 직접 수행합니다.

## 아카이브 결정
- 중복 에이전트 파일 삭제 및 참조 정리가 완료되었고 모든 회귀 테스트를 통과하였으므로 정상 아카이브 대상입니다.
