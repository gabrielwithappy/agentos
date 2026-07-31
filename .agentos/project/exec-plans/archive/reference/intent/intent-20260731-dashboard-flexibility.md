# Intent Sheet: 대시보드 연동 아키텍처 유연성 확보

**날짜:** 2026-07-31
**요청자 의도 요약:** GitHub Projects에 종속된 현재 대시보드 동기화 구조를 개선하여, 다양한 외부 대시보드(Jira, Linear 등)와 연결 가능한 유연한 플러그인/어댑터 아키텍처를 구축한다.

## 가설
> 하드코딩된 어댑터 생성 로직과 상태 매핑을 설정 기반 레지스트리 패턴으로 분리하면, 기존 코드 수정 없이 새로운 대시보드 어댑터를 추가하고 로컬 상태를 외부 보드 상태에 유연하게 매핑할 수 있을 것이다.

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `python3 -c "from agentos.observability.notifier import notifier; print('Registry exists')"` Expected: `Registry exists`
- [ ] Run: `agentos dashboard sync-plan --help | grep -i config` Expected: CLI 도움말에 설정 기반 동기화에 대한 설명이 포함될 것.
- [ ] Run: `pytest tests/observability/test_dashboard_registry.py -q` Expected: `pass` (레지스트리 및 설정 로드 테스트 통과)

## 범위 제약 (Scope Fence)
- 포함: `agentos/observability/notifier.py`, `agentos/observability/adapters/`, `agentos/commands/dashboard.py`, 설정 로더 모듈.
- 제외: `agentos/observability/plan_parser.py` (마크다운 파싱 로직은 그대로 유지), 프론트엔드/TUI 렌더링.

## 기술 스택 제약
- 순수 Python (설정 파일은 JSON 또는 YAML, 현재 환경에 맞게 `pyproject.toml` 의존성 내에서 해결).
- `Protocol` 기반의 의존성 역전 원칙(DIP) 준수.

## Worktree Decision
- 필요 여부: 불필요
- 이유: 현재 checkout 보존 및 다른 병렬 작업 없음.

## 우선순위
- 프로덕션 수준의 안정성과 확장성 확보 우선 (다양한 어댑터 수용을 위한 인터페이스 확립).
