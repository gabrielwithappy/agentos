# Intent Sheet: 최신 knowledge-curator 스킬 적용

**날짜:** 2026-08-23  
**요청자 의도 요약:** 지정된 `skills-seed/knowledge-curator` 구현을 AgentOS의 `catalog/skills/knowledge-curator/`에 반영한다.

## 가설
> 최신 standalone knowledge-curator 구현과 OKF 검사·재구성 도구를 AgentOS catalog에 반영하면, AgentOS가 최신 장기지식 관리 흐름을 동일하게 제공할 수 있다.

## Plan Quality Gate
- [ ] Run: `diff -ruN --exclude='__pycache__' --exclude='.pytest_cache' /home/gabriel/agent/prj-agent/development/qm-private/skills-seed/knowledge-curator catalog/skills/knowledge-curator`  Expected: 출력 없음
- [ ] Run: `python3 -m pytest tests/test_knowledge_curator_evals.py -q`  Expected: 모든 테스트 PASS
- [ ] Run: `python3 /home/gabriel/agent/prj-agent/development/qm-private/skills-seed/knowledge-curator/scripts/knowledge.py --help`  Expected: exit 0
- [ ] Run: `./.agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`  Expected: `🏆 [PASS] 하네스 무결성 확인 완료.`

## 범위 제약
- 포함: `catalog/skills/knowledge-curator/SKILL.md`, `evals/evals.json`, standalone Python scripts와 OKF fixture/test 자산의 catalog 반영
- 제외: `.agents/agents/harness/knowledge-curator.md` 삭제 또는 변경, AgentOS runtime `agentos/knowledge/**`, 원격 Git 작업, private 경로의 파일 수정

## 기술 스택 제약
- Python 표준 라이브러리 기반 standalone CLI 유지
- 외부 네트워크·credential·third-party dependency 추가 금지

## Worktree Decision
- 필요 여부: 불필요
- 이유: 이미 `feature/apply-knowledge-curator` 작업 브랜치에서 단일 범위로 진행 중
- ownership: `feature/apply-knowledge-curator`

## 우선순위
- 최신 소스의 기능 parity와 기존 catalog 회귀 방지
