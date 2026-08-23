# Intent Sheet: knowledge-agent remote-only migration

**날짜:** 2026-08-23
**요청자 의도 요약:** 로컬 `docs/knowledge` 문서 데이터를 `https://github.com/gabrielwithappy/knowledge-agent`에 병합하고, 앞으로 지식 관리는 해당 저장소를 단일 원격 저장소로 사용한다.

## 가설
> AgentOS의 `docs/knowledge` 운영 지침을 `knowledge-agent` OKF bundle에 흡수하고 AgentOS 로컬 문서를 pointer-only 안내로 바꾸면, 장기지식 관리 위치가 `knowledge-agent` 하나로 수렴한다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?
- [ ] Run: `git -C /tmp/knowledge-agent fetch origin main && git -C /tmp/knowledge-agent diff --name-status origin/main...HEAD` Expected: only `A concepts/agentos-knowledge-lifecycle.md`, `M concepts/index.md`, and `M log.md`
- [ ] Run: `python3 .agentos/worktrees/feature-knowledge-agent-remote-only/catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent` Expected: JSON with `"ok": true`
- [ ] Run: `git -C /tmp/knowledge-agent fetch origin main && BEFORE=$(git -C /tmp/knowledge-agent rev-parse origin/main) && AFTER=$(git -C /tmp/knowledge-agent rev-parse HEAD) && test "$BEFORE" != "$AFTER" && git -C /tmp/knowledge-agent push origin main && git -C /tmp/knowledge-agent fetch origin main && test "$(git -C /tmp/knowledge-agent rev-parse HEAD)" = "$(git -C /tmp/knowledge-agent rev-parse origin/main)"` Expected: exit 0
- [ ] Run: `rg -q "https://github.com/gabrielwithappy/knowledge-agent" docs/knowledge/README.md && rg -q "pointer-only" docs/knowledge/README.md && rg -q "Do not add new knowledge notes here" docs/knowledge/README.md && rg -q "git clone git@github.com:gabrielwithappy/knowledge-agent.git" docs/knowledge/README.md && rg -q "knowledge-agent" docs/knowledge/index.md && rg -q "knowledge-agent" .agentos/project/00-project-index.md` Expected: exit 0
- [ ] Run: `git status --short --branch` Expected: only allowed AgentOS files changed

## 범위 제약
- 포함: `/tmp/knowledge-agent/concepts/agentos-knowledge-lifecycle.md`, `/tmp/knowledge-agent/concepts/index.md`, `/tmp/knowledge-agent/log.md`, AgentOS `docs/knowledge/README.md`, `docs/knowledge/index.md`, `.agentos/project/00-project-index.md`, this plan, intent sheet, lifecycle board, `HISTORY.md`
- 제외: AgentOS runtime code, `agentos/knowledge/**`, `agentos/commands/knowledge.py`, tests deletion, `catalog/skills/knowledge-curator/**`, force push, history rewrite, credential storage, existing `knowledge-agent` file deletion

## 기술 스택 제약
- `knowledge-agent` push uses SSH: `git@github.com:gabrielwithappy/knowledge-agent.git`
- HTTPS remote is not used because this environment cannot prompt for GitHub credentials.

## Worktree Decision
- 필요 여부: 필요
- 이유: main checkout has unrelated runtime-removal changes; migration is isolated in a clean worktree.
- ownership: `.agentos/worktrees/feature-knowledge-agent-remote-only`, branch `feature/knowledge-agent-remote-only`

## 우선순위
- Preserve existing remote knowledge first; add only the migration note and pointer docs needed for the user's requested single-remote flow.
