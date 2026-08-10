# AHA·스킬 양방향 장기지식 저장소 및 Git 연동 구현 계획

> **상태:** 완료
> **작성일:** 2026-08-09
> reviewed: true
> **usability_review_required:** true
> user_request: `aha knowledge`와 knowledge skill 양쪽에서 장기지식을 저장·검토하고, AgentOS가 설치되지 않은 환경에서도 skill 자체로 실행하며, 문서 폴더를 Git으로 백업하고 다른 프로젝트에서 연동할 수 있게 한다.
> active_agent: codex
> active_session: 2026-08-09-aha-knowledge-skill-git
> dashboard_item_id:
> implementation_started_at: "2026-08-10T01:17:50+09:00"
> implementation_completed_at: 2026-08-10T01:35:00Z
> implementation_duration: 17m

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** OKF v0.2 frontmatter 계약을 준수하는 지식 문서를 AgentOS 설치 없이도 knowledge skill 자체에서 저장·검토하고, `aha knowledge`는 선택적으로 같은 contract에 연결하며, Git으로 백업·동기화·다른 프로젝트에서 재사용할 수 있게 한다.

**사용자 결과:** 사용자는 AgentOS 설치 여부와 관계없이 skill runtime 또는 `aha knowledge` 중 가능한 진입점을 선택해 지식을 작성·검토·publish하고, GitHub 저장소에서 상대 링크로 연결된 지식 graph를 탐색하며, 다른 프로젝트에 clone/pull해 같은 knowledge surface를 재사용한다.

**진행 상태:** Gate 2 독립 리뷰 완료, Task 0 실행 대기 중

**아키텍처:** Markdown 문서와 frontmatter 계약은 OKF v0.2의 portable Markdown/YAML·path identity·cross-link 원칙을 따른다. 지식 GitHub repository와 GitHub web UI를 canonical 저장·기본 뷰어로 삼고, 문서 간 관계는 저장소 내부 상대 Markdown 링크로 표현한다. tag는 사용자의 활용 목적을 나타내는 `action/<value>`와 지식 분류를 나타내는 `domain/<value>`, `context/<value>`를 기본 namespace로 사용하고 `task/<value>`는 선택적으로 추가한다. `status`는 OKF lifecycle(`draft|stable|deprecated`)이고, `action`은 `학습`, `참고`, `개발` 같은 사용자 행동 tag이며, `source`는 OKF `sources` provenance, `target`은 `type`·`resource`·본문 링크로 표현한다. `catalog/skills/knowledge-curator/scripts/knowledge_core.py`가 유일한 portable core이며, standalone script·`agentos knowledge`·AHA bridge는 JSON line output/exit-code contract를 그 core에 위임하는 thin adapter다. 프로젝트의 `docs/knowledge`는 managed checkout surface로 유지하며, inbox 문서는 publish 전까지 instruction authority가 아니다.

**기술 스택:** Python 3.11 표준 라이브러리, OKF v0.2 Markdown/YAML frontmatter, `subprocess` 기반 Git CLI, 독립 skill package, 선택적 AgentOS skill catalog/manifest, pytest와 Bash harness tests

OKF lifecycle·metadata 계약은 다음과 같이 고정한다: `type`은 필수, `status`는 `draft|stable|deprecated`, 설명은 `description`, 출처는 `sources` 목록이다. 기존 `category`와 프로젝트 운영용 메타데이터는 extension field로 보존하며, 기존 `published`, `summary`, 단일 문자열 `source`/`citation` 계약은 새 문서에서 사용하지 않는다.

Tag 계약: `knowledge/` 공통 접두사는 사용하지 않으며, 기본 namespace는 `action/<value>`, `domain/<value>`, `context/<value>`, 선택 namespace는 `task/<value>`다. `action`은 사용자가 지식을 활용하려는 행동(`학습`, `참고`, `개발`)을 표현하고, 문서 lifecycle은 별도의 OKF `status`와 명령으로 관리한다. `source`는 OKF `sources`, `target`은 `type`·`resource`·본문 링크로 표현한다.

### 분류·lifecycle 필드 요약

| 구분 | 필드/namespace | 필수 여부 | 의미 | 예시 |
|---|---|---:|---|---|
| 활용 목적 | `action/<value>` tag | 권장 | 사용자가 이 지식을 활용하려는 행동 | `action/학습`, `action/참고`, `action/개발` |
| 지식 분류 | `domain/<value>` tag | 권장 | 지식이 속한 주제·업무 영역 | `domain/knowledge-management` |
| 사용 맥락 | `context/<value>` tag | 권장 | 적용 환경·상황 | `context/agent`, `context/obsidian` |
| 작업 단위 | `task/<value>` tag | 선택 | 특정 작업이나 산출물과의 연결 | `task/frontmatter` |
| 문서 lifecycle | `status` frontmatter | 선택, 기본 `stable` | 검토·사용 가능 상태 | `draft`, `stable`, `deprecated` |
| concept 종류 | `type` frontmatter | 필수 | OKF concept의 종류 | `Playbook`, `Reference`, `Metric` |
| 출처 provenance | `sources` frontmatter | 출처가 있을 때 | 지식이 유래한 자료 목록 | `sources[].resource: docs/source.md` |
| 대상 resource | `resource` frontmatter | 대상이 있을 때 | 설명 대상의 URI 또는 bundle-relative path | `resource: /datasets/orders.md` |

`action`은 lifecycle 명령이 아니며 사용자 의도 기반 분류다. `status`는 문서 lifecycle이고, `sources`는 출처 구조다. 세 역할을 서로 대체하거나 하나의 tag namespace로 합치지 않는다.

## OKF frontmatter 계약

OKF는 지식 문서의 저장·교환 형식이며 검색 엔진, 인덱서, CLI 명령 또는 검색 알고리즘을 포함하지 않는다. 이 계획도 검색 runtime이나 검색 결과 정렬을 구현하지 않는다.

