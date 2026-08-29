# Intent Sheet: knowledge-curator project layout

**날짜:** 2026-08-25  
**요청자 의도 요약:** `knowledge-agent` 저장소의 `knowledge-curator` 스킬이 장기 지식을 저장·관리하는 canonical 위치로 `docs/knowledge`를 정확히 안내하도록 수정한다.

## 가설
> 스킬의 저장소 루트, OKF bundle, 실행 근거 경계를 `knowledge-agent`의 실제 구조와 일치시키면, 후속 에이전트가 장기 지식을 `docs/knowledge`에 남기고 `skills/*/runs/`의 중간 산출물과 혼동하지 않게 된다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 검증으로 통과하는가?
- [ ] Run: `python3 ./.agents/skills/harness/skill-creator/scripts/quick_validate.py knowledge-agent/skills/knowledge-curator` Expected: `Skill is valid`
- [ ] Run: `python3 -S knowledge-agent/skills/knowledge-curator/scripts/knowledge.py validate --project knowledge-agent/docs/knowledge` Expected: JSON에 `"ok": true` 및 exit 0
- [ ] Run: `rg -n "docs/knowledge|skills/.*runs|repository root|starter|backup|validate|status" knowledge-agent/skills/knowledge-curator/SKILL.md` Expected: 저장 위치·근거 분리·기존 bundle 운영·검증/백업 흐름이 모두 검색됨

## 범위 제약
- 포함: `docs/knowledge-agent/skills/knowledge-curator/SKILL.md`, 이 실행 계획과 Intent Sheet
- 제외: `knowledge-agent` CLI 구현, `docs/knowledge` 콘텐츠, `catalog/skills/knowledge-curator/SKILL.md`, 원격 sync/push, AgentOS runtime 및 harness asset

## 기술 스택 제약
- Markdown skill instructions, Python 3 standalone knowledge CLI, OKF v0.2

## Worktree Decision
- 필요 여부: 불필요
- 이유: 이미 전용 feature branch에서 작업하며, 기존 변경은 그대로 보존한다.
- ownership: `feature/knowledge-curator-docs-knowledge`

## 우선순위
- 기존 프로젝트 구조와 안전 경계를 보존하는 최소 문서 수정
