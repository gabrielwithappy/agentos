# Intent Sheet: 공통 AgentOS 하네스 base 구조

**날짜:** 2026-08-29  
**요청자 의도 요약:** 사용자별 profile/override는 현재 단계에서 만들지 않고, 모든 사용자가 동일한 하네스 agent와 핵심 하네스 skill 구조를 사용하도록 한다.

## 가설

> AgentOS가 package-owned 하네스 base 리소스와 manifest를 단일 기준으로 사용하고 setup/project init이 같은 base를 반영하면, 설치 위치나 실행 프로젝트가 달라도 하네스 agent·핵심 skill 구조와 버전이 일관되게 유지될 것이다.

## Plan Quality Gate

> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"

- [ ] Run: `./.venv/bin/python -m pytest -q tests/test_setup_bootstrap.py tests/test_project_command.py tests/test_conversation_bootstrap.py`  Expected: exit 0, 하네스 base 설치·project init·로컬 bootstrap 회귀 테스트 전체 통과
- [ ] Run: `bash scripts/verify-public-test-suite.sh && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`  Expected: `PASS agentos-public-suite` 및 하네스 무결성 `PASS`
- [ ] Run: `./.venv/bin/python -m build --wheel --outdir <tmpdir>`  Expected: wheel 생성 성공 및 package-owned harness agent/core skill base 리소스 포함
- [ ] Run: `./.venv/bin/python -m pytest -q tests/test_common_base_resources.py`  Expected: 설치형/소스형 경로가 동일한 manifest와 동일한 하네스 agent/core skill 목록을 반환

## 범위 제약 (Scope Fence)

- 포함: 하네스 agent와 `.agents/skills/harness` 핵심 skill source, manifest/digest, `setup`, `project init/status`, 하네스 resource discovery, 회귀 테스트, 사용자 문서
- 제외: 사용자별 profile 명령·설정 overlay, provider/auth 설정, 사용자별 enable/disable 정책, 서버 PATH·패키지 배포 자동화, vendor별 실제 agent runtime

## 기술 스택 제약

- Python 3.11+, Typer, pathlib/shutil, importlib.resources, JSON manifest, pytest
- 기존 atomic filesystem/symlink 안전성 경계를 유지한다.

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 checkout의 기존 project-init 작업과 동일한 연속 범위이며 parallel ownership이 없다.
- ownership: `bugfix/project-init-applies-harness`

## 우선순위

- 완전한 구현: 공통 base 일관성과 설치형 검증을 우선하며 profile 기능은 명시적으로 deferred한다.