### 표준 문서 예시

```yaml
---
type: Playbook
title: Example knowledge
description: One-sentence summary of this concept.
status: draft
tags:
  - action/학습
  - domain/knowledge-management
  - context/agent
  - task/frontmatter
sources:
  - id: source-doc
    resource: docs/source.md
    title: Source document
generated:
  by: human:owner
  at: 2026-08-10T12:00:00Z
verified:
  - by: human:owner
    at: 2026-08-10T12:30:00Z
category: topics
---
```

### 필드 계약

| 필드 | 계약 | 비고 |
|---|---|---|
| `type` | 필수 문자열 | concept 종류. 예: `Playbook`, `Reference`, `Metric` |
| `title` | 권장 문자열 | 사람이 읽는 제목 |
| `description` | 권장 문자열 | 한 문장 요약. index와 미리보기에 사용 가능 |
| `status` | 선택 문자열 | `draft`, `stable`, `deprecated`; 생략 시 `stable` |
| `tags` | 선택 문자열 배열 | `domain/...`, `context/...`, 선택적 `task/...` |
| `sources` | 출처가 있으면 구조화된 배열 | 각 항목은 `resource` 필수, `id`/`title` 선택 |
| `generated` | 생성 provenance가 있으면 사용 | `by`, `at` 필요 |
| `verified` | 검증 provenance가 있으면 사용 | `{by, at}` 항목 목록 |
| `resource` | 대상 리소스가 있을 때 선택 | canonical URI 또는 bundle-relative path |
| `category` | AgentOS extension | `references`, `topics`, `decisions` 분류용 |

### Migration 규칙

- `summary`는 `description`으로 변환한다.
- `published`는 `stable`로 변환한다.
- 단일 문자열 `source`와 `citation`은 `sources[].resource` 및 필요 시 `sources[].id`/`title`로 변환한다.
- 기존 문서는 자동 덮어쓰지 않고 explicit migration 대상으로 보고한다.
- OKF가 정의하지 않은 extension field는 consumer가 보존한다.

## 검색 범위 제외

- 검색 명령, 검색 인덱스, ranking, vector search, cache, citation bundle은 이 계획에서 구현하지 않는다.
- OKF 문서는 frontmatter, 본문, 상대 Markdown 링크, `index.md`/`log.md`를 제공하는 저장·교환 표면으로만 다룬다.
- 검색 기능은 별도 후속 계획에서 독립적으로 정의한다.

## OKF 지식 번들 검증

생성된 지식 구조를 검사하는 기능의 공식 명칭은 **OKF Knowledge Bundle Validation(OKF 지식 번들 검증)**으로 한다. 이는 OKF의 핵심 구조를 확인하지만 검색 기능은 포함하지 않는다.

- `OKF Conformance`: parseable frontmatter, 필수 `type`, 예약 파일(`index.md`, `log.md`) 구조
- `OKF Metadata`: `description`, `sources`, `generated`, `verified`, `status`, `stale_after`
- `OKF Structure`: concept Markdown 파일, bundle 디렉터리와 progressive-disclosure `index.md`
- `OKF Links`: bundle-relative 또는 relative Markdown cross-link 형식
- `AgentOS Knowledge Policy`: orphan, index 등록, 조직 tag 규칙 같은 프로젝트 추가 정책. OKF conformance와 별도 결과로 보고한다.

실행 순서는 `지식 생성 → OKF 지식 번들 검증 → 검토 → publish`이며, 검증기는 각 지식 생성자가 별도로 작성하지 않고 knowledge skill이 제공한다. OKF 명세가 강제하지 않는 orphan·index 등록·링크 품질은 AgentOS policy check로만 처리한다.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 구현 계획 / 실행 대기 |
| 완료됨 | 기존 `agentos knowledge` store·CLI·문서·테스트 조사, Intent Sheet 작성, OKF 및 GitHub viewer/lint 요구사항 조사, plan-reviewer·principle-auditor·usability-reviewer Gate 2 PASS |
| 현재 위치 | 구현 시작 전 Task 0 preflight 대기 |
| 다음 단계 | authorization·local Git·AHA host availability를 확인한 뒤 standalone core와 adapter를 구현 |
| 완료 신호 | OKF metadata/lifecycle test, knowledge test, AHA/skill parity, Git workflow, cross-project 검증이 모두 PASS |

## 세션 중단 대비 체크포인트

| 항목 | 현재 값 |
|---|---|
| 현재 완료 범위 | OKF 계약과 Git/skill 요구사항을 조사했고 Gate 2 1차 FAIL 항목을 계획에 반영 중이다. |
| 미완료 작업 | canonical core·AHA bridge·Git 안전 계약을 구현하고 focused/public 검증을 실행한다. |
| 다음 세션 첫 작업 | Task 0의 authorization, local Git, AHA host preflight를 실행해 가능한 진입점을 확인한다. |
| 아직 안 한 검증 | focused knowledge suite, security sentinel suite, local-bare cross-project suite, public-boundary verifier, Gate 2 재리뷰. |
| 관련 HISTORY checkpoint | 2026-08-09 AHA knowledge plan Gate 2 review evidence를 closeout 시 `plan=` 경로와 함께 기록한다. |

## 사용자 결과 요약

| 질문 | 답변 |
|---|---|
| 사용자가 무엇을 얻게 되는가? | `aha knowledge`와 설치된 knowledge skill에서 같은 지식 저장소를 관리하고, Git backup/clone/pull로 재사용한다. |
| 누구를 위한 것인가? | AgentOS 사용자, 에이전트, 프로젝트 간 장기지식을 재사용하는 운영자 |
| 일상 사용에서 무엇이 달라지는가? | 지식 초안을 inbox에 넣은 뒤 CLI 또는 skill flow로 검토·publish하고, 필요할 때 `sync`로 Git 상태를 확인한다. |
| 무엇은 바뀌지 않는가? | OKF frontmatter와 category/tag extension 외의 root project docs 권한, 자동 publish·자동 push, 외부 벡터 검색은 범위 밖이다. GitHub를 대체하는 별도 기본 뷰어도 만들지 않는다. |

