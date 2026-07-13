---
name: brainstorm
description: Design-first ideation that explores user intent, constraints, and approaches before any planning or implementation. Use for brainstorming, ideation, exploring concepts, and evaluating approaches.
---

# Brainstorm - Design-First Ideation

## When to use
- Exploring a new feature idea before planning
- Understanding user intent and constraints before committing to an approach
- Comparing multiple design approaches with trade-offs
- When the user says "I have an idea" or "let's design something"
- Before invoking `pm` skill (write-plan) for complex or ambiguous requests

## When NOT to use
- Requirements are already clear and well-defined -> use pm-agent directly
- Implementing actual code -> delegate to specialized agents
- Performing code reviews -> use QA Agent
- Debugging existing issues -> use debug-agent
- 요구사항 문서화가 목적이면 brainstorm이 아니라 `requirement-discovery`를 사용한다

## Core Rules
1. **No implementation or planning before design approval** - brainstorm produces a design document, not code or task plans
2. **One question at a time** - ask clarifying questions sequentially, not in batches
3. **Always propose 2-3 approaches** - include a recommended option with trade-off analysis
4. **Section-by-section design** - present design incrementally with user confirmation at each step
5. **YAGNI** - do not over-engineer; design only what is needed for the stated goal
6. **Save design, then transition** - persist the approved design document before handing off to `pm` skill (write-plan)

## How to Execute
Follow the brainstorm workflow step by step:
1. **Phase 1 - Context**: Explore the existing codebase and understand the project landscape
2. **Phase 1.5 - Mode Selection**: Ask ONE question to determine mode:
   > "새 아이디어를 검증하고 싶으신가요 (Mode A), 아니면 기존 프로젝트의 설계 방향을 탐색하고 싶으신가요 (Mode B)?"
   - **Mode A (아이디어 검증)**: Phase 2에서 6개 강제 질문 적용 → 아이디어 실현 가능성 검증
   - **Mode B (설계 탐색)**: Phase 2 기존 방식대로 진행 (접근 방법 탐색)
3. **Phase 2 - Questions**: Ask clarifying questions one at a time
   - **Mode A 전용 — 6개 강제 질문 (순서대로, 1회에 1개)**:
     1. "지금 이걸 쓰는 사람이 실제로 있나요?" (수요 현실)
     2. "지금 이 문제를 어떻게 해결하고 있나요?" (현재 상태)
     3. "가장 절박하게 이 문제를 겪는 한 사람은 누구인가요?" (구체적 페르소나)
     4. "진입할 수 있는 가장 좁은 지점은 어디인가요?" (최소 쐐기)
     5. "직접 관찰한 것은 무엇인가요?" (1차 관찰)
     6. "5년 후에도 이게 필요한가요?" (미래 적합성)
   - **Mode B**: intent, constraints, scope 관련 질문 순차 진행
4. **Phase 3 - Approaches**: Propose 2-3 approaches with a recommended option and trade-off matrix
5. **Phase 4 - Design**: Present the detailed design section by section, getting user approval at each step
6. **Phase 5 - Documentation**: Save the approved design as a reference mission document under `docs/exec-plans/archive/reference/architecture/` and project memory.
   After saving, **Mandatory Assignment**: "지금 당장 할 수 있는 한 가지 구체적 행동"을 반드시 제시.
   예: "오늘 실제 사용자 1명과 10분 대화하기", "최소 기능 프로토타입 1개 만들기", "경쟁 제품 3개 직접 써보기"
7. **Phase 6 - Transition**: Invoke `pm` skill (write-plan) for task decomposition. The executable plan is created under `docs/exec-plans/active/`, while `.agents/mission/plan.json` remains the lifecycle registry SSOT.

요약: `brainstorm`는 아이디어 탐색과 접근 비교를 위한 단계이고, `requirement-discovery`는 사용자 목표를 `Requirement Brief`로 고정하는 요구사항 문서화 단계다.

## Change Log

- **[EVOLUTION_APPLIED] 2026-04-01**: gstack office-hours 패턴 통합 — Phase 1.5 Mode Selection + Mode A 6개 강제 질문 + Phase 5 Mandatory Assignment 추가. 사용자 승인 완료.
- **[EVOLUTION_APPLIED] 2026-03-28**: Phase 6 전환 대상을 `/plan`에서 `pm` skill (write-plan)으로 변경. 사용자 승인 완료.
  - WHY: brainstorm 완료 후 plan 수립 단계가 명확히 pm 스킬로 연결되지 않아 일관성 부재
  - 변경 범위: When to use, Core Rule 6, Phase 6

## Common Pitfalls
- **Jumping to solutions**: Asking "how" before fully understanding "what" and "why"
- **Too many questions at once**: Overwhelming the user with a wall of questions
- **Single approach bias**: Presenting only one option without alternatives
- **Over-engineering**: Designing for hypothetical future requirements instead of stated needs
- **Skipping confirmation**: Moving forward without explicit user approval on design decisions
