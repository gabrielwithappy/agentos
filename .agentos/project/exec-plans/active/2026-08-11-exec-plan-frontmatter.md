---
status: 완료 (구현 및 검증 완료)
date: 2026-08-11
reviewed: true (Gate 2 3종 PASS, 증거: `.agents/traces/reviews/2026-08-11-exec-plan-frontmatter/{plan-reviewer,principle-auditor,usability-reviewer}.md`)
usability_review_required: true
user_request: 현재 프로젝트 계획을 구현할 때 구현문서의 메타데이터가 렌더링이 잘 안되는 경우가 많아 frontmatter로 수정하는 계획문서를 작성한다.
active_agent: Antigravity
active_session: 
dashboard_item_id: 
implementation_started_at: 2026-08-11T00:36:45Z
implementation_completed_at: 2026-08-11T00:39:20Z
implementation_duration: 3 minutes
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
| 진행 요약 | 구현 및 전체 검증 완료 |
| 완료됨 | Milestone 1, 2 전체 구현 및 테스트 완료 |
| 현재 위치 | 프로젝트 메타데이터 파서 전환 완료 |
| 다음 단계 | (없음, 완료됨) |
| 완료 신호 | `uv run pytest` 전체 PASS 확인 및 TEMPLATE 변경 완료 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 파서 업데이트 | Frontmatter 형식 지원 파서 완성 | `agentos/observability/plan_parser.py`, `tests/test_plan_parser.py` | `Run:` `uv run pytest tests/test_plan_parser.py -q` / `Expected:` PASS |
| 2. 템플릿 마이그레이션 | 신규 계획 생성 시 Frontmatter 포맷 사용됨 | `.agentos/project/exec-plans/TEMPLATE.md` | `Run:` `cat .agentos/project/exec-plans/TEMPLATE.md \| head -n 15` / `Expected:` 최상단에 `---` 블록으로 시작 |

## 리뷰 반영 이력
- 2026-08-11: Gate 2 리뷰 (plan-reviewer, principle-auditor, usability-reviewer) 모두 PASS 완료.

## 구현 결과
- `agentos/observability/plan_parser.py` 및 테스트 스위트에 YAML Frontmatter 파서 로직을 추가하여 기존 방식(Blockquote) 및 신규 방식 모두 완벽히 지원하도록 변경했습니다.
- `TEMPLATE.md`에 Frontmatter 구조(`---`)를 적용하였습니다.
- 전체 테스트 스위트가 에러 없이 통과(675 passed)하여 하위 호환성이 검증되었습니다.

## 사용 방법
- 앞으로 신규 구현 계획서를 작성할 때는 `TEMPLATE.md`에 정의된 바와 같이 문서 최상단에 `---` 로 둘러싸인 메타데이터 포맷을 사용합니다.
- `agentos dashboard sync-plan` 커맨드는 기존과 같이 동일하게 사용하면 되며 변경된 Frontmatter 포맷을 자동으로 인식합니다.

## 아카이브 결정
모든 구현과 검증을 성공적으로 완료하였으므로 아카이브(완료) 처리 가능합니다.