## 지식 tag 및 링크 계약

문서의 작업·정보 분류는 Obsidian과 standalone/AgentOS runtime이 함께 읽을 수 있는 평면 tag 배열로 기록한다.

```yaml
tags:
  - action/학습
  - domain/knowledge-management
  - context/obsidian
  - task/frontmatter
```

| namespace | 필수 여부 | 표현하는 정보 | 예시 |
|---|---:|---|---|
| `action/<value>` | 권장 | 사용자가 지식을 활용하려는 행동 | `action/학습`, `action/참고`, `action/개발` |
| `domain/<value>` | 권장 | 지식의 주제·업무 영역 | `domain/knowledge-management` |
| `context/<value>` | 권장 | 적용 환경·상황 | `context/agent`, `context/obsidian` |
| `task/<value>` | 선택 | 특정 작업·산출물 연결 | `task/frontmatter` |

`status`는 tag가 아니라 OKF lifecycle frontmatter이며, `source`도 tag가 아니라 `sources` frontmatter다. `action`은 lifecycle 명령이 아니라 사용자 활용 목적이다.

- 표준 namespace는 `action`, `domain`, `context`이며 `task`는 선택적이다.
- 각 tag의 `/` 뒤 값은 평문 leaf value이며 `#` 접두사와 `knowledge/` 공통 접두사는 쓰지 않는다.
- `action`은 사용자의 활용 목적을 나타내는 tag이며 `action/학습`, `action/참고`, `action/개발`처럼 기록한다.
- `source`는 tag가 아니라 OKF `sources` provenance 목록으로 관리한다.
- `target`은 `type`, `resource`, 본문 링크로 표현하며 별도 tag namespace로 강제하지 않는다.
- 현재 parser는 nested tag를 문자열로 보존하므로 부모 tag 자동 생성·자동 상속은 범위에 넣지 않는다.
- 출처 근거는 OKF `sources` 목록으로 기록하고, 본문 관계는 상대 Markdown 링크로 표현한다.
- skill 문서에는 namespace별 tag 예시와 기존 tag 재사용 규칙만 명시한다.
- OKF 참고 원칙은 `type` 필드, concept별 Markdown 파일, Markdown cross-link, `index.md` progressive disclosure, `log.md` 변경 이력으로 적용한다. 고정 taxonomy 전체를 OKF 표준으로 주장하지 않고 프로젝트 tag namespace로 둔다.
- OKF 지식 번들 검증은 OKF 구조·metadata·링크를 검사하고, AgentOS policy check는 orphan·index 등록·프로젝트 tag 규칙을 별도 검사한다.
- 문서 링크는 GitHub web UI와 clone된 로컬 checkout 양쪽에서 해석 가능한 상대 경로만 canonical 관계 표현으로 인정한다. 외부 URL은 `sources[].resource` provenance 용도로만 허용한다.
- GitHub 기본 뷰어에서 링크를 따라 progressive disclosure할 수 있도록 root 및 각 지식 디렉터리의 `index.md`를 navigation surface로 유지하고, concept 문서에는 관련 concept로 향하는 링크를 본문에 둔다.

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 독립 skill runtime | AgentOS 없이 skill 명령이 실행되고 문서 lifecycle을 처리함 | `catalog/skills/knowledge-curator/SKILL.md`, `catalog/skills/knowledge-curator/scripts/` | `bash tests/harness/test_aha_knowledge_standalone.sh` / Expected: `PASS aha-knowledge-standalone` |
| 2. 공통 저장 계약 | AHA와 skill이 같은 OKF 문서·lifecycle 결과를 반환 | standalone runtime, `agentos/knowledge/`, `agentos/commands/knowledge.py` | `python3 -m pytest tests/test_knowledge_okf.py tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q` / Expected: PASS |
| 3. Git 지식 저장소 | 지식 repository를 init/status/backup/sync할 수 있음 | standalone runtime, 선택적 AgentOS adapter | `bash tests/harness/test_aha_knowledge_git_workflow.sh` / Expected: `PASS aha-knowledge-git-workflow` |
| 4. 다른 프로젝트 연동 | 별도 프로젝트에서 clone/pull한 OKF knowledge checkout을 열고 검토함 | `docs/knowledge/README.md`, integration test fixture | `bash tests/harness/test_aha_knowledge_cross_project.sh` / Expected: `PASS aha-knowledge-cross-project` |

## 장기 적용 표면

- traceability surface: 이 active plan, Intent Sheet, OKF 조사 trace, `HISTORY.md`, `.agentos/project/exec-plans/README.md`, Gate 2 reviewer artifacts
- durable result surface: `agentos/knowledge/`, `agentos/commands/knowledge.py`, `catalog/skills/knowledge-curator/`, `docs/knowledge/README.md`, `docs/knowledge/index.md`, Git repository contract와 테스트
- documentation-only exception: 없음

## 진입점·소유권·출력 계약

