# Intent Sheet: 하네스 스킬 계층과 전체 catalog 통합

**날짜:** 2026-08-30
**요청자 의도 요약:** `agentos-core-guidance`를 하네스 핵심 스킬로 이동하고, 하네스 스킬과 선택형 스킬을 하나의 catalog에서 계층적으로 관리한다.

## 가설

> 하네스 루트에 cascade routing용 `SKILL.md`를 두고 하위 스킬을 명시적으로 연결하며, catalog가 각 하위 스킬의 canonical path와 분류를 함께 관리하면, AgentOS는 핵심·선택형 스킬을 중복 없이 발견·설치·project init·검증할 수 있을 것이다.

## Plan Quality Gate

- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check` Expected: 하네스 manifest 무결성 PASS
- [ ] Run: `python3 -m pytest -q tests/test_harness_skill_catalog.py tests/test_project_command.py tests/test_common_base_resources.py` Expected: exit 0, 관련 회귀 테스트 전체 PASS
- [ ] Run: `bash scripts/verify-public-test-suite.sh` Expected: `PASS agentos-public-suite`

## 범위 제약

- 포함: `.agents/skills/harness/agentos-core-guidance/` 이동, `.agents/skills/harness/SKILL.md` cascade guide, harness skill catalog metadata, project-init/package/read routing 회귀 검증
- 제외: harness skill 본문 전면 재작성, 새 skill runtime/recursive executor, 자동 skill 삭제·정리 daemon, AGENTS.md 수정, vendor CLI/provider 변경, 외부 서비스

## 기술 스택 제약

- 기존 Markdown `SKILL.md`, JSON catalog, Python/Typer, pytest, 기존 harness manifest/package resource 경로
- protected harness path 변경은 `harness-architect` 승인과 manifest sync 후에만 수행

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 feature branch의 하네스·catalog 구조를 단일 소유자가 연속 변경한다.
- ownership: `feature/add-skill-creator`

## 우선순위

- canonical path 일관성, project init 복구 가능성, 중복·순환 없는 routing을 최우선으로 한다.
