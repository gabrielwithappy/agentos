# Intent Sheet: Register knowledge-curator as a harness skill

**날짜:** 2026-08-23
**요청자 의도 요약:** standalone `knowledge-curator`를 Agent Harness의 harness skill registry에 등록해 AgentOS harness가 직접 사용할 수 있게 한다.

## 가설
> `catalog/skills/knowledge-curator/` bundle을 `.agents/skills/harness/knowledge-curator/`에 등록하고 manifest를 갱신하면, harness skill discovery와 standalone CLI 사용을 모두 지원할 수 있다.

## Plan Quality Gate
- [ ] Run: `test -f .agents/skills/harness/knowledge-curator/SKILL.md && test -f .agents/skills/harness/knowledge-curator/scripts/knowledge.py` Expected: `PASS harness-skill-present`
- [ ] Run: `diff -ru catalog/skills/knowledge-curator .agents/skills/harness/knowledge-curator` Expected: no output
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` Expected: `PASS` integrity
- [ ] Run: `python3 -S .agents/skills/harness/knowledge-curator/scripts/knowledge.py --help` Expected: exit code 0

## 범위 제약
- 포함: harness skill bundle 등록, manifest 갱신, source/catalog parity 검증
- 제외: curator 동작 변경, AgentOS CLI 재등록, `agentos/knowledge` 복원, 외부 서비스 연결

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 feature branch에서 직접 수행하며 기존 변경을 보존한다.

## 우선순위
- 기존 standalone bundle을 그대로 재사용하는 단순 등록
