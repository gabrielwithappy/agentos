---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
model: sonnet
---

# Executing Plans

## Harness Principles (MANDATORY)

You are part of the Agent Harness. You MUST read and follow **[AGENTS.md](AGENTS.md)** principles:
1. **P1: Reliability > Sustainability > Efficiency** is your core directive.
2. **Trigger 4 (Brain)**: If you encounter recurring logical gaps or complex architectural constraints, check `.agents/skills/harness/brain/` for existing knowledge before designing from scratch.

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 0: 실행 모드 결정 (에스컬레이션)

계획을 실행하기 전에 실행 환경을 확인하고 에스컬레이션한다:

**루프 모드** (`harness_loop.py`가 이 세션을 호출한 경우):
- 컨텍스트가 매 루프마다 리셋됨 → 직접 실행 가능

**대화형 모드** (사용자가 Claude Code와 직접 대화 중인 경우):
- 컨텍스트가 세션 내내 누적됨
- 태스크 수 ≥ 4 또는 추정 파일 읽기 수 ≥ 10이면 → **에스컬레이션 필수**

```
## [ESCALATION] 실행 모드 선택

- **상황**: 대화형 세션에서 계획 실행 요청
- **태스크 수**: N개 / **추정 컨텍스트 부하**: [낮음|중간|높음]

**선택지 A**: 루프 모드 — `./.agents/skills/harness/harness-loop.sh --resume --cli claude`
  장점: 매 루프 컨텍스트 리셋, 상태는 loop-state.md/HISTORY.md에 영속, 에스컬레이션 대화형 처리 지원
  단점: 사용자가 터미널에서 직접 실행해야 함

**선택지 B**: 대화형 직접 실행
  장점: 즉시 시작 가능
  단점: 컨텍스트 누적 → 긴 계획에서 이전 결과 망각 위험

**에이전트 권장**: 태스크 수와 컨텍스트 부하에 따라 A 또는 B
```

### Step 1: Load and Review Plan
1. Read plan file
2. **Gate check**:
   - 계획 파일 헤더에 `reviewed: true`가 반드시 있어야 한다.
   - 없으면 이 스킬이 직접 추가하지 않는다. `writing-plans` Gate 2(`plan-reviewer` + `principle-auditor`)를 먼저 완료하도록 되돌린다.
   - 대화형 세션에서는 `reviewed: true`가 없으면 실행 금지다.
   - **루프 모드일 때만** 아래 추가 Gate를 확인한다:
     ```bash
     grep "execution_locked" .agents/traces/harness/loop-state.md
     ```
     Expected: `execution_locked: false`
     → `execution_locked: true` 또는 파일 없음이면 실행 금지. "랄프 루프 완료 대기 중" 에스컬레이션 후 중단.
3. 대상 계획이 `.agentos/project/exec-plans/active/` 아래에 있는지 확인하고, 필요하면 board를 재생성한다:
   ```bash
   python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh
   ```
   루프 모드에서만 현재 실행 중인 계획 포인터를 `.agents/traces/harness/loop-state.md`의 `plan_path`로 해석한다.
   대화형 모드에서는 사용자가 지정한 active plan 경로를 기준으로 실행한다.
4. Review critically - identify any questions or concerns about the plan
5. If concerns: Raise them with your human partner before starting
6. main checkout 보존, review/spike/hotfix 격리, 또는 명시적으로 승인된 병렬 소유권 분리가 필요한 계획이면 canonical `git-worktree-parallel` skill로 예외적 격리 workspace를 먼저 준비한다
7. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. After the verification command returns `PASS`, mark the Step checkbox as completed
5. Update the plan's `진행 스냅샷` so `완료됨`, `현재 위치`, `다음 단계`, and `완료 신호` reflect the verified state. Existing `Progress Snapshot` labels are legacy aliases.
6. Update `사용자 진행 계획` rows when a milestone changes state, keeping the user-visible result and verification evidence current. Existing `User Progress Plan` labels are legacy aliases.
7. Update the plan's `장기 적용 표면` section so the traceability surface and durable result surface still point to the verified result location.
8. Keep progress in the plan Markdown only. Do not add a progress DB or separate status file for this contract
9. Mark the task as completed

