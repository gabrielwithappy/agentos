---
name: intent-clarification
description: >
  다단계 작업 착수 전 사용자 의도·제약·성공 기준을 인터뷰로 추출한다.
  writing-plans 직전에 호출하라.
  Karpathy autoresearch 철학 기반 — "가설과 측정 기준이 없는 실험은 실험이 아니다."
  brainstorm(발산)과 달리 이미 방향이 정해진 요청에서 전제·제약·완료 기준만 빠르게 수렴하여
  Plan Quality Gate를 통과할 수 있는 Intent Sheet를 생성한다.
  사용자가 "계획을 세우자", "구현하자", "만들어줘"처럼 다단계 구현을 요청할 때 반드시 이 스킬을 먼저 발동하라.
model: sonnet
---

# Intent Clarification

## 핵심 철학 (Karpathy autoresearch 기반)

Karpathy autoresearch의 핵심: 에이전트는 `program.md`(가설 정의서)없이 실험을 시작하지 않는다.
이 스킬은 그 `program.md`를 코딩 전에 사용자와 합의하는 과정이다.

실험(계획) 전에 반드시 세 가지를 고정한다:
1. **가설 (Hypothesis)**: "이것을 바꾸면 저것이 나아질 것이다"
2. **측정 기준 (Plan Quality Gate)**: 실행 후 누가 판단해도 동일한 Pass/Fail 조건
3. **범위 (Scope Fence)**: 건드릴 것과 절대 건드리지 않을 것의 경계

## When to Use

- 사용자가 다단계 구현 또는 아키텍처 변경을 요청하는 경우
- 요청이 구체적이나 제약·완료 기준이 불명확한 경우
- `writing-plans` 직전 게이트로 자동 발동
- "계획 세우자", "만들어줘", "구현하자" 등의 표현이 나올 때
- 사용자가 원하는 기능을 아직 명확히 설명하지 못했지만, `Requirement Brief`는 이미 존재하는 경우

## When NOT to Use

- 단일 파일 수정 등 단순 작업 (바로 실행)
- 이미 Intent Sheet가 존재하는 경우 (재인터뷰 불필요)
- 자유로운 아이디어 탐색 → `brainstorm` 사용
- 사용자가 아직 무엇을 원하는지조차 흐리게 말하는 단계
  이 경우 먼저 `requirement-discovery` 사용
- 목표/예시/완료 기준이 부족하면 `requirement-discovery`의 canonical triage contract를 참조해 discovery로 되돌린다

## One Question Protocol (MANDATORY)

**한 번에 하나의 질문만 한다.** 사용자가 답하면 다음 질문으로 이동한다.
질문을 묶어서 던지지 마라. 사용자를 압도하지 마라.
전 단계 답변이 충분히 명확하면 다음 질문을 건너뛸 수 있다.
질문 순서는 항상 사용자 목적, 기대 변화, 완료 기준을 먼저 두고 그 다음에 범위나 기술 제약을 묻는다.
표면적인 작업 방식 질문은 목적이 선명해지기 전까지 뒤로 미룬다.
필수 핵심 질문만 남기고, 같은 의미의 반복 질문은 하지 않는다.
사용자가 목적을 바로 한 문장으로 못 정리하면, 한 번에 하나의 질문 형식은 유지한 채 2-3개의 짧은 선택지를 통해 자기 의도를 스스로 확인하게 할 수 있다.
이 선택형 self-check는 구현 표면 선택지가 아니라 사용자 목적 후보여야 한다.
선택지를 제시할 때도 에이전트가 목적을 대신 결정하지 말고, 사용자가 "이 중 어느 쪽에 더 가깝다"를 고르게 해 자기 의도를 스스로 확인하게 한다.

## 실행 흐름

