# Intent Sheet: 계획문서 frontmatter metadata 표준화

**날짜:** 2026-09-04
**요청자 의도 요약:** 계획문서의 상태와 핵심 실행 metadata를 문서 상단에서 빠르게 읽을 수 있도록 YAML frontmatter로 표준화하고, 기존 blockquote 계획과의 호환성을 유지한다.

## 가설

> 계획 metadata를 문서 본문과 분리된 frontmatter에 모으면 상태·담당자·리뷰·실행 시점을 빠르게 파악할 수 있고, lifecycle 및 reviewer가 같은 값을 안정적으로 읽을 수 있을 것이다.

## Plan Quality Gate

- [ ] Run: `pytest tests/test_plan_parser.py .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q` Expected: exit 0
- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh` Expected: exit 0 and frontmatter active plan appears in generated board
- [ ] Run: `python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan .agentos/project/exec-plans/active/2026-09-04-plan-frontmatter.md` Expected: valid review evidence
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` Expected: exit 0

## 범위 제약 (Scope Fence)

- 포함: 신규 계획 template의 frontmatter, lifecycle parser, review artifact metadata detection, 기존 legacy blockquote fallback, 관련 contract tests와 문서 사용법
- 제외: 기존 모든 archive 계획 일괄 변환, plan board의 새 상태 저장소, YAML 외부 dependency 도입, reviewer 권한·승인 규칙 변경, `.agents/mission/plan.json` schema 확장

## 기술 스택 제약

- Python 표준 라이브러리 기반의 제한된 YAML-like frontmatter parser
- Markdown, pytest, 기존 lifecycle scripts
- 외부 의존성 없음

## Worktree Decision

- 필요 여부: 불필요
- 이유: 단일 checkout에서 기존 계획·parser·template의 호환성 변경을 순차 검증
- ownership: `feature/lifecycle-status-alignment`

## 우선순위

- 기존 계획 호환성과 사용자 가독성을 우선하고, frontmatter 도입에 필요한 최소 변경만 허용한다.