Progress maintenance rules:
- Never advance `진행 스냅샷` before the relevant 검증 명령 has returned `PASS`.
- Never mark a `사용자 진행 계획` milestone complete before the related verification signal exists.
- If the session may stop before all tasks are done, update the plan's `세션 중단 대비 체크포인트` and the latest `HISTORY.md` handoff evidence before stopping.
- The checkpoint must name the current complete scope, unfinished work, next session first task, remaining verification, and related HISTORY checkpoint so the next run can resume without guessing.
- Keep append-only `HISTORY.md` checkpoint evidence searchable with existing `plan=` and `artifact=` tags when a meaningful user-visible milestone is reached.
- `진행 스냅샷` is a human-readable summary, not an automatic percent calculator.
- `사용자 결과 요약` and `사용자 진행 계획` are reader-facing presentation contracts only. They do not authorize implementation, protected-path mutation, Gate 2 bypass, or reviewer-authority changes.
- `장기 적용 표면` is also a reader-facing contract. It must point to the verified durable result surface, not just traceability surface entries.

### Step 3: Complete Development

After all tasks complete and verified:
- 계획 문서를 `.agentos/project/exec-plans/active/`에 유지한 채 `> **상태:** 완료`로 바꾸고 아래 closeout metadata를 추가하거나 갱신한다:
  ```markdown
  > implementation_started_at: YYYY-MM-DDTHH:MM:SSZ
  > implementation_completed_at: YYYY-MM-DDTHH:MM:SSZ
  > implementation_duration: <human-readable elapsed time, e.g. 15m 26s>
  ```
  `implementation_duration`은 started/completed timestamp 차이를 사용자가 이해하기 쉬운 단위로 적는다.
- 완료된 active plan에는 사용자가 결과를 확인할 수 있도록 아래 섹션을 포함해야 한다:
  - `## 구현 결과`
  - `## 사용 방법`
  - `## 완료 증거`
  - `## 아카이브 결정`
- completed plan이 user-facing or operator-facing work를 닫는다면, `## 장기 적용 표면`의 `durable result surface`도 실제 갱신된 결과 위치로 남아 있어야 한다.
- Do not close work as complete when the result exists only in the plan document or `HISTORY.md`. That is `plan-only completion` and must be treated as incomplete.
- `아카이브 결정`은 사용자가 명시적으로 archive를 요청하기 전까지 계획이 active에 남는다고 설명해야 한다.
- append-only `HISTORY.md` closeout checkpoint는 `plan=<active-or-archive-path>`를 포함해야 한다.
- 최종 산출물 경로 또는 proof artifact가 있으면 같은 checkpoint에 `artifact=<path>`도 함께 남긴다.
- 진화 계획을 완료했다면 `[EVOLUTION_APPLIED]`를 기록하고 `EVOLUTION_APPLIED`, `applied result`, `result=`, `artifact=`, `verification=`, `next_action=`을 포함한다.
- 진화 트리거가 reusable change로 이어지지 않았거나 후속 계획으로 미뤄졌다면 `[EVOLUTION_DEFERRED]`를 기록하고 `classification=local-fix` 또는 `classification=deferred`, 이유, `next_action=`을 포함한다.
- `하네스 검증 완료` 같은 generic suite health checkpoint는 tagging 예외로 둘 수 있다.
- 이 실행 규칙은 `HISTORY.md` evidence 정렬 범위에만 적용한다. loop engine 변경이나 새 상태 필드는 추가하지 않는다.
- fresh verification evidence를 확보한 뒤 lifecycle board를 refresh한다:
  ```bash
  python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py refresh
  ```
- archive는 사용자가 명시적으로 요청한 경우에만 실행한다:
  ```bash
  python3 .agents/skills/harness/writing-plans/scripts/plan_lifecycle.py archive <plan-path> --status 완료
  ```
- refresh/archive 명령은 `.agentos/project/exec-plans/README.md`와 `.agents/mission/plan.json`도 함께 갱신한다
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **git-worktree-parallel** - REQUIRED when parallel work, main checkout preservation, or isolated review/spike/hotfix work is needed
- **git-worktree-parallel** - REQUIRED only when main checkout preservation or explicit isolated workspace handling is needed; it is not the default execution path
- **writing-plans** - Creates the plan this skill executes
- **finishing-a-development-branch** - Complete development after all tasks
