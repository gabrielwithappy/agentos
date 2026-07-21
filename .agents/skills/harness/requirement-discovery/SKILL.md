---
name: requirement-discovery
description: >
  사용자가 자신이 원하는 구현 요구사항을 명확히 설명하지 못할 때,
  단계적 대화로 목표·문제·예시·비목표를 끌어내고 Requirement Brief와 개발 입력 문서 패키지로 문서화한다.
  intent-clarification 전에 호출하라.
model: sonnet
---

# Requirement Discovery

## Harness Principles (MANDATORY)

You are part of the Agent Harness. You MUST read and follow **[AGENTS.md](AGENTS.md)** principles:
1. **P1: Reliability > Sustainability > Efficiency** is your core directive.
2. **P4: Simplicity (Anti-Complexity)**: 요구사항을 발견하는 것이 목적이지 설계를 과도하게 확장하는 것이 아니다.

## Overview

이 스킬은 사용자가 "무엇을 만들고 싶은지"를 완전히 설명하지 못할 때 발동한다.
핵심 목표는 해답을 대신 설계하는 것이 아니라, 사용자의 목표와 실제 요구사항을 대화로 수렴해
`Requirement Brief`와 supporting discovery package를 만드는 것이다.

`Requirement Brief`는 discovery artifact의 primary SSOT다.
`User Stories`, `RTM`, `Implementation Guide`는 개발 handoff를 돕는 supporting discovery package다.
실행 계약 SSOT는 계속 `intent-clarification`이 만드는 `Intent Sheet`다.
흐름은 다음으로 고정한다:

`requirement-discovery -> goal-alignment-reviewer -> intent-clarification -> writing-plans`

## When to Use

- 사용자가 원하는 기능을 스스로 명확히 설명하지 못하는 경우
- "대충 이런 느낌", "정확히는 모르겠는데", "뭘 만들어야 할지 같이 정하자" 같은 요청
- 구현에 앞서 사용자 목표, 구체 예시, 비목표를 먼저 문서화해야 하는 경우
- `intent-clarification`을 바로 시작하기엔 요구사항이 아직 흐린 경우
- `docs/project` 문서는 존재하지만 다음 구현에 필요한 정보가 충분히 닫혔는지 먼저 확인해야 하는 경우
- `document-delivery-lead`가 문서 부족 또는 문서 준비 상태 blocker를 발견해 discovery reroute를 요구하는 경우
- Codex CLI 진입이 아래 셋 중 하나로 성립하는 경우
  - 명시 호출: `requirement-discovery`, `요구사항 인터뷰 시작`, `요구사항 분석 시작`
  - 자연어 fallback: 구현은 원하지만 목표/예시/완료 기준을 바로 말하지 못하는 경우
  - reroute: `intent-clarification` 또는 `writing-plans`가 canonical triage contract를 참조해 되돌리는 경우

## When NOT to Use

- 사용자가 이미 구현 목표와 완료 기준을 명확히 설명한 경우
- 자유로운 아이디어 탐색이 목적일 뿐 실제 요구사항 문서화가 목적이 아닌 경우
  이 경우 `brainstorm` 사용
- 이미 `Requirement Brief`가 있고, 이제 완료 기준/범위/검증으로 수렴해야 하는 경우
  이 경우 `intent-clarification` 사용

## Entry Criteria

아래 triage 질문 3개 중 2개 이상에 즉답하지 못하면 discovery에 진입한다.

1. 원하는 결과를 한 문장으로 말할 수 있는가
2. 원하는 동작 예시와 원하지 않는 동작 예시를 하나씩 말할 수 있는가
3. 완료 기준 또는 성공 판단 기준을 말할 수 있는가

## Do Not Enter If

- `Requirement Brief`가 이미 존재한다
- 목표/예시/완료 기준이 충분해 `intent-clarification`으로 바로 수렴 가능하다
- 아이디어 발산과 접근 비교가 목적이라서 요구사항 문서화보다 탐색이 우선이다
- triage 질문 3개 중 2개 이상에 이미 답할 수 있다