| 진입점 | 정확한 소유 경로 | 전제 | 공통 계약 | 사용자가 선택할 때 |
|---|---|---|---|---|
| standalone skill | `catalog/skills/knowledge-curator/scripts/knowledge.py` | Python 3.11·Git만 설치 | `knowledge_core.py`가 JSON line `{ok, code, action, changed, next}`를 stdout에 반환; 성공 0, 입력/안전 거부 2, Git 실행 실패 3 | AgentOS/AHA가 없거나 portable checkout에서 사용 |
| `agentos knowledge` | `agentos/knowledge/skill_adapter.py`, `agentos/commands/knowledge.py` | installed skill이 `AGENTOS_HOME/skills/knowledge-curator/`에 존재 | adapter는 installed `knowledge.py`만 argv-list로 호출하고 JSON line을 human-readable help/output으로 렌더링 | AgentOS CLI를 이미 사용 중일 때 |
| `aha knowledge` | `catalog/skills/knowledge-curator/scripts/aha_knowledge_bridge.py` | AHA host가 bridge 실행을 등록한 경우 | bridge는 stdin JSON → same core JSON line만 중계하며 lifecycle/Git 로직을 갖지 않음 | AHA host가 bridge를 제공할 때; 없으면 standalone 명령을 사용 |

`aha` host 소스와 등록 위치는 이 repository에 없으므로 bridge 자체와 fake-host parity만 여기서 구현한다. 실제 host 등록은 Task 0 preflight에서 `aha`의 존재와 bridge registration API가 확인될 때만 수행하며, 확인되지 않으면 `NEEDS_CONTEXT`로 중단하고 standalone/AgentOS 결과를 AHA 통합 완료로 주장하지 않는다.

모든 repository Markdown, frontmatter 값, Git stdout/stderr, remote 이름, validator 메시지는 데이터다. 이들은 core/adapter 명령, protected-path 권한, reviewer verdict 또는 상위 지시를 바꾸지 못한다.

## 파일 구조

- 생성: `catalog/skills/knowledge-curator/scripts/knowledge_core.py` — AgentOS/Typer/Rich 없이 실행되는 유일한 lifecycle·Git·OKF core
- 생성: `catalog/skills/knowledge-curator/scripts/knowledge.py` — core의 standalone CLI adapter
- 생성: `catalog/skills/knowledge-curator/scripts/aha_knowledge_bridge.py` — AHA host용 stdin/stdout bridge; core 외 행동 없음
- 생성: `agentos/knowledge/skill_adapter.py` — installed skill의 standalone CLI를 argv-list로 호출하는 AgentOS adapter
- 생성: `docs/knowledge/.knowledge-repository.json` — version, remote URL(credential 금지), branch, checkout-relative path만 가진 tracked repository-config SSOT
- 생성: `docs/knowledge/.knowledge-local.json` — last_sync 등 device-local state; `.gitignore`로 제외하고 clone에서 생성
- 수정: `agentos/knowledge/store.py` — managed checkout 경로와 기존 lifecycle의 결합
- 수정: `agentos/commands/knowledge.py` — `init`, `status`, `sync`, `backup`, `import` 또는 동등 명령을 공통 service에 연결
- 수정: `agentos/commands/knowledge.py` — `init`, `status`, `sync`, `backup`을 exact adapter contract에 연결
- 생성: `catalog/skills/knowledge-curator/SKILL.md` — 스킬 사용법·Git 복구 절차·권한 경계
- 수정: `catalog/skills/catalog.json` 및 필요한 catalog manifest — skill 설치/발견 등록
- 생성: `tests/test_knowledge_skill.py` — skill 계약과 CLI parity 검증
- 생성: `tests/test_knowledge_git_security.py` — argv-only Git allowlist, filtered environment, redaction, dirty/conflict, path/symlink, prompt-data 경계 검증
- 생성: `tests/test_knowledge_okf.py` — `type`, `draft|stable|deprecated`, `description`, `sources` 및 extension 보존 검증
- 생성: `tests/harness/test_aha_knowledge_standalone.sh` — AgentOS 미설치 환경의 직접 실행 계약
- 생성: `tests/harness/test_aha_knowledge_git_workflow.sh` — local Git backup/restore 계약
- 생성: `tests/harness/test_aha_knowledge_skill_parity.sh` — AHA와 skill 명령 결과 parity
- 생성: `tests/harness/test_aha_knowledge_cross_project.sh` — 두 임시 프로젝트의 clone/pull 재사용 검증
- 생성: `catalog/skills/knowledge-curator/scripts/okf_bundle_validate.py` — OKF conformance, metadata, structure, relative link 점검
- 생성: `catalog/skills/knowledge-curator/scripts/knowledge_policy_check.py` — AgentOS orphan/index/tag 추가 정책 점검
- 생성: `tests/test_okf_bundle_validation.py` — OKF 정상·frontmatter·reserved file·relative link 회귀 검증
- 생성: `tests/test_knowledge_policy.py` — AgentOS orphan/index/tag 정책 회귀 검증
- 생성: `tests/harness/test_aha_knowledge_okf_validation.sh` — OKF 지식 번들 검증 계약
- 참조: `.agents/traces/research/2026-08-09-aha-knowledge-skill-git-okf.md` — OKF·GitHub viewer·lint 설계 근거
- 수정: `docs/knowledge/README.md`, `docs/knowledge/index.md` — canonical repository, checkout, backup/sync 사용법
- 수정: `.agentos/project/00-project-index.md`, `.agentos/project/02-product-scope-and-requirements.md`, `.agentos/project/03-system-contract.md`, `.agentos/project/04-safety-risk-verification.md`, `.agentos/project/06-decisions-change-log.md` — SSOT traceability와 Git/skill 권한 경계
- 수정: `.agents/agents/harness/knowledge-curator.md` — protected 운영 지침을 실제 두 진입점과 Git flow에 맞게 갱신
- 수정: `tests/test_knowledge_store.py`, `tests/test_knowledge_cli.py` — managed path, 명령별 safe default, user recovery와 새 lifecycle 회귀 보강
- 수정: `.gitignore` — `docs/knowledge/.knowledge-local.json`만 제외; tracked config는 제외하지 않음
- 수정: `agentos/knowledge/schema.py` — OKF frontmatter 필수값·상태값·sources 구조 검증

## 의존성 분석

