# Intent Sheet: 독립 프로젝트용 AgentOS 핵심 운영 스킬

**날짜:** 2026-08-30
**요청자 의도 요약:** `AGENTS.md`에 의존하지 않는 프로젝트에서도 AgentOS의 핵심 신뢰성·안전·검증 운영 원칙을 스킬로 적용할 수 있게 한다.

## 가설

> `AGENTS.md`의 프로젝트 결합 정보와 하네스 내부 전용 규칙을 분리해 독립 실행 가능한 `agentos-core-guidance` 스킬로 제공하고 `agentos project init`의 기본 스킬 집합에 포함하면, 대상 프로젝트에 기존 `AGENTS.md`가 없어도 동일한 핵심 운영 행동을 일관되게 적용할 수 있을 것이다.

## Plan Quality Gate

> 계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?

- [ ] Run: `python3 /home/gabriel/.codex/skills/.system/skill-creator/scripts/quick_validate.py catalog/skills/agentos-core-guidance` Expected: `Skill is valid` 또는 동등한 frontmatter 검증 PASS
- [ ] Run: `python3 -m pytest -q tests/test_project_command.py tests/test_core_guidance_skill.py` Expected: exit 0, 기본 설치·`project init` 반영·스킬 계약 회귀 PASS
- [ ] Run: `bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check && bash scripts/verify-public-test-suite.sh` Expected: 하네스 무결성 PASS 및 `PASS agentos-public-suite`

## 범위 제약 (Scope Fence)

- 포함: `agentos-core-guidance` 스킬 본문/eval, catalog 등록, bundled default skill 목록, `agentos project init` 적용 회귀 테스트, 스킬 사용 문서와 검증 계획
- 제외: 기존 `AGENTS.md` 수정, `.agents/skills/harness/**` 거버넌스 변경, 하네스 엔진·hook 스크립트 변경, target 프로젝트의 AGENTS.md 자동 생성/덮어쓰기, 사용자 설정 hook 실행

## 기술 스택 제약

- Python 3.11+, 기존 catalog skill 형식, Typer/pytest의 기존 project-init 경로
- 외부 서비스·credential·network·plugin 없음

## Worktree Decision

- 필요 여부: 불필요
- 이유: 현재 feature branch에서 기존 변경과 연속된 catalog/default skill 통합을 단일 소유자가 수행한다.
- ownership: `feature/add-skill-creator`

## 우선순위

- 프로덕션 수준의 안전성과 명확한 경계를 우선한다. 스킬은 운영 원칙을 제공하되 target 프로젝트의 고유 요구사항·비밀·하네스 내부 상태를 추측하지 않는다.