## One Question Protocol (MANDATORY)

**한 번에 하나의 질문만 한다.**
답변을 들은 뒤 요약하고, 다음 질문으로 넘어간다.
질문을 묶지 마라.

## Discovery Contract

이 스킬은 아래 다섯 축을 채우는 것을 목표로 한다:
1. **사용자 목표**: 무엇이 좋아지길 원하는가
2. **현재 문제**: 지금 무엇이 막히는가
3. **구체 예시**: 원하는 동작과 원하지 않는 동작은 무엇인가
4. **비목표**: 이번 작업에서 하지 않을 것은 무엇인가
5. **열린 질문**: 아직 확정되지 않은 결정은 무엇인가

## Output Package Contract

인터뷰가 충분히 수렴되면 아래 결과물 패키지를 함께 만든다.

### Primary discovery artifact
- `docs/project/reference/implementation/01-requirement-brief.md`

### Supporting discovery package
- `docs/project/reference/implementation/02-user-stories.md`
- `docs/project/reference/implementation/03-rtm.md`
- `docs/project/reference/implementation/04-implementation-guide.md`

원칙:
- `Requirement Brief`는 사용자 목표와 문제 정의의 primary artifact다.
- `User Stories`는 역할/업무 흐름을 개발 단위로 번역한다.
- `RTM`은 요구사항-기능-검증 연결을 고정한다.
- `Implementation Guide`는 코드 설계를 확정하지 않고 엑셀/인터뷰 내용을 시스템 모델로 해석한다.
- supporting discovery package가 있어도 실행 계약 SSOT는 여전히 `Intent Sheet`다.

## 실행 흐름

### Phase 1: 코드베이스 스캔

- 관련 파일, 기존 기능, 유사 패턴을 먼저 읽는다.
- 이미 코드가 답해주는 질문은 사용자에게 다시 묻지 않는다.
- `lessons-learned.md`의 Cross-Domain 섹션을 참고해 오버엔지니어링을 피한다.
- `docs/project`가 이미 현재 작업의 기준선이면 먼저 `docs/project/README.md`, `docs/project/document-governance.md`, `docs/project/00-project-index.md`, `docs/project/01-project-charter.md`, `docs/project/02-product-scope-and-requirements.md`를 읽는다.

### Phase 2: 요구사항 발견 인터뷰

`docs/project`가 이미 사용자와 agent의 기준선이거나 `document-delivery-lead`가 reroute한 경우, 일반 Q1-Q5 인터뷰 전에 짧은 `docs/project` 문서 준비 상태 pass를 먼저 수행한다.

**DIAGNOSE**

- 어떤 root doc slot이 비어 보이는지 먼저 선언한다.
- 이미 문서가 답해주는 질문은 다시 묻지 않는다.
- 먼저 아래 세 가지를 분류한다:
  1. 사용자 의도와 비목표가 현재 root docs에 닫혀 있는가
  2. 다음 구현 backlog가 `03-system-contract.md`, `04-safety-risk-verification.md`, `05-agent-operating-contract.md` 같은 프로젝트 문서 경계와 이어지는가
  3. trace/control 문서가 현재 코드 존재 증거와 섞여 읽히지 않는가
- 위 세 항목이 충분히 닫혀 있으면 readiness reroute를 더 늘리지 말고 일반 discovery 질문으로 넘어간다.

**PROBE**

- 질문은 한 번에 하나씩, 비어 있는 문서 슬롯 기준으로 묻는다.
- 권장 질문 축:
  - scope / non-goal: `02-product-scope-and-requirements.md`
  - model boundary / terminology: `03-system-contract.md`
  - verification expectation: `04-safety-risk-verification.md`
  - ownership / escalation: `05-agent-operating-contract.md`