- 외부 의존성: 아래에 선언함. `git`, `bash`, `python3`와 local bare fixture는 repository baseline 도구이므로 network dependency가 아니다.
- 스캔 기준: standalone Python 표준 라이브러리, optional AHA host, optional AgentOS installed skill, skill catalog/manifest, GitHub viewer 문서, 모든 `Run:` 명령과 cross-project fixture

## 의존성 게이트

### AgentOS 설치

- name: AgentOS 설치
- type: nonstandard-local-tool
- required: false
- purpose: `agentos knowledge` adapter와 bundled skill catalog를 제공한다. standalone skill runtime에는 필요하지 않다.
- preflight:
  Run: `python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help`
  Expected: `PASS knowledge-standalone-ready`
- fallback:
  available: true
  reason: AgentOS가 없으면 standalone skill runtime을 직접 실행한다.
- failure_behavior: CONTINUE_WITH_FALLBACK

### AHA host bridge registration

- name: AHA host bridge registration
- type: nonstandard-local-tool
- required: false
- purpose: 외부 AHA host에서 `aha knowledge`가 bridge를 호출하는 실제 등록을 검증한다.
- preflight:
  Run: `command -v aha >/dev/null && aha knowledge --help >/dev/null && echo 'PASS aha-host-ready'`
  Expected: `PASS aha-host-ready`
- fallback:
  available: true
  trigger: `aha` 또는 bridge registration API가 현재 host에 없음
  action: standalone/AgentOS adapter와 fake-host parity만 검증하고 실제 AHA 등록은 중단한다.
  limits: `aha knowledge` actual invocation 완료를 주장하지 않는다.
  verification:
    Run: `bash tests/harness/test_aha_knowledge_skill_parity.sh`
    Expected: `PASS aha-knowledge-skill-parity`
- failure_behavior: use_fallback

### GitHub viewer

- name: GitHub viewer
- type: external-service
- required: false
- purpose: canonical relative Markdown links가 GitHub web UI에서 탐색 가능하다는 문서 경계를 설명한다. 구현/자동화는 local bare repository로 검증한다.
- preflight:
  Run: `test -f docs/knowledge/README.md && echo 'PASS github-viewer-docs-ready'`
  Expected: `PASS github-viewer-docs-ready`
- fallback:
  available: true
  trigger: GitHub 접근 또는 credential 없음
  action: local clone에서 상대 링크·index 계약만 검증한다.
  limits: live GitHub page를 열거나 remote credential을 사용하지 않는다.
  verification:
    Run: `bash tests/harness/test_aha_knowledge_cross_project.sh`
    Expected: `PASS aha-knowledge-cross-project`
- failure_behavior: use_fallback

## 실행 전 안전 경계

- remote URL과 credential은 문서·로그·테스트 출력에 기록하지 않는다.
- `backup`은 working tree가 clean일 때 사용자가 준 message로 **local commit만** 만들며 push하지 않는다. `sync`는 기본적으로 fetch/pull만 하고, `sync --push --confirm-branch <branch>`만 remote write를 수행한다. 자동 commit·push·stash·reset·clean·force checkout은 금지한다.
- 기존 `docs/knowledge` 문서를 자동 삭제하거나 덮어쓰지 않는다. 충돌·dirty working tree·잘못된 remote는 중단하고 복구 명령을 안내한다.
- skill 설치는 기존 AgentOS skill manifest 규칙을 따르며, 임의 symlink나 프로젝트 외부 파일을 읽지 않는다.
- Git runner는 `shell=False`와 argv allowlist(`init`, `status`, `remote`, `fetch`, `pull`, `add`, `commit`, `push`, `clone`)만 사용하고, credential/token/key/cookie/authorization 환경변수를 제거한 최소 env만 전달한다.

## 구현 작업

### Task 0: 실행 전 baseline과 Git 경계 확인

**파일:**
- 수정 없음
- 참조: `.agents/_version.json`, `docs/knowledge/README.md`, `agentos/knowledge/store.py`, `agentos/commands/knowledge.py`, `catalog/skills/catalog.json`

**사용자에게 보이는 마일스톤:** 구현자가 현재 knowledge 계약과 Git 실행 환경을 재현할 수 있다.

