---
status: 완료
date: 2026-08-23
reviewed: true
usability_review_required: true
user_request: 최신 knowledge-curator 스킬을 AgentOS에 적용하고 존재하지 않는 skill-curator 에이전트 삭제 요청을 정리한다.
active_agent: codex
active_session:
dashboard_item_id:
implementation_started_at: 2026-08-23T01:58:00Z
implementation_completed_at: 2026-08-23T02:03:49Z
implementation_duration: 약 6분
---

# 최신 knowledge-curator 스킬 적용 구현 계획

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 지정된 최신 standalone `knowledge-curator` 스킬을 AgentOS catalog에 반영한다.

**사용자 결과 요약:** 사용자는 AgentOS catalog에서 최신 knowledge checkout 초기화, OKF v0.2 검사, read-only inspect, 안전한 reorganize 흐름을 사용할 수 있으며 기존 `knowledge-curator` 에이전트 안내는 보존된다.

**의존성 분석:** 외부 의존성 없음. 참조 소스는 로컬 경로이며, 스킬 runtime은 Python 표준 라이브러리만 사용한다.

**장기 적용 표면:**
- Traceability Surface: 이 계획, `HISTORY.md`, `.agents/traces/` 리뷰 증거
- Durable Result Surface: `catalog/skills/knowledge-curator/` standalone skill bundle 및 기존 `tests/test_knowledge_curator_evals.py`

**진행 상태:** 최신 소스와 catalog 차이를 확인했으며, 리뷰 후 구현 대기 중이다.

**아키텍처:** 외부 source bundle을 catalog skill root에 동기화한다. 실행 runtime은 catalog 내부의 standalone Python CLI로 유지하며 `.agents` harness agent와 AgentOS managed knowledge runtime은 건드리지 않는다.

**기술 스택:** Markdown, JSON, Python 3 표준 라이브러리, pytest.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 최신 source bundle 동기화 및 검증 완료 |
| 완료됨 | feature branch, intent/plan, Gate 2 증거, catalog 동기화, 회귀 검증 |
| 현재 위치 | 완료 |
| 다음 단계 | 사용자가 PR 또는 병합 방식을 결정 |
| 완료 신호 | parity diff·eval·CLI help·manifest check·knowledge 회귀 테스트 PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 최신 bundle 반영 | catalog skill이 source와 일치하고 OKF 도구를 포함 | `catalog/skills/knowledge-curator/**` | `diff -ruN ...` → 출력 없음 |
| 2. 회귀 및 무결성 검증 | 기존 eval contract와 harness integrity 유지 | `tests/test_knowledge_curator_evals.py`, `.agents/**` | pytest, CLI help, manifest check → PASS |

## 리뷰 반영 이력
- 2026-08-23: `skill-curator`라는 이름의 에이전트는 저장소에 존재하지 않음을 확인했다. 기존 `.agents/agents/harness/knowledge-curator.md`는 범위 밖으로 유지한다.
- Gate 2 self-review는 이 런타임에서 독립 subagent 호출 도구가 제공되지 않아 허용된 fallback으로 수행한다.

## 구현 결과
- `/home/gabriel/agent/prj-agent/development/qm-private/skills-seed/knowledge-curator/`의 최신 `SKILL.md`, CLI, OKF 검사·증거·inspect·reorganize 도구, schema/evidence fixture, inspect tests를 `catalog/skills/knowledge-curator/`에 반영했다.
- source cache와 pytest cache는 복사하지 않았다.
- 저장소에 `skill-curator`라는 에이전트는 없었으므로 `.agents/agents/harness/knowledge-curator.md`는 삭제하지 않고 유지했다.
- AgentOS managed knowledge runtime과 remote sync 동작은 변경하지 않았다.

검증 결과:
- source/catalog parity: PASS
- `tests/test_knowledge_skill.py tests/test_knowledge_git_security.py tests/test_knowledge_curator_evals.py`: 17 passed
- copied inspect suite: 8 passed
- standalone CLI help: PASS
- harness manifest integrity: PASS

## 사용 방법
```bash
python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help
```

## 아카이브 결정
사용자 검토와 PR/병합 결정 전까지 active에 유지한다. 구현과 자동 검증은 완료되었지만 브랜치 통합은 사용자 승인 범위 밖이다.