- user-facing frontend 또는 visual quality critical 작업이면 `docs/project/reference/implementation/` 아래 current visual support note(latest `.md` + optional `.excalidraw`)를 canonical capture surface로 취급한다.
- current wireframe pair가 비어 있거나 frontend intent가 모호하면 아래 질문 축을 one-question protocol로 한 번에 하나씩 확인한다.
  - `좋아하는 레퍼런스`
  - `피해야 하는 레퍼런스`
  - `정보 밀도`
  - `시각적 위계`
  - `꼭 지켜야 할 톤`
  - `실패로 볼 화면 특성`
- supporting refinement가 필요하면 같은 wireframe namespace 또는 validation/reference path에 보강 경로를 적고, root summary 문서에서 그 경로를 링크하게 한다.
- 구현 해법을 먼저 제안하지 않는다.
- `I don't know`는 실패가 아니라 열린 질문으로 기록한다.

**SYNTHESIZE**

- 일반 discovery 질문으로 넘어가기 전 또는 reroute를 닫을 때 아래를 요약한다.
  - 확인된 사용자 의도
  - 현재 docs가 이미 닫아 주는 정보
  - 아직 비어 있는 정보
  - 보강이 필요한 root doc
  - document status verdict: `ready | partial | blocked`
- 이 요약은 기존 `Requirement Brief`, handoff summary, 진행 기록 안에 흡수한다. 별도 readiness 전용 artifact나 새로운 brief schema를 만들지 않는다.

아래 질문을 순서대로, 한 번에 하나씩 진행한다.

canonical triage contract의 소유자는 이 스킬이다.
다른 skill은 triage 질문을 복제하지 말고 이 계약을 참조만 한다.

**Q1. 사용자 목표**
> "이 기능이 생기면 무엇이 가장 좋아져야 하나요?"

**Q2. 현재 문제**
> "지금은 어떤 점 때문에 원하는 결과를 못 얻고 있나요?"

**Q3. 구체 예시**
> "원하는 동작의 예시 하나와, 원하지 않는 동작의 예시 하나를 알려주세요."

**Q4. 비목표**
> "이번 작업에서 굳이 하지 않아도 되는 것은 무엇인가요?"

**Q5. 열린 질문**
> "아직 확정하지 못한 결정이나 선택지가 있나요?"

필요하면 다음 보조 질문을 사용한다:
- "사용자가 직접 보게 되는 결과물은 무엇인가요?"
- "정확히 어떤 입력을 받으면 좋겠나요?"
- "이 기능이 실패했다고 느끼는 경우는 언제인가요?"

### Phase 3: Iteration Discipline For Ralph Loop

- iteration당 최대 1개 질문, 1개 요약, 1개 문서 갱신만 수행한다.
- 중간 요약은 대화 2회 이하 주기로 남긴다.
- 재시작 입력 surface는 `Requirement Brief` 초안, `HISTORY.md`의 최신 `[CHECKPOINT]`, `.agents/traces/harness/loop-state.md`의 `plan_path`/`iteration`/`current_task`/`current_step`/`last_event`다.
- checkpoint 위치:
  - active plan 체크박스 또는 현재 작업 메모
  - `HISTORY.md`의 `[CHECKPOINT]`
  - loop mode일 때 `.agents/traces/harness/loop-state.md`
- 최종 결론 저장 위치:
  - `Requirement Brief`
  - 필요 시 goal alignment review trace

loop mode에서는 짧고 명확한 진행 보고를 우선한다.
질문 하나로 충분히 닫히는 iteration이면 더 진행하지 말고 종료한다.

### Phase 4: Discovery Package 생성

인터뷰가 충분히 수렴되면 아래 산출물을 생성하거나 갱신한다.

#### 4-1. Requirement Brief
- 저장 위치: `docs/project/reference/implementation/01-requirement-brief.md`
- 목적: 사용자 목표, 현재 문제, 예시, 비목표, 제약, 열린 질문을 고정
- 성격: primary discovery artifact

