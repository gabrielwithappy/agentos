# 계획 전 결정 게이트 사용자 surface 구현 계획

> **상태:** 구현 계획 (리뷰 대기)<br>
> **작성일:** 2026-09-01<br>
> reviewed: false<br>
> user_request: 결정 질문·재개·성공 신호를 사용자 문서와 project traceability에 반영한다.<br>
> active_agent: Codex<br>
> active_session: pre-plan-user-surface-r1<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

**목표:** 사용자가 질문에 답하는 방법, 재개 방식, 완료 신호와 durable result 위치를 이해하도록 문서화한다.

**사용자 결과:** 사용자는 내부 구현 선택이 아니라 결정 내용에 답하고, 결과 문서에서 다음 행동과 완료 기준을 찾을 수 있다.

**진행 상태:** 초안 / flow integration 계획 완료 후 리뷰 대기

**아키텍처:** 동작 계약은 앞선 두 계획에서 소유한다. 이 계획은 getting-started와 project root 문서의 설명·추적성만 갱신하고 실행 로직을 추가하지 않는다.

**기술 스택:** Markdown, 문서 계약 테스트, lifecycle/manifest scripts

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 선행 계획 의존 / 리뷰 대기 |
| 완료됨 | 없음 |
| 현재 위치 | 문서 범위와 acceptance 고정 |
| 다음 단계 | flow integration PASS 후 문서 수정·검증 |
| 완료 신호 | 문서 계약 테스트, lifecycle, manifest PASS |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | 질문 형식·재개·성공 신호를 설명하는 일관된 안내. |
| 누구를 위한 것인가? | 계획 요청자, 운영자, 후속 구현자. |
| 일상 사용에서 무엇이 달라지는가? | 어디에 답하고 어디서 결과를 확인할지 바로 알 수 있다. |
| 무엇은 바뀌지 않는가? | 실행 계약과 질문 판정 로직은 이 계획에서 바꾸지 않는다. |

## 장기 적용 표면

- traceability surface: 이 active plan, 선행 두 계획, `HISTORY.md`, lifecycle board, Gate 2 traces
- durable result surface: `docs/getting-started.md`, `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/05-agent-operating-contract.md`, `.agentos/project/06-decisions-change-log.md`
- documentation-only exception: 문서 변경 계획이므로 위 문서가 durable result다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 안내 문서 | 질문·답변·재개 흐름을 한 번에 이해 | `docs/getting-started.md` | docs contract test |
| project traceability | 요구사항·운영 계약·결정 기록이 같은 용어를 사용 | `.agentos/project/*.md` | cross-reference grep + lifecycle |

## 파일 구조

- 수정: `docs/getting-started.md`
- 수정: `.agentos/project/00-project-index.md`, `02-product-scope-and-requirements.md`, `05-agent-operating-contract.md`, `06-decisions-change-log.md`
- 생성: `tests/test_pre_plan_user_surface.py`
- 제외: `.agents/agents/**`, `.agents/skills/**`, 실행 로직과 manifest source

## 의존성 분석

- 외부 의존성: 없음
- 선행 조건: triage 및 flow integration 계획의 contract/acceptance가 PASS.
- protected path: `.agentos/project/**`의 정책성 변경은 project SSOT와 Gate 2 범위로 검토한다. `.agents/**`는 이 계획에서 수정하지 않는다.

## Task 1: 사용자 안내

- [ ] **Step 1.1: 질문·재개·성공 신호를 사용자 언어로 기록한다.**
  - Run: `grep -n 'material ambiguity\|재개\|계획을 작성할 준비가 되었습니다\|확인된 목표' docs/getting-started.md`
  - Expected: exit 0; 사용자가 입력할 내용, 입력하지 않을 내용, invalid recovery, 완료 신호가 설명된다.

## Task 2: project traceability

- [ ] **Step 2.1: 네 root 문서의 상호 참조를 검증한다.**
  - Run: `grep -rn 'pre-plan\|결정 게이트\|material ambiguity' .agentos/project/00-project-index.md .agentos/project/02-product-scope-and-requirements.md .agentos/project/05-agent-operating-contract.md .agentos/project/06-decisions-change-log.md`
  - Expected: exit 0; 각 문서는 자신의 SSOT 역할과 triage/flow 문서의 참조 위치를 설명한다.

## Task 3: 문서·lifecycle closeout

- [ ] **Step 3.1: 문서 테스트와 board/manifest 상태를 확인한다.**
  - Run: `.venv/bin/pytest -q tests/test_pre_plan_user_surface.py -k 'docs or user_message' && python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
  - Expected: docs tests, lifecycle refresh, manifest check 모두 exit 0; 이 계획은 active에 남는다.

## 아카이브 결정

사용자의 명시적 archive 요청 전까지 active 유지.