### Phase 1: 코드베이스 스캔 (사용자 개입 없음)
- 관련 파일과 기존 패턴을 파악한다.
- brownfield 작업이라면 `codebase-explorer`를 선택적으로 사용해 read-only 방식으로 Tech Stack, 핵심 타입, 패턴, 프로토콜, 관습을 먼저 수집한다.
- `lessons-learned.md`에서 유사 작업의 선례를 확인한다.
- 코드베이스에서 답할 수 있으면 먼저 확인하고, 같은 내용을 사용자에게 다시 묻지 않는다.
- 이미 답이 명확한 질문은 건너뛴다.
- `Requirement Brief`가 있으면 이를 먼저 읽고, discovery 단계에서 이미 확정된 항목은 다시 묻지 않는다.
- `docs/project/00-project-index.md`가 있으면 프로젝트 문서 컨텍스트로 읽고, 특히 `docs/project/01-project-charter.md`와 `docs/project/02-product-scope-and-requirements.md`에서 이미 답한 목표/범위/완료 기준은 다시 묻지 않는다.
- `docs/project` root 문서가 없거나 비어 있어 실행계획 준비 상태를 판단할 수 없으면 인터뷰를 확장하기 전에 `aha project init/check` 또는 `requirement-discovery` 문서 준비 상태 확인으로 되돌린다.
- user-facing frontend 또는 visual quality critical 작업이면 현재 `docs/project/reference/wireframes/` 아래 current wireframe pair와 관련 root summary 문서를 먼저 읽는다.
- current wireframe pair, 최신 update 시각, 관련 reference가 비어 있으면 인터뷰를 확장하지 말고 `requirement-discovery`의 `docs/project bundle readiness`로 되돌린다.

### Role Boundary

- `requirement-discovery`: 사용자가 원하는 기능을 아직 명확히 설명하지 못할 때 `Requirement Brief`를 만든다.
- `goal-alignment-reviewer`: **user-goal alignment only**를 판정한다.
- `intent-clarification`: `Requirement Brief` 또는 사용자 응답을 바탕으로 실행 계약 SSOT인 `Intent Sheet`를 만든다.
- `plan-reviewer`: **execution feasibility and plan quality only**를 판정한다.
- `Requirement Brief`가 있으면 이를 입력 artifact로 받아 `Intent Sheet`를 생성한다.

### Phase 2: 의도 수렴 인터뷰

아래 질문을 순서대로, **한 번에 하나씩 객관식(Multiple-choice)** 형태로 묻는다.
사용자가 쉽게 선택할 수 있도록 번호(1, 2, 3...)와 함께 명확한 옵션을 제공하고, 항상 "기타 (직접 입력)" 옵션을 포함한다.

에이전트는 사전에 파악한 컨텍스트(Phase 1 스캔 결과 등)를 바탕으로 상황에 맞는 **동적 선택지**를 생성하여 제안하는 것을 기본으로 하며, 필요한 경우 표준 선택지를 혼합하여 제공한다.

frontend UI intent가 구현 품질을 좌우하는 작업이면, 일반 객관식 질문 전에 아래 conditional flow를 먼저 적용한다.
- current wireframe pair와 관련 summary 문서가 있으면 그 문서가 frontend UI intent primary surface라고 선언한다.
- 필요한 supporting refinement path가 빠져 있으면 먼저 그 경로를 채우게 한다.
- 문서가 충분하면 아래 항목을 one-question protocol로 한 번에 하나씩 확인한다.
  - `좋아하는 레퍼런스`
  - `피해야 하는 레퍼런스`
  - `정보 밀도`
  - `시각적 위계`
  - `꼭 지켜야 할 톤`
  - `실패로 볼 화면 특성`
- 이 체크리스트가 비어 있으면 discovery 없이 추정하지 말고 `docs/project bundle readiness` reroute 또는 current wireframe 문서 보강을 먼저 요구한다.

**Q1. 작업의 주 목적 (Hypothesis)**
> 에이전트가 문맥을 분석하여 가장 가능성 높은 목적 후보 3~4개를 객관식으로 제시한다.
→ 예시:
  1. 새로운 기능 추가 및 연동
  2. 기존 기능 개선 및 리팩토링
  3. 버그 수정 및 예외 처리 강화
  4. 기타 (직접 입력)
→ 사용자가 선택한 후, "~가 나아질 것이다" 형태의 핵심 가설로 재진술하여 확인받는다.

**Q2. 완료 검증 방식 (Plan Quality Gate)**
> 에이전트가 검증 가능한 방식을 객관식으로 제안하고 선택하게 한다. (터미널 명령어 기반)
→ 예시:
  1. 특정 스크립트/명령어의 정상 실행 결과 확인
  2. 자동화된 단위/통합 테스트 작성 및 통과
  3. 빌드 및 로컬 서버 구동 후 직접 UI 수동 확인
  4. 기타 (직접 입력)
→ 선택 결과에 따라 에이전트가 구체적인 터미널 명령어(예: `pytest tests/ -q`)를 제안하여 합의한다. "잘 되면" 같은 모호한 조건은 거부한다.

