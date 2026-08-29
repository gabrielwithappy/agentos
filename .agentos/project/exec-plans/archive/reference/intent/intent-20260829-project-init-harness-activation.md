# Intent Sheet: project init 하네스 리소스 적용

**날짜:** 2026-08-29  
**요청자 의도 요약:** `agentos project init` 실행 후 프로젝트가 하네스 에이전트와 스킬을 실제 런타임에서 사용할 수 있게 한다.

## 가설

> 프로젝트 초기화가 관리 대상 하네스 리소스를 프로젝트의 `.agents` 표면에 설치하고 런타임이 이를 읽도록 연결하면, 초기화 직후 프로젝트에서도 하네스 에이전트·스킬이 실제로 적용될 것이다.

## Plan Quality Gate

> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"

- [ ] Run: `pytest -q tests/test_project_command.py tests/test_conversation_bootstrap.py` Expected: `모든 테스트 통과 (exit 0)`
- [ ] Run: `python3 -m pytest -q` Expected: `전체 테스트 통과 (exit 0)`
- [ ] Run: `scripts/verify-public-test-suite.sh` Expected: `PASS public-test-suite`

## 범위 제약 (Scope Fence)

- 포함: `agentos/commands/project.py`, 프로젝트 초기화 시 리소스 복사/매니페스트, 세션의 프로젝트 로컬 스킬 선택, 관련 회귀 테스트와 사용자 문서
- 제외: 외부 vendor CLI 설정 병합, AgentOS 전역 설치 위치 변경, 신규 에이전트/스킬 내용 작성, 기존 사용자 `.agents` 파일 삭제

## 기술 스택 제약

- Python 3.11+, Typer, pytest, 기존 atomic write/regular-tree 검증 유틸리티
- 외부 서비스·credential·network 의존성 없음

## Worktree Decision

- 필요 여부: 불필요
- 이유: 이미 기능 브랜치에서 단일 저장소 변경으로 진행하며 병렬 작업이 없다.
- ownership: `bugfix/project-init-applies-harness`

## 우선순위

- 프로덕션 수준의 안정성과 엣지 케이스 처리 우선. 특히 기존 `.agents` 사용자 파일 보존과 재실행 안전성을 유지한다.
