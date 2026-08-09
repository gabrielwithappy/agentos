# 프로젝트 문서 구조 리팩토링 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-18<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-18T08:50:00+09:00<br>
> implementation_completed_at: 2026-07-18T09:02:00+09:00<br>
> implementation_duration: 12m<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 프로젝트 관리 문서의 구조를 최적화하여 혼란스러운 `agentos-plans` 경로를 교정하고, 요구사항 범위를 벗어나는 시각적 의도를 분리하며, 결정 로그(decision log) 파일 구조를 리팩토링한다. 요구사항(REQ-001)의 인수 조건 최신화 및 추적성(RTM) 원칙을 보완하고, 추가로 Antigravity 에이전트를 위한 시작 훅(Hook)을 구성한다.

**사용자 결과 요약:** DDL 에이전트 및 Designer 에이전트가 올바른 `.agentos/project` 디렉터리를 참조하게 되며, ADR 문서가 개별화되어 결정 사항의 장기 보존 및 추적이 용이해진다. 또한 인수 조건(Acceptance)과 추적성(Traceability)의 역할이 명확히 구분되어 프로젝트 산출물의 검증 기준이 바로잡힌다.

**의존성 분석:**
- 외부 의존성: 없음 (전체 작업이 로컬 마크다운 파일 구조 변경 및 로컬 훅 변경에 국한됨)

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 이 계획 문서의 완료 증거
- Durable Result Surface: `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/06-decisions-change-log.md`, `reference/decisions/*.md`, `.agents/AGENTS.md` 파일들

**진행 상태:** 진행 요약, 완료됨, 현재 위치, 다음 단계, 완료 신호를 간단히 보여줌

**아키텍처:** 
- `designer-agent`와 `document-delivery-lead`의 입력 경로 교정 (`agentos-plans/docs/project` -> `.agentos/project`)
- `02-product-scope-and-requirements.md` 내 요구사항(REQ-001)의 인수 조건을 최신 Python CLI 기준으로 변경 및 Acceptance와 Traceability의 목적 구분 명확화.
- `02-product-scope-and-requirements.md` 내 시각적 의도 섹션 제거.
- `06-decisions-progress-change-log.md`를 `06-decisions-change-log.md`로 이름 변경 후 `progress` 섹션 분리.
- 기존 결정 사항을 `reference/decisions/` 내 개별 파일(ADR 0001, 0002)로 추출하여 인덱싱.
- Antigravity(Gemini) 컨텍스트 강제를 위한 시작 훅 파일 `.agents/AGENTS.md` 신규 생성.

**기술 스택:** Markdown

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 계획 초안 작성 |
| 현재 위치 | 리뷰 통과, 계획 승인 대기 |
| 다음 단계 | 구현(이미 반영된 코드의 승인 확인) 실행 |
| 완료 신호 | 모든 참조 문서 경로가 정상으로 변경되고, ADR 문서가 분리된 상태로 존재함 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 에이전트 경로 교정 | DDL 및 Designer 에이전트가 정상 경로를 탐색함 | `catalog/agents/...` | `grep -r ".agentos/project" catalog/agents/` / Expected: 경로 변경 내역 출력(PASS) |
| 2. PRD 최적화 | 요구사항 문서에 비-요구사항 항목 제거됨 | `02-product-scope-and-requirements.md` | `cat .agentos/project/02-product-scope-and-requirements.md | grep "시각적 의도"` / Expected: 출력 없음(PASS) |
| 3. 결정 로그 리팩토링 | `06-decisions-change-log.md`로 변경됨 | `06-decisions-change-log.md` | `ls .agentos/project/06-decisions-change-log.md` / Expected: 파일 존재(PASS) |
| 4. ADR 문서 개별 생성 | 개별 결정 문서(0001, 0002) 열람 가능 | `reference/decisions/...` | `ls .agentos/project/reference/decisions/` / Expected: 0001, 0002 파일 출력(PASS) |
| 5. Antigravity 훅 구성 (Protected Path 거버넌스) | 에이전트가 새 대화 시 규칙을 인지함 | `.agents/AGENTS.md` | `cat .agents/AGENTS.md` (authorized architect 확인 포함) 및 `sync-manifest --check` / Expected: 파일 내용 확인 및 sync PASS |
| 6. 요구사항/추적성 지침 | RTM 분리 기준이 명확해짐 | `02-product-scope-and-requirements.md` | `grep "Traceability" .agentos/project/02-product-scope-and-requirements.md` / Expected: 지침 업데이트 확인(PASS) |

## 리뷰 반영 이력
- 즉시 구현 및 사용자(PO) 승인에 따른 사후 계획 문서 작성.
- [2026-07-18] plan-reviewer 및 principle-auditor 검증 결과 반영 (검증 명령어 추가, 의존성 분석 선언, 장기 적용 표면 추가, Protected Path 거버넌스 보강)

## 구현 결과
모든 파일 참조 경로가 `.agentos/project`로 통일되었으며, `06` 문서의 progress 부분이 삭제되고 ADR 문서 체계가 도입되었습니다. 

## 사용 방법
결정 로그를 확인할 때는 `06-decisions-change-log.md`를 참조하고 세부 내용은 `reference/decisions/`의 개별 ADR 파일을 참고합니다.

## 완료 증거
- `catalog/agents/...` 내 경로 업데이트 적용 완료.
- `02-product-scope-and-requirements.md` 요구사항 재정렬 완료.
- `06-decisions-change-log.md` 개명 및 구조 개선 완료.
- `reference/decisions/0001-agentos-harness-python-cli.md` 및 `0002` 생성 완료.
- `.agents/AGENTS.md` 훅 생성 완료 및 `sync-manifest --update` 동기화 확인.

## 아카이브 결정
모든 구현 작업과 검증, 그리고 하네스 리뷰(Gate 2)가 성공적으로 완료되었으므로, 이 계획 문서는 즉시 `.agentos/project/exec-plans/archive/` 디렉터리로 이동되어 보존됩니다.