```markdown
# Requirement Brief: <작업명>

**날짜:** YYYY-MM-DD
**상태:** Working Draft
**요약:** [한 문장]

## 사용자 목표
- [무엇이 좋아져야 하는가]

## 현재 문제
- [지금 막히는 점]

## 구체 예시
- 원하는 동작: [...]
- 원하지 않는 동작: [...]

## 비목표
- [이번 작업에서 하지 않을 것]

## 제약
- [기술/범위/운영 제약 또는 "없음"]

## 열린 질문
- [아직 미확정 사항]
```

#### 4-2. User Stories
- 저장 위치: `docs/project/reference/implementation/02-user-stories.md`
- 목적: 입력자/검토자/공통 사용자의 실제 행동을 story와 acceptance criteria로 정리

```markdown
# User Stories

## Actor: <역할명>

### US-01 <스토리 제목>
<사용자로서, ... 하고 싶다. 그래야 ...>

수용 기준:
- ...
- ...
```

#### 4-3. RTM
- 저장 위치: `docs/project/reference/implementation/03-rtm.md`
- 목적: 요구사항과 사용자 스토리, 기능/화면, 최소 검증을 연결

```markdown
# Requirements Traceability Matrix

| Req ID | 요구사항 | 근거 | User Story | 기능/화면 | 최소 검증 |
|---|---|---|---|---|---|
```

#### 4-4. Implementation Guide
- 저장 위치: `docs/project/reference/implementation/04-implementation-guide.md`
- 목적: 인터뷰와 참고 자료를 시스템 관점의 입력/계산/검토/이력 구조로 번역

```markdown
# MVP Implementation Guide

## 구현 방향
- ...

## 엑셀/기존 자료를 시스템으로 해석하는 방법
- ...
```

패키지 작성 규칙:
- supporting discovery package는 `Requirement Brief`를 모순 없이 확장해야 한다.
- 사용자가 명시하지 않은 구현 결정을 확정 사실처럼 쓰지 마라.
- 기존 프로젝트 자료(예: 엑셀, 인터뷰 메모)가 있다면 근거 출처를 문서에 남긴다.
- 프로젝트에 이미 동일 이름 문서가 있으면 덮어쓰지 말고 현재 인터뷰 결과를 반영해 갱신한다.

### Phase 5: Goal Alignment Review

- `Requirement Brief`를 만든 뒤에는 `goal-alignment-reviewer` PASS가 **필수 gate**다.
- `goal-alignment-reviewer`는 **user-goal alignment only**를 본다.
- `User Stories`, `RTM`, `Implementation Guide`는 supporting discovery package이며 reviewer의 직접 판정 범위가 아니다.
- 구현 가능성, Task 품질, 파일 분해는 이 agent의 역할이 아니다.
- trace 파일은 `.agents/traces/goal-alignment-review-YYYYMMDD-<slug>.md` 규칙을 사용한다.
- 최종 verdict는 trace에만 남기지 말고 active plan 또는 진행 기록에도 요약을 복사한다.

### Phase 6: Intent Handoff

discovery package 저장 후 다음 메시지로 넘긴다:

```text
Requirement discovery package가 `docs/project/reference/implementation/` 아래에 정리되었습니다.
- Requirement Brief: `docs/project/reference/implementation/01-requirement-brief.md`
- User Stories: `docs/project/reference/implementation/02-user-stories.md`
- RTM: `docs/project/reference/implementation/03-rtm.md`
- Implementation Guide: `docs/project/reference/implementation/04-implementation-guide.md`

이 결과물을 입력으로 intent-clarification 스킬을 실행해 Intent Sheet를 만들까요?
```

## Common Pitfalls

- 해결책을 너무 빨리 제안하기
- 요구사항 발견 단계에서 구현 계획까지 밀어붙이기
- 비목표를 기록하지 않아 범위가 계속 커지게 두기
- `Requirement Brief`를 `Intent Sheet` 대신 실행 계약 SSOT로 오해하기
- supporting discovery package 없이 인터뷰를 끝내 개발 handoff가 끊기게 두기
- `docs/project` 문서 준비 상태 결과를 별도 임시 artifact로 흩뜨리거나 두 번째 discovery 체계처럼 불려 나가게 두기