- [ ] **Step 1: 기존 knowledge 회귀 baseline 실행**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py -q`
Expected: `PASS` (기존 knowledge 테스트 전부 통과); 실패하면 구현을 시작하지 않고 failure output을 기록한다

- [ ] **Step 2: Git 및 임시 bare remote preflight 실행**

Run: `git --version && tmpdir=$(mktemp -d) && git init --bare "$tmpdir/knowledge.git" >/dev/null && test -d "$tmpdir/knowledge.git/refs" && echo 'PASS knowledge-git-ready'`
Expected: `PASS knowledge-git-ready`

- [ ] **Step 3: AHA host와 protected-path authorization preflight 실행**

`aha` host는 optional integration으로만 검사한다. `.agents/agents/harness/knowledge-curator.md`를 수정하기 전에는 `codex`가 authorized architect인지 확인하고, 아니면 protected change를 중단한다. 이 preflight 및 후속 structural audit은 GitHub/MCP 승인을 요구하지 않는다.

Run: `python3 -c "import json; assert 'codex' in json.load(open('.agents/_version.json'))['authorized_architects']; print('PASS knowledge-curator-protected-authorized')" && (command -v aha >/dev/null && aha knowledge --help >/dev/null && echo 'PASS aha-host-ready' || echo 'PASS aha-host-fallback')`
Expected: `PASS knowledge-curator-protected-authorized` 및 `PASS aha-host-ready` 또는 `PASS aha-host-fallback`

### Task 1: 독립 skill runtime과 repository service 구현

**파일:**
- 생성: `catalog/skills/knowledge-curator/scripts/knowledge_core.py`, `catalog/skills/knowledge-curator/scripts/knowledge.py`, `catalog/skills/knowledge-curator/scripts/aha_knowledge_bridge.py`
- 생성: `agentos/knowledge/skill_adapter.py`
- 생성: `docs/knowledge/.knowledge-repository.json`, `docs/knowledge/.knowledge-local.json`
- 수정: `agentos/knowledge/store.py`, `agentos/knowledge/__init__.py`
- 수정: `agentos/knowledge/schema.py` — OKF metadata/lifecycle/source contract
- 수정: `.gitignore`, `tests/test_knowledge_store.py`
- 생성: `tests/test_knowledge_okf.py`
- 생성: `tests/test_knowledge_git_security.py`

**사용자에게 보이는 마일스톤:** AgentOS가 없어도 standalone skill이 관리된 checkout 안에서 안전하게 저장되며, 다른 진입점은 같은 결과를 보여 준다.

- [ ] **Step 1: standalone runtime의 의존성 경계 정의**

`knowledge_core.py`만 lifecycle, OKF validation, repository config, Git runner를 소유한다. `knowledge.py`와 AHA bridge는 같은 파일을 import하고, AgentOS adapter는 `global_skills_dir()/knowledge-curator/scripts/knowledge.py`를 `shell=False` argv-list로 호출한다. 모든 adapter는 JSON line `{ok, code, action, changed, next}`와 exit code 0/2/3을 보존하며 독자 Git/store 로직을 갖지 않는다. 이 Step에서 새 standalone script와 test fixture를 먼저 생성한 뒤에 아래 검증을 실행한다.

Run: `python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help | grep -q 'init' && python3 catalog/skills/knowledge-curator/scripts/knowledge.py --help | grep -q 'backup' && echo 'PASS knowledge-standalone-ready'`
Expected: `PASS knowledge-standalone-ready`

- [ ] **Step 2: repository config와 managed path 계약 정의**

tracked `docs/knowledge/.knowledge-repository.json`은 `version`, credential 없는 remote URL, branch, `checkout_path: docs/knowledge`만 소유한다. device-local `docs/knowledge/.knowledge-local.json`은 `last_sync`만 소유하고 `.gitignore`에 등록한다. 첫 실행은 정확히 `knowledge init --remote <https-or-ssh-url-without-userinfo> --branch <branch> --project <project-root> --adopt-existing`로 한다. `--remote`와 `--branch`는 필수이고, existing `docs/knowledge`에 파일이 있으면 `--adopt-existing` 없이는 no-change/exit 2로 거부한다. `--adopt-existing`은 config와 local Git repository만 만들며 fetch/pull/push/overwrite는 하지 않는다; 이후 사용자가 `status`로 확인하고 `backup --message <message>` 또는 `sync`를 선택한다. clone/pull 후 `status`는 tracked config를 읽어 local state를 재생성한다. remote URL에는 userinfo/token을 거부하며 config/checkout의 symlink 또는 project-root 탈출은 거부한다.

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_skill.py tests/test_knowledge_git_security.py -q -k 'managed or path or config or standalone or symlink'`
Expected: `PASS knowledge-config-path-contract`

- [ ] **Step 3: OKF metadata와 lifecycle 계약 정의**

`type`을 필수로 검증하고 `status`를 `draft|stable|deprecated`로 제한한다. `summary`는 `description`으로, 단일 문자열 `source`/`citation`은 `sources` 목록으로 전환하며, `category`와 unknown extension field는 보존한다. 기존 `published` 문서는 새 계약으로 명시적 migration 대상으로 분리한다.

Run: `python3 -m pytest tests/test_knowledge_okf.py -q`
Expected: `type`, 상태값, `description`, `sources`, extension 보존 및 구계약 거부 테스트 PASS

- [ ] **Step 4: nested tag schema와 링크 계약 정의**

`domain`, `context`, 선택적 `task` namespace와 상대 Markdown 링크를 문서화하고, nested tag를 Obsidian YAML 배열과 AgentOS parser가 동일한 문자열로 보존하도록 고정한다. 검색 인덱스나 검색 명령은 구현하지 않는다.

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_skill.py -q -k 'tag or link'`
Expected: nested tag 보존·상대 링크 계약 테스트 PASS

- [ ] **Step 5: Git command runner와 dirty/conflict 보호 구현**

Git runner는 `shell=False`, argv allowlist, filtered environment, sanitized typed error를 사용한다. dirty checkout, merge/rebase/cherry-pick state, invalid/credential-bearing remote, symlink escape에서 no-change로 중단한다. `reset --hard`, `clean`, force checkout, auto-stash, automatic push는 코드·테스트 모두에서 금지한다. 실패는 조건·no-change·redacted next command를 출력한다.

Run: `python3 -m pytest tests/test_knowledge_git_security.py -q`
Expected: `PASS knowledge-git-security-boundary`

- [ ] **Step 6: OKF store lifecycle과 standalone repository service 통합**

OKF frontmatter/type/status/category 검증을 유지하고 publish/update/deprecate 결과가 Git diff에서 추적되도록 연결한다. inbox Markdown, frontmatter, Git output, validation messages의 instruction-like text는 저장·표시만 하며 command/authorization/reviewer state를 바꾸지 않는 adversarial fixture로 검증한다.

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_git_security.py -q -k 'store or prompt or authority'`
Expected: `PASS knowledge-store-data-boundary`

### Task 2: AHA와 AgentOS CLI의 공통 adapter 구현

**파일:**
- 수정: `agentos/commands/knowledge.py`
- 생성: `agentos/knowledge/skill_adapter.py`, `catalog/skills/knowledge-curator/scripts/aha_knowledge_bridge.py`
- 생성: `tests/test_knowledge_skill.py`

**사용자에게 보이는 마일스톤:** `aha knowledge`와 `agentos knowledge`가 같은 저장소와 결과 계약을 사용한다.

- [ ] **Step 1: 명령 계약 확정**

