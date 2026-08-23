# Intent Sheet: Remove embedded AgentOS knowledge runtime

**날짜:** 2026-08-23
**요청자 의도 요약:** standalone `knowledge-curator` 스킬을 단일 knowledge 운영 surface로 사용하기 위해 AgentOS에 내장된 중복 `agentos/knowledge` runtime을 제거한다.

## 가설
> 내장 knowledge runtime과 `agentos knowledge` CLI를 제거하고 standalone 큐레이터 스킬을 보존하면, knowledge 관리 구현이 하나로 수렴하고 OKF 기반 큐레이터 흐름과 충돌하지 않는다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `test ! -d agentos/knowledge && ! test -e agentos/commands/knowledge.py && rg -n 'agentos\\.knowledge|commands\\.knowledge|knowledge\\.app' agentos tests || true` Expected: `agentos/knowledge` 및 legacy import/register 참조 없음
- [ ] Run: `uv run pytest tests/test_cli.py tests/test_cli_contract.py tests/test_knowledge_skill.py tests/test_knowledge_curator_evals.py -q` Expected: exit code 0
- [ ] Run: `uv run agentos --help` Expected: 성공하고 `knowledge` 명령이 목록에 없음
- [ ] Run: `git diff --check` Expected: exit code 0

## 범위 제약 (Scope Fence)
- 포함: `agentos/knowledge/`, legacy `agentos knowledge` command 등록 및 구현, 해당 runtime 전용 테스트와 legacy CLI 문서 참조
- 제외: `catalog/skills/knowledge-curator/`, OKF schema/tooling, `docs/knowledge` standalone skill 문서, conversation/LLM/TUI runtime

## 기술 스택 제약
- Python 3.11+, Typer, pytest, uv
- 외부 서비스·네트워크·credential 없음

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout이 이미 관련 feature branch이며 변경은 이 checkout의 명시된 범위 안에 있다.
- ownership: `feature/knowledge-agent-migration`

## 우선순위
- 기존 AgentOS CLI 회귀 없이 중복 runtime 제거
