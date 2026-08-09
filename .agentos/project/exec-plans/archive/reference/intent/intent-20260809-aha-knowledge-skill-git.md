# Intent Sheet: AHA·스킬 양방향 장기지식 저장소와 Git 연동

**날짜:** 2026-08-09
**요청자 의도 요약:** `docs/knowledge` 장기지식을 기존 `aha knowledge` 명령과 설치된 지식관리 스킬 양쪽에서 다루고, AgentOS 설치 여부와 무관하게 스킬 자체로 실행하며, 독립 Git 저장소로 백업·다른 프로젝트 재사용이 가능하게 만든다.

## 가설

> 지식 저장·검토·검색의 독립 실행 runtime을 knowledge skill 자체에 포함하고 `aha` 명령은 선택적 adapter로 연결하면, AgentOS가 없는 환경에서도 스킬을 사용할 수 있으며 기존 CLI 사용성과 안전한 백업·프로젝트 간 재사용을 함께 얻을 수 있다.

## Plan Quality Gate

- [ ] Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q`  Expected: 모든 knowledge 관련 테스트 PASS
- [ ] Run: `bash tests/harness/test_aha_knowledge_git_workflow.sh`  Expected: `PASS aha-knowledge-git-workflow`
- [ ] Run: `bash tests/harness/test_aha_knowledge_skill_parity.sh`  Expected: `PASS aha-knowledge-skill-parity`
- [ ] Run: `bash tests/harness/test_aha_knowledge_cross_project.sh`  Expected: `PASS aha-knowledge-cross-project`
- [ ] Run: `python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help`  Expected: AgentOS import 없이 skill standalone 명령 도움말 출력
- [ ] Run: `bash tests/harness/test_aha_knowledge_standalone.sh`  Expected: `PASS aha-knowledge-standalone`
- [ ] Run: `python3 -m agentos.cli knowledge --help`  Expected: `inbox`, `publish`, `search`, `context`, `sync` 명령이 표시됨

## 범위 제약 (Scope Fence)

- 포함: skill 자체의 독립 실행 runtime, 공통 knowledge contract, `aha knowledge` 선택적 adapter, knowledge skill 패키지, skill이 관리하는 Git 지식 저장소, `docs/knowledge` 프로젝트 checkout/연동, 백업·clone/pull 기반 cross-project 흐름, 문서와 테스트
- 제외: 지식 내용 자동 생성, 외부 벡터 DB/검색 서비스, 자동 Git push, 기존 프로젝트 문서의 authority 규칙 변경, 비-knowledge AHA 명령의 리팩터링

## 기술 스택 제약

- skill standalone runtime은 Python 표준 라이브러리와 표준 Git CLI만 사용하며 `agentos`, Typer, Rich 설치에 의존하지 않는다.
- 기존 `agentos` CLI adapter는 설치되어 있을 때만 선택적으로 사용한다.
- 원격 Git 저장소와 credential은 실행 전 preflight로 검증하며 계획 단계에서 새 외부 서비스는 도입하지 않는다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 계획 작성과 리뷰만 수행하며 현재 feature branch를 사용한다.
- ownership: `feature/aha-knowledge-skill-git`

## 우선순위

- 프로덕션 수준의 안정성: 두 진입점의 동작 parity, 백업 실패 복구, 다른 프로젝트 clone/pull 시나리오를 자동 검증한다.