`init`, `status`, `sync`, `backup`의 command table을 help/README/test에 같은 wording으로 기록한다: `init --remote <url> --branch <branch> --project <root> --adopt-existing`만 populated existing checkout을 채택하고, `init`은 그 외 기존 checkout을 no-change/exit 2로 거부한다. `status`는 변경 없음, `backup --message`는 clean tree에서 local commit만 생성, `sync`는 fetch/pull만, `sync --push --confirm-branch <branch>`만 remote write다. 각 help/output은 변경 여부·never-push default·exit 0/2/3·다음 안전 행동을 표시한다. 기존 inbox/publish/update/deprecate/list와 충돌 없이 등록하며 검색 명령은 이 계획에 새로 등록하지 않는다.

Run: `python3 -m pytest tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q -k 'help or command_contract or recovery'`
Expected: `PASS knowledge-command-contract`

- [ ] **Step 2: AHA adapter를 공통 service에 연결**

AgentOS adapter와 AHA bridge는 portable core의 JSON line을 그대로 중계해 lifecycle/Git 로직을 중복하지 않는다. AHA host가 없을 때 fake host는 bridge stdin/stdout protocol만 검증한다. host가 Task 0에서 발견되면 external registration을 별도 확인하고, 발견되지 않으면 actual `aha knowledge` 완료 주장은 중단한다.

Run: `bash tests/harness/test_aha_knowledge_skill_parity.sh && python3 -m pytest tests/test_knowledge_skill.py -q -k 'installed or parity or adapter'`
Expected: `PASS aha-knowledge-skill-parity` 및 `PASS knowledge-installed-adapter-parity`

