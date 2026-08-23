# Intent Sheet: knowledge-agent remote migration

**날짜:** 2026-08-23
**요청자 의도 요약:** 로컬 `docs/knowledge` 데이터를 `https://github.com/gabrielwithappy/knowledge-agent`에 병합하고, 앞으로 지식 관리는 해당 저장소를 단일 원격으로 사용한다.

## 가설
> `docs/knowledge`의 현재 운영 문서와 인덱스 정보를 `knowledge-agent` 저장소에 흡수하고 AgentOS 문서가 새 canonical 저장소를 가리키면, 장기 지식의 관리 위치가 하나로 수렴한다.

## Plan Quality Gate
> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?
- [ ] Run: `git -C /tmp/knowledge-agent status --short --branch` Expected: `## main...origin/main` and no dirty paths
- [ ] Run: `git -C /tmp/knowledge-agent ls-remote --heads origin main` Expected: `refs/heads/main` is reachable
- [ ] Run: `python3 catalog/skills/knowledge-curator/scripts/knowledge.py validate --project /tmp/knowledge-agent` Expected: JSON with `"ok": true`
- [ ] Run: `rg -n "knowledge-agent|docs/knowledge" docs .agentos/project/00-project-index.md` Expected: AgentOS docs point to `knowledge-agent` as canonical knowledge repository
- [ ] Run: `git status --short --branch` Expected: AgentOS branch contains only planned migration documentation/pointer changes

## 범위 제약
- 포함: `/tmp/knowledge-agent` repository content, AgentOS `docs/knowledge` pointer docs, `.agentos/project/00-project-index.md`, execution-plan trace files, `HISTORY.md`
- 제외: AgentOS runtime code, `catalog/skills/knowledge-curator` behavior changes, force push, history rewrite, credential storage, unreviewed deletion of unrelated knowledge files

## 기술 스택 제약
- Git over SSH is available for `git@github.com:gabrielwithappy/knowledge-agent.git`.
- HTTPS access requires credentials and is not used for push.

## Worktree Decision
- 필요 여부: 불필요
- 이유: AgentOS 변경은 feature branch에서 수행하고, target knowledge repository는 `/tmp/knowledge-agent` 임시 checkout으로 분리한다.
- ownership: AgentOS branch `feature/knowledge-agent-migration`, knowledge repo `/tmp/knowledge-agent` main

## 우선순위
- 프로덕션 수준의 안전성 우선: 기존 원격 지식 저장소 내용을 보존하면서 로컬 `docs/knowledge` 정보를 병합한다.