**Q3. 작업 영향 범위 (Scope Fence)**
> 건드리면 안 되는 파일명 등 기술적인 세부 사항을 직접 묻기보다 아키텍처 관점의 범위를 객관식으로 제시한다.
→ 예시:
  1. 프론트엔드(UI/UX) 영역만 수정
  2. 백엔드(API, DB) 영역만 수정
  3. 풀스택(전체 영역) 수정
  4. 특정 컴포넌트 제한 (기타 직접 입력)
→ 범위 밖 항목을 명시적으로 기록한다.

**Q3-1. Worktree 필요 여부 (parallel / isolation gate)**
> (객관식으로 유지하되, 필요시에만 묻는다)
→ 1. 현재 checkout에서 바로 진행 (충돌 위험 없음)
→ 2. 별도 worktree 생성 필요 (parallel 작업 등)

**Q4. 완성도 및 우선순위 (Priority)**
> 작업의 우선순위를 명확히 하기 위해 객관식으로 묻는다.
→ 예시:
  1. 빠른 MVP(최소 기능) 구현 우선
  2. 프로덕션 수준의 안정성과 엣지 케이스 처리 우선
  3. 기술 부채 해결 및 코드 구조 리팩토링 우선
  4. 기타 (직접 입력)
→ 이 선택은 `writing-plans`의 Simplicity Gate 기준이 된다.

### Phase 3: Intent Sheet 생성

인터뷰 완료 후 reference mission 문서로 `.agentos/project/exec-plans/archive/reference/intent/intent-YYYYMMDD-<slug>.md`에 저장한다.

```markdown
# Intent Sheet: <작업명>

**날짜:** YYYY-MM-DD  
**요청자 의도 요약:** [한 문장]

## 가설
> [에이전트가 재진술한 가설]

## Plan Quality Gate
> "계획 실행 완료 후, 아래 조건들이 자동 채점으로 통과하는가?"
- [ ] Run: `<터미널 명령어>` Expected: `<정확한 출력>`
- [ ] Run: `<터미널 명령어>` Expected: `<정확한 출력>`

*판단자가 누구든 동일한 결과를 낸다. "잘 되면"은 기준이 아니다.*

## 범위 제약 (Scope Fence)
- 포함: [건드릴 파일/컴포넌트]
- 제외: [건드리지 않을 것 — 계획에서 절대 수정 금지]

## 기술 스택 제약
- [제약 사항 또는 "없음"]

## Worktree Decision
- 필요 여부: [필요 / 불필요]
- 이유: [parallel 작업 / 현재 checkout 보존 / 없음]
- ownership: [branch/path naming 또는 "없음"]

## 우선순위
- [MVP / 완전한 구현] → writing-plans Simplicity Gate 기준
```

### Phase 4: writing-plans 전환

Intent Sheet 저장 후:
```
Intent Sheet가 `.agentos/project/exec-plans/archive/reference/intent/<filename>.md`에 저장되었습니다.
이를 기반으로 writing-plans 스킬로 구체적인 실행 계획을 `.agentos/project/exec-plans/active/<filename>.md`에 작성할까요?
```

`Requirement Brief`에서 넘어왔다면 흐름은 다음으로 고정한다:
`requirement-discovery -> goal-alignment-reviewer(PASS required) -> intent-clarification -> writing-plans`

## writing-plans와의 연동

이 스킬이 생성한 Intent Sheet는 `writing-plans`의 **Gate 0 (Plan Quality Gate)** 판단 기준이 된다.
Intent Sheet의 `Plan Quality Gate` 섹션 = 계획의 모든 `Expected:` 조건의 원본이 된다.
계획 작성 시 Intent Sheet를 반드시 참조하라.

## Common Pitfalls

- **Q를 묶어 던지기**: "A도 알고 싶고 B도..." → 하나씩
- **"잘 되면"을 기준으로 수락**: 반드시 터미널 명령어로 재질문
- **인터뷰 없이 바로 계획 작성**: intent-clarification을 건너뛰면 P1 위반
- **brainstorm 중복 호출**: 이미 brainstorm을 거친 경우 Intent Sheet만 작성
- **Scope Fence 미작성**: 범위 제약이 없으면 계획이 오버엔지니어링될 위험
- **선택형 self-check를 표면 선택으로 바꾸기**: 선택지는 사용자 목적 후보를 좁히는 용도여야 하며 파일 경로/스택/구현 surface를 먼저 고르게 하면 안 된다
