---
status: 리뷰 대기
date: 2026-08-23
reviewed: true
usability_review_required: true
user_request: standalone knowledge-curator를 단일 운영 surface로 사용하기 위해 agentos/knowledge를 삭제한다.
active_agent: codex
active_session:
dashboard_item_id:
implementation_started_at:
implementation_completed_at:
implementation_duration:
---

# AgentOS 내장 knowledge runtime 제거 구현 계획

**목표:** standalone `knowledge-curator` 스킬과 중복되는 AgentOS 내장 knowledge runtime을 제거하고 CLI를 일관되게 유지한다.

**사용자 결과 요약:**
- 사용자는 `catalog/skills/knowledge-curator/`의 standalone OKF 큐레이터만 knowledge 관리에 사용한다.
- `agentos` CLI에는 더 이상 동작하지 않는 legacy `knowledge` 명령이 노출되지 않는다.
- conversation, LLM, TUI, session 기능은 바뀌지 않는다.

## 의존성 분석

- 외부 의존성: 없음
- 스캔 기준: CLI import/register, legacy runtime 전용 테스트, standalone curator tests

## 장기 적용 표면

- Traceability Surface: 이 계획, Intent Sheet, `HISTORY.md`
- Durable Result Surface: `catalog/skills/knowledge-curator/`는 유지되고 AgentOS package에서 legacy runtime이 제거됨

**진행 상태:** Gate 2 리뷰 완료, 구현 실행 가능

**아키텍처:** AgentOS package의 embedded knowledge adapter를 제거하고 standalone curator skill을 유일한 knowledge implementation으로 남긴다.

**기술 스택:** Python, Typer, pytest, uv

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 삭제 범위와 회귀 경계를 고정함 |
| 완료됨 | 관련 참조 및 중복 구현 조사 |
| 현재 위치 | Gate 2 리뷰 대기 |
| 다음 단계 | 리뷰 증거 생성 후 legacy runtime과 CLI surface 제거 |
| 완료 신호 | legacy path/import/command 없음, CLI·curator 회귀 테스트 PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. Embedded runtime 제거 | AgentOS package에 legacy knowledge 구현이 없음 | `agentos/knowledge/**`, `agentos/commands/knowledge.py`, `agentos/cli.py` | path/reference scan PASS |
| 2. CLI·standalone curator 회귀 확인 | AgentOS CLI가 정상 실행되고 curator skill은 계속 동작 | `tests/**`, `catalog/skills/knowledge-curator/**` | focused pytest, `uv run agentos --help` PASS |

## File Structure

- 삭제: `agentos/knowledge/**` - 중복 embedded knowledge runtime
- 삭제: `agentos/commands/knowledge.py` - legacy CLI command implementation
- 수정: `agentos/cli.py` - legacy command import/registration 제거
- 삭제: `tests/test_knowledge_store.py`, `tests/test_knowledge_cli.py` - 제거 대상 runtime 전용 테스트
- 유지: `catalog/skills/knowledge-curator/**` - standalone curator 단일 구현
- 유지: `tests/test_knowledge_skill.py`, `tests/test_knowledge_curator_evals.py` - standalone curator 회귀 테스트

## Task 0: Gate 2 리뷰

**파일:** `.agents/traces/audit-plan-review-remove-agentos-knowledge-runtime.md`, `.agents/traces/audit-principle-remove-agentos-knowledge-runtime.md`, `.agents/traces/audit-usability-remove-agentos-knowledge-runtime.md`

- [x] **Step 1:** 계획의 범위, 파일 소유권, 보존 surface, rollback 가능성을 검토한다.

Run: `test -f .agents/traces/audit-plan-review-remove-agentos-knowledge-runtime.md && test -f .agents/traces/audit-principle-remove-agentos-knowledge-runtime.md && test -f .agents/traces/audit-usability-remove-agentos-knowledge-runtime.md`
Expected: `PASS review-artifacts-present`

## Task 1: Embedded runtime과 CLI surface 제거

**파일:**
- 삭제: `agentos/knowledge/**`, `agentos/commands/knowledge.py`
- 수정: `agentos/cli.py`

- [ ] **Step 1:** legacy package, command implementation, CLI import/register를 제거한다.

Run: `test ! -d agentos/knowledge && test ! -e agentos/commands/knowledge.py && ! rg -n 'from agentos.commands import .*knowledge|knowledge\\.app|agentos\\.knowledge' agentos`
Expected: `PASS embedded-knowledge-removed`

## Task 2: Legacy 전용 테스트와 사용자 문서 참조 정리

**파일:**
- 삭제: `tests/test_knowledge_store.py`, `tests/test_knowledge_cli.py`
- 수정: `docs/knowledge/README.md`, `docs/knowledge/index.md`

- [x] **Step 1:** 제거된 `agentos knowledge` 명령 안내를 standalone curator 명령 안내로 대체하고 전용 legacy 테스트를 삭제한다.

Run: `! rg -n 'agentos knowledge' docs/knowledge tests && rg -n 'catalog/skills/knowledge-curator|knowledge\.py' docs/knowledge`
Expected: `PASS legacy-knowledge-docs-removed`

## Task 3: 회귀 검증

- [ ] **Step 1:** AgentOS CLI 및 standalone curator 회귀 테스트를 실행한다.

Run: `uv run pytest tests/test_cli.py tests/test_cli_contract.py tests/test_knowledge_skill.py tests/test_knowledge_curator_evals.py -q`
Expected: exit code 0

- [ ] **Step 2:** CLI help와 전체 참조 경계를 확인한다.

Run: `uv run agentos --help && ! uv run agentos --help 2>&1 | rg -n '^\\s*knowledge\\s' && git diff --check`
Expected: CLI help 성공, `knowledge` command 없음, diff whitespace clean

## 리뷰 반영 이력

- 계획 리뷰 artifact가 생성되면 Gate 2 결과를 기록한다.

## 구현 결과

(구현 후 작성)

## 사용 방법

Knowledge 작업은 `catalog/skills/knowledge-curator/SKILL.md`와 standalone `scripts/knowledge.py`를 사용한다.

## 아카이브 결정

사용자 검토 및 PR/병합 결정 전까지 active에 유지한다.
