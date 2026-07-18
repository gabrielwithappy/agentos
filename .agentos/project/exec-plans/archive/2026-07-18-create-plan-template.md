# 계획 문서 템플릿 생성 및 리뷰 강제화 구현 계획

> **상태:** 완료
> **작성일:** 2026-07-18<br>
> reviewed: true<br>
> implementation_started_at: 2026-07-18T09:06:00+09:00<br>
> implementation_completed_at: 2026-07-18T09:07:00+09:00<br>
> implementation_duration: 1m<br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 새로운 실행 계획 문서를 작성할 때 반드시 포함되어야 할 필수 항목(의존성 분석, 장기 적용 표면, 검증 명령어 등)과 에이전트의 리뷰(Gate 2)가 누락 없이 강제되도록 표준 템플릿(`TEMPLATE.md`)을 신설하고 하네스 규칙을 보완한다.

**사용자 결과 요약:** 앞으로 생성되는 모든 에이전트 계획 문서는 일관된 포맷을 가지게 되며, `plan-reviewer` 및 `principle-auditor` 등의 공식 리뷰 증거 파일이 분리되어 저장되지 않으면 문서를 완료(실행)할 수 없는 명확한 제어가 보장된다.

**의존성 분석:**
- 외부 의존성: 없음 (로컬 마크다운 파일 생성 및 지침 수정 작업)

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 `.agents/traces/` 내부의 리뷰 증거 기록
- Durable Result Surface: `.agentos/project/exec-plans/TEMPLATE.md` 템플릿 파일 및 수정된 `AGENTS.md` 지침

**진행 상태:** 계획 문서 생성 완료, 리뷰 및 승인 대기 중

**아키텍처:** 
- `.agentos/project/exec-plans/TEMPLATE.md` 생성: 필수 메타데이터, 사용자 결과, 검증, 생명주기 마감 처리가 모두 빈칸 또는 주석으로 포함된 마스터 양식.
- `.agents/AGENTS.md` 수정: `Rule 6`에 "모든 신규 계획은 TEMPLATE.md 기반으로 작성되어야 하며, `.agents/traces/` 내 별도 리뷰 증거가 없으면 `reviewed: true`를 불가한다"는 문구 추가.

**기술 스택:** Markdown

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 계획 초안 작성 |
| 현재 위치 | 계획 검토 대기 |
| 다음 단계 | 계획 승인 후 템플릿 파일 생성 및 지침 업데이트 실행 |
| 완료 신호 | `TEMPLATE.md`가 생성되고, `AGENTS.md`에 강제 리뷰 규칙이 포함됨 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 마스터 템플릿 파일 생성 | 모든 필수 항목이 포함된 `TEMPLATE.md` 생성됨 | `.agentos/project/exec-plans/TEMPLATE.md` | `cat .agentos/project/exec-plans/TEMPLATE.md` / Expected: 템플릿 본문 출력(PASS) |
| 2. AGENTS.md 강제화 규정 추가 | 에이전트 지침에 템플릿 사용과 리뷰 증거 분리 규정이 명문화됨 | `.agents/AGENTS.md` (Protected Path) | `grep -E "TEMPLATE.md|traces" .agents/AGENTS.md` 및 `sync-manifest --check` / Expected: 해당 규정 확인 및 sync PASS |

## 사용자 리뷰 필요 (User Review Required)
- `TEMPLATE.md` 내에 리뷰 증거 파일 위치(`.agents/traces/audit-plan-review.md`)를 강제로 기록하는 필드를 추가할까요, 아니면 단순히 템플릿 주석으로 안내만 할까요?

## 리뷰 반영 이력
- (초안 작성됨)

## 구현 결과
1. `.agentos/project/exec-plans/TEMPLATE.md` 마스터 양식 생성 완료.
2. `AGENTS.md` 파일 Rule 6을 업데이트하여 TEMPLATE 복사 및 `traces` 폴더 내 리뷰 증거 의무 생성 조항 추가 완료.

## 사용 방법
새로운 계획을 작성할 때 `cp .agentos/project/exec-plans/TEMPLATE.md .agentos/project/exec-plans/active/YYYY-MM-DD-plan-name.md` 명령어로 복사하여 시작합니다.

## 완료 증거
- `TEMPLATE.md` 생성됨
- `AGENTS.md` 수정됨

## 아카이브 결정
모든 구현 작업과 검증이 완료되었으므로, 이 계획 문서는 `.agentos/project/exec-plans/archive/` 로 이동하여 아카이브합니다.
