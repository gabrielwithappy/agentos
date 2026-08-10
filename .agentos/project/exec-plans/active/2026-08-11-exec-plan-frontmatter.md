---
status: 구현 계획 (리뷰 대기)
date: 2026-08-11
reviewed: true (Gate 2 3종 PASS, 증거: `.agents/traces/reviews/2026-08-11-exec-plan-frontmatter/{plan-reviewer,principle-auditor,usability-reviewer}.md`)
usability_review_required: true
user_request: 현재 프로젝트 계획을 구현할 때 구현문서의 메타데이터가 렌더링이 잘 안되는 경우가 많아 frontmatter로 수정하는 계획문서를 작성한다.
active_agent: Antigravity
active_session: 
dashboard_item_id: 
implementation_started_at: 
implementation_completed_at: 
implementation_duration: 
---

# [Frontmatter 전환] 구현 계획 문서 메타데이터 포맷 변경

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- 기존 인용구(`>`) 형식의 메타데이터를 YAML Frontmatter(`---`) 형식으로 변경하여, Markdown 렌더러 호환성과 파싱 안전성을 높인다.
- 기존 파서(`agentos/observability/plan_parser.py`)를 업데이트하여 Frontmatter 형식을 완벽하게 처리할 수 있게 한다.

**사용자 결과 요약:** 
- 마크다운 뷰어 및 IDE(VS Code 등) 환경에서 구현 계획 문서의 메타데이터 렌더링이 깨지지 않고 깔끔하게 표출된다.
- 대시보드 동기화(`sync-plan`) 커맨드가 정상 작동한다.

**의존성 분석:**
- 파싱에는 외부 라이브러리(PyYAML 등)를 추가하지 않고, `re` 모듈 및 단순 파싱 함수를 이용하여 의존성 추가를 피한다.
- 하위 호환성 유지: 기존 인용구 포맷 문서들도 문제 없이 파싱되게 유지하거나, 하위 호환성을 유지하기 어려우면 기존 `active` 및 `TEMPLATE.md` 를 일괄 업데이트하여 깨지지 않도록 한다.

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md`, 이 계획 문서
- Durable Result Surface: 
  - `.agentos/project/exec-plans/TEMPLATE.md`
  - `agentos/observability/plan_parser.py`
  - `tests/test_plan_parser.py`

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:** 
- `agentos/observability/plan_parser.py` 내의 메타데이터 추출 로직(`_find_meta_line`, `_find_meta_field`)을 정규식 기반 인용구(`>`) 파싱에서 YAML Frontmatter 파싱과 병행/대체 하도록 변경한다.
- YAML Frontmatter의 파싱은 문서 최상단의 `---` 와 `---` 사이의 텍스트 블록을 추출한 뒤 각 `key: value`를 정규식이나 문자열 split으로 파싱하는 방식으로 구성한다.

**기술 스택:** 
- Python 3.11+
- Markdown

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 리뷰 대기 |
| 완료됨 | 계획 초안 작성 |
| 현재 위치 | 리뷰 통과, 계획 승인 대기 |
| 다음 단계 | 리뷰 통과 후 구현 실행 |
| 완료 신호 | `uv run pytest tests/test_plan_parser.py`가 PASS하고, 대시보드 동기화가 정상 작동함 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 파서 업데이트 | Frontmatter 형식 지원 파서 완성 | `agentos/observability/plan_parser.py`, `tests/test_plan_parser.py` | `Run:` `uv run pytest tests/test_plan_parser.py -q` / `Expected:` PASS |
| 2. 템플릿 마이그레이션 | 신규 계획 생성 시 Frontmatter 포맷 사용됨 | `.agentos/project/exec-plans/TEMPLATE.md` | `Run:` `cat .agentos/project/exec-plans/TEMPLATE.md \| head -n 15` / `Expected:` 최상단에 `---` 블록으로 시작 |

## 리뷰 반영 이력
- 2026-08-11: Gate 2 리뷰 (plan-reviewer, principle-auditor, usability-reviewer) 모두 PASS 완료.

## 구현 결과
(구현 후 작성)

## 사용 방법
(구현 후 작성)

## 아카이브 결정
(모든 구현과 검증, 하네스 리뷰 완료 후 아카이브 결정 사유 기록)