- [ ] **Step 3: CLI lifecycle regression 실행**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q`
Expected: 모든 knowledge 관련 테스트 PASS

### Task 3: knowledge skill 패키지와 문서 흐름 구현

**파일:**
- 생성: `catalog/skills/knowledge-curator/SKILL.md`
- 수정: `catalog/skills/catalog.json`
- 수정: `.agents/agents/harness/knowledge-curator.md`
- 수정: `docs/knowledge/README.md`, `docs/knowledge/index.md`
- 수정: `.gitignore`
- 생성/수정: `tests/test_knowledge_skill.py`, `tests/test_knowledge_cli.py`

**사용자에게 보이는 마일스톤:** 에이전트가 같은 knowledge service를 사용하도록 안전한 명령 순서와 Git 복구 절차를 안내한다.

- [ ] **Step 1: skill 사용 계약 작성**

문서 첫 화면에 한국어 entrypoint quick-start table을 둔다: standalone exact command/전제/용도, `agentos knowledge` exact command/installed-skill 전제/용도, AHA bridge가 등록된 경우의 exact host command/전제/용도, 그리고 AHA·AgentOS가 없을 때 standalone으로 복귀하는 길을 함께 적는다. 공통 예시는 draft → OKF 지식 번들 검증 → review → publish → status → backup/sync 순서이며, `type`/`description`/`sources`, `domain`/`context`/선택적 `task` tag, inbox data-authority 경계를 설명한다. 검색 명령은 새 skill flow로 안내하지 않는다.

Run: `python3 -m pytest tests/test_knowledge_skill.py tests/test_knowledge_cli.py -q -k 'quickstart or entrypoint or docs or help'`
Expected: `PASS knowledge-entrypoint-docs-contract`

- [ ] **Step 2: skill catalog 등록과 설치 검증**

Run: `python3 -m pytest tests/test_knowledge_skill.py -q -k install`
Expected: skill catalog 발견·설치·manifest 기록 테스트 PASS

- [ ] **Step 3: 보호 문서와 사용자 문서 정합성 확인**

Run: `python3 -m pytest tests/test_knowledge_skill.py -q -k 'curator_guidance or no_new_search or authority'`
Expected: `PASS knowledge-curator-guidance-contract`

- [ ] **Step 4: GitHub 기본 뷰어와 상대 링크 사용법 문서화**

GitHub에서 바로 열리는 repository layout, root/하위 `index.md` 탐색, concept 간 상대 Markdown 링크 작성법, 외부 `sources[].resource`와 내부 관계 링크의 구분, orphan lint 복구 절차를 skill과 `docs/knowledge/README.md`에 명시한다. `init/status/sync/backup` command table에는 purpose, required input, local change 여부, default never-push, exit-code 의미, 성공·거부 뒤 next action을 모두 적고 dirty/conflict/wrong-remote output에는 condition·no-change·redacted recovery command를 포함한다.

Run: `python3 -m pytest tests/test_knowledge_cli.py tests/test_knowledge_skill.py -q -k 'recovery or dirty or conflict or remote or command_contract'`
Expected: `PASS knowledge-recovery-docs-output-contract`

### Task 4: Git backup과 cross-project 통합 검증

**파일:**
- 생성: `tests/harness/test_aha_knowledge_git_workflow.sh`, `tests/harness/test_aha_knowledge_cross_project.sh`
- 생성: `tests/harness/test_aha_knowledge_security_boundary.sh`
- 수정: `tests/test_knowledge_cli.py`, `tests/test_knowledge_git_security.py`
- 수정: `docs/knowledge/README.md`, project SSOT 문서

**사용자에게 보이는 마일스톤:** 한 프로젝트에서 만든 OKF 지식을 백업하고 다른 프로젝트에서 clone/pull해 열어볼 수 있다.

- [ ] **Step 1: local backup/restore 시나리오 검증**

Run: `bash tests/harness/test_aha_knowledge_git_workflow.sh`
Expected: `PASS aha-knowledge-git-workflow`

- [ ] **Step 2: 두 프로젝트 cross-project 시나리오 검증**

Project A에서 `backup --message`로 local commit한 뒤 temporary bare remote를 통해 explicit `sync --push --confirm-branch main`를 실행하고, Project B가 clone/pull하여 동일한 OKF frontmatter·본문·상대 링크를 확인한다. fixture는 temp bare remote만 쓰며 user remote/credential에는 접근하지 않는다.

Run: `bash tests/harness/test_aha_knowledge_cross_project.sh`
Expected: `PASS aha-knowledge-cross-project`

- [ ] **Step 3: nested tag 재구조화 검증**

동일 문서의 `domain`·`context`·선택적 `task` tag를 추가·변경해도 Obsidian에서 계층으로 인식되고, standalone/AgentOS가 tag 문자열을 보존하며, 상대 링크가 유지되는지 검증한다.

Run: `python3 -m pytest tests/test_knowledge_skill.py -q -k 'nested or tag or link'`
Expected: nested tag와 상대 링크 회귀 테스트 PASS

- [ ] **Step 4: OKF 지식 번들 검증과 AgentOS policy 검증**

정상 bundle, 존재하지 않는 상대 링크, index에 등록되지 않은 concept, inbound link가 없는 orphan, 잘못된 `index.md`/`log.md`, 외부 URL source를 각각 검사한다. 기본 모드는 복구 가능한 경고를 출력하고, `--strict`는 orphan·broken internal link·index 불일치를 실패로 처리한다.

Run: `bash tests/harness/test_aha_knowledge_okf_validation.sh`
Expected: `PASS aha-knowledge-okf-validation`; OKF 오류와 AgentOS policy 오류가 별도 분류됨

- [ ] **Step 5: public boundary와 전체 focused suite 실행**

Run: `python3 -m pytest tests/test_okf_bundle_validation.py tests/test_knowledge_policy.py tests/test_knowledge_okf.py tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py tests/test_knowledge_git_security.py -q && bash tests/harness/test_aha_knowledge_standalone.sh && bash tests/harness/test_aha_knowledge_git_workflow.sh && bash tests/harness/test_aha_knowledge_skill_parity.sh && bash tests/harness/test_aha_knowledge_cross_project.sh && bash tests/harness/test_aha_knowledge_okf_validation.sh && bash tests/harness/test_aha_knowledge_security_boundary.sh && bash scripts/security/verify-public-repo.sh`
Expected: 모든 pytest와 verifier가 exit code 0이고 여섯 harness 명령이 각각 PASS 출력 및 `PASS public-repo-security-boundary`

### Task 5: Gate 2 리뷰·manifest·closeout

**파일:**
- 수정: active plan 및 필요한 SSOT/HISTORY 문서
- 생성: `.agents/traces/audit-plan-review.md`, `.agents/traces/audit-principle.md`, `.agents/traces/audit-usability-review.md`

**사용자에게 보이는 마일스톤:** 구현 계획과 구현 결과가 독립 리뷰·검증 증거를 갖는다.

- [ ] **Step 1: plan-reviewer·principle-auditor·usability-reviewer 리뷰 요청**

Run: `test -s .agents/traces/audit-plan-review.md && test -s .agents/traces/audit-principle.md && test -s .agents/traces/audit-usability-review.md && rg -q 'PASS' .agents/traces/audit-plan-review.md && rg -q 'PASS' .agents/traces/audit-principle.md && rg -q 'PASS' .agents/traces/audit-usability-review.md && echo 'PASS knowledge-gate2-review-artifacts'`
Expected: `PASS knowledge-gate2-review-artifacts`; 세 artifact는 plan path/hash, independent reviewer provenance, UTC timestamp, verdict, implementer separation을 포함한다

- [ ] **Step 2: protected `.agents` 변경의 structural audit와 manifest 동기화**

`codex` authorization이 Task 0에서 PASS일 때에만 `.agents/agents/harness/knowledge-curator.md`를 바꾼다. principle-auditor는 이 파일 하나만 protected scope로 감사하며 다른 `.agents` asset 변경은 허용하지 않는다. 이후 manifest update/check를 실행한다.

Run: `python3 -c "import json; assert 'codex' in json.load(open('.agents/_version.json'))['authorized_architects']; print('PASS knowledge-curator-protected-authorized')" && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --update codex && bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check`
Expected: `PASS knowledge-curator-protected-authorized` 및 두 manifest 명령 PASS; 하나라도 실패하면 protected 변경을 중단한다

- [ ] **Step 3: fresh verification과 closeout 기록**

Run: `python3 -m pytest tests/test_knowledge_store.py tests/test_knowledge_cli.py tests/test_knowledge_skill.py tests/test_knowledge_git_security.py -q && bash tests/harness/test_aha_knowledge_security_boundary.sh`
Expected: fresh focused suite와 `PASS aha-knowledge-security-boundary` 후에만 plan의 `reviewed`/완료 상태와 `HISTORY.md` checkpoint(`plan=.agentos/project/exec-plans/active/2026-08-09-aha-knowledge-skill-git.md`)를 갱신

## 비목표 및 보류 항목

- 외부 벡터 DB, semantic embedding, 중앙 knowledge SaaS는 이번 계획에서 다루지 않는다.
- Git remote 자동 생성·자동 push·credential 저장은 다루지 않는다.
- 기존 `docs/knowledge` 내용의 대량 이동/정리는 별도 migration plan 없이는 수행하지 않는다.
- `aha` 레거시 전체 리팩터링은 이 계획의 범위가 아니며 knowledge adapter 계약만 다룬다.

## 리뷰 반영 이력

- 2026-08-09: 사용자 선택으로 자동화 테스트와 별도 프로젝트 clone/pull 검증을 Plan Quality Gate에 반영함.
- 2026-08-09: 사용자가 AgentOS 미설치 환경에서도 skill 자체가 실행되어야 한다는 제약을 추가함. standalone runtime, optional AgentOS adapter, 독립 실행 검증을 계획에 반영함.

## 구현 결과

(구현 후 작성)

## 사용 방법

(구현 후 작성)

## 아카이브 결정

(구현과 검증, Gate 2 closeout 후 기록)
