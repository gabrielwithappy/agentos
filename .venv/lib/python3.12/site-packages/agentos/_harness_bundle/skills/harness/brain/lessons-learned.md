# Lessons Learned

A cumulative lesson repository across sessions. Agents read only the relevant domain section for Complex or related tasks.
New durable lessons should start as lesson candidates in `HISTORY.md`, `.agents/traces/experiment-ledger.md`, or review output, then be promoted with human approval and the protected-path rules in `AGENTS.md`.

---

## Skill → Domain Mapping

| Role | Primary Section | Secondary Section |
|------|-----------------|-------------------|
| backend-engineer | Backend | Cross-Domain |
| frontend-engineer | Frontend | Cross-Domain |
| debug-investigator | Debug | Relevant domain |
| qa-reviewer | QA / Security | Relevant domain being reviewed |
| plan-reviewer | Cross-Domain | Relevant plan scope |
| principle-auditor | Cross-Domain | Relevant architecture scope |

---

## How to Use

### Reading (All Agents)
- At Complex task start: Read your domain section to prevent repeating mistakes
- Medium tasks: Reference if related items exist
- Simple tasks: Can skip

### Writing
Use this format for approved durable entries:
```markdown
### {YYYY-MM-DD}: {agent-type} - {one-line summary}
- **Problem**: {what went wrong}
- **Cause**: {why it happened}
- **Solution**: {how it was fixed}
- **Prevention**: {how to prevent in the future}
```

Lesson candidates that do not yet have approval should remain in `HISTORY.md` or trace files.

---

## Backend Lessons

> This section is referenced by backend-agent, debug-agent (for backend bugs).

### Initial Lessons (Recorded at Project Setup)
- **Use SQLAlchemy 2.0 style only**: Use `select()` instead of `query()`. Legacy style causes warnings.
- **Always review after Alembic autogenerate**: Auto-generated migrations may have missing indexes or incorrect types.
- **FastAPI Depends chain**: Calling other Depends inside a dependency function can cause ordering issues. Verify with tests.
- **async/await consistency**: Don't mix sync/async in a single router. Unify everything as async.

---

## Frontend Lessons

> This section is referenced by frontend-agent, debug-agent (for frontend bugs).

### Initial Lessons
- **Next.js App Router**: `useSearchParams()` must be used inside a `<Suspense>` boundary. Otherwise, build error.
- **shadcn/ui components**: Import path is `@/components/ui/button`, not `shadcn/ui`.
- **TanStack Query v5**: First argument of `useQuery` is object form `{ queryKey, queryFn }`. v4's `useQuery(key, fn)` form doesn't work.
- **Tailwind dark mode**: `dark:` prefix requires `darkMode: 'class'` setting to work.

---

## Mobile Lessons

> This section is referenced by mobile-agent, debug-agent (for mobile bugs).

### Initial Lessons
- **Riverpod 2.4+ code generation**: When using `@riverpod` annotation, `build_runner` execution required. Run `dart run build_runner build` before building.
- **GoRouter redirect**: Returning current path in redirect function causes infinite loop. Must return `null` to indicate no redirect.
- **Flutter 3.19+ Material 3**: `useMaterial3: true` is the default. M3 applies even without explicit setting in ThemeData.
- **Network on iOS simulator**: Use `127.0.0.1` instead of localhost. Or `10.0.2.2` for Android.

---

## QA / Security Lessons

> This section is referenced by qa-agent.

### Initial Lessons
- **Rate limiting verification method**: Send continuous requests with `curl` to verify 429 response. Code review alone is insufficient.
- **CORS wildcard**: `*` is OK for development environment, but must restrict to specific domains in production build.
- **npm audit vs safety**: Frontend uses `npm audit`, backend (Python) uses `pip-audit` or `safety check`.

---

## Debug Lessons

> This section is referenced by debug-agent.

### Initial Lessons
- **React hydration error**: Caused by code with different server/client values like `Date.now()`, `Math.random()`, `window.innerWidth`. Wrap with `useEffect` + `useState`.
- **N+1 query detection**: Setting `echo=True` in SQLAlchemy logs all queries. If same pattern query repeats, it's N+1.
- **State loss after Flutter hot reload**: initState of StatefulWidget doesn't re-execute on hot reload. State initialization logic should go in didChangeDependencies.

---

## Cross-Domain Lessons

> Referenced by all agents.

### Initial Lessons
- **API contract mismatch**: Parsing fails when backend uses `snake_case` but frontend expects `camelCase`. Casing must be specified in contract.
- **Timezone issues**: Backend stores in UTC, frontend displays in local timezone. Unify on ISO 8601 format.
- **Auth token passing**: Watch for mistakes where backend expects `Authorization: Bearer {token}` but frontend sends `token` header.
- **Over-Engineering (KISS)**: 에이전트 리뷰 과정에서 계획이 점점 복잡해지는 경향이 있음. 이를 방지하기 위해 반드시 `Simplicity Gate`를 적용하여 '요구사항 대비 추가된 복잡성'을 검역해야 함. (P1 Reliability)
- **Core vs domain capability boundary**: Mandatory governance belongs in core (`plan-reviewer`, `principle-auditor`, `usability-reviewer`). Domain implementation, debugging, QA, design, spreadsheet, and UI package help should stay in catalog packages unless the plan explicitly approves making them core.
- **macOS portable search baseline**: 하네스 테스트, 설치 스크립트, catalog 지침은 macOS 기본 도구인 `find`와 `grep`을 우선 사용한다. ripgrep 계열 명령은 사용자 환경에 설치되지 않을 수 있으므로 필수 검증 경로에 두지 않는다.
- **AI-native operating memory**: 반복 업무를 먼저 매핑하고, 공유 Git 컨텍스트와 append-only 결정 로그로 운영 기억을 축적한 뒤, 가장 단순한 자동화와 eval 루프로 품질을 고정해야 한다.

### 2026-04-01: research - gstack 분석 TOP 5 적용 패턴
- **패턴 1**: `careful` Hook — PreToolUse hook으로 `rm -rf`, `DROP`, `git push --force` 차단. Rule 2 텍스트 지침의 구조적 보완. 구현: `.agents/skills/harness/careful/bin/check-careful.sh` + settings.json 등록
- **패턴 2**: `investigate` Iron Law → `debug` 스킬 4단계 (증상수집 → 재현 → Scope Lock → 검증). Rule 2 반복 발동 근본 해결
- **패턴 3**: Completion Status Protocol — `HARNESS_COMPLETE:DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`
- **패턴 4**: lessons-learned.md 구조화 — `<!-- LESSON key="..." domain="..." -->` 태그로 Grep 검색 가능
- **패턴 5**: `retro` 경량 스킬 — HISTORY.md 500줄 초과 시 자동 패턴 분석 + 압축
- **참고**: `.agents/docs/research/gstack-analysis-2026-04-01.md`

### 2026-03-31: orchestrator - Concurrent bun plugin startup collision
- **Problem**: 4 Claude agents with discord plugin started simultaneously but 3 failed and became OFFLINE.
- **Root Cause**: The discord plugin's package.json runs `bun install && bun server.ts` unconditionally on start, and concurrent `bun install` causes lockfile/directory conflicts across the shared plugin directory.
- **Fix Applied**: Added `sleep 3` between starting each agent in the `pool-tmux.sh` loop to stagger their startup.
- **Prevention**: When orchestrating multiple agents that rely on the same plugin directory with dependency resolution at startup, always stagger their launch sequences.

### 2026-05-05: orchestrator - Codex child stagnation on large active plan
- **Problem**: Harness loop repeated Codex child stagnation three times while executing a large active plan, with no Task 1 artifacts produced.
- **Root Cause**: Each child reloaded long Phase A and plan context, then attempted broad implementation setup without a durable artifact or checkpoint inside the watchdog window.
- **Fix Applied**: Stopped the loop per Rule 2, recorded RCA in HISTORY.md, and blocked automatic resume pending human approval.
- **Prevention**: Resume large plans with bounded task-slice prompts, require a first artifact/checkpoint within 30 seconds, and avoid full-plan rereads on every child iteration.
- **CD Impact**: 3 repeated stagnation retries.

### 2026-05-05: orchestrator - Bounded Codex loop still stalled without file artifacts
- **Problem**: A human-approved Task 1-only harness-loop resume still reached Codex child stagnation after creating only directory scaffolding and no required Task 1 files.
- **Root Cause**: The bounded prompt still referenced the full active plan path and broad Step 1 contract, letting the child spend the watchdog window in context loading and setup instead of writing concrete files.
- **Fix Applied**: Stopped the loop, recorded the failed resume in HISTORY.md, and kept `loop-state.md` inactive.
- **Prevention**: Resume with a strict Execution Contract or direct interactive Step 1-1 execution that names the exact files to create and treats a real file artifact, not a directory or generic checkpoint, as the first progress gate.
- **CD Impact**: 1 additional stagnation retry after prior Rule 2 stop.

### 2026-05-14: coordinator - HISTORY compression checkpoint
- **Problem**: `HISTORY.md` reached 680 lines, exceeding the 500-line compression trigger.
- **Root Cause**: Multiple reviewed AHA expansion plans recorded detailed protected-path approvals, implementation checkpoints, and verification evidence in the same day.
- **Fix Applied**: Pattern counts were captured (`[LOOP_STOP]` = 23, `Rule 2` = 4) and the durable session summary was condensed here without deleting the source history.
- **Prevention**: For large multi-plan sessions, keep per-plan HISTORY entries concise and move stable cross-plan summaries into lessons or architecture references after verification.
- **CD Impact**: No new loop stop in this implementation slice; existing historical counts remain unchanged.

---

## Lesson Addition Protocol

### RCA Candidate Triggers

Record an RCA candidate when:

| Trigger | Responsible Role | Deadline |
|---------|-------------------|----------|
| Session CD score >= 50 | qa-reviewer | Before session close |
| Verification failure after a planned gate | debug-investigator or owner | Before retry |
| Same error type occurs 2+ times in session | current coordinator | Immediate |
| User explicitly requests "do not repeat this" | current agent | Before next action |

The candidate is mandatory when the trigger fires. Durable promotion to this file still follows human approval and protected-path rules.

### RCA Entry Format (Required Fields)

```markdown
### {YYYY-MM-DD}: {agent-type} - {one-line summary}
- **Problem**: {what went wrong - be specific}
- **Root Cause**: {why it happened - go deeper than surface}
- **Fix Applied**: {how it was resolved this time}
- **Prevention**: {process/prompt change to prevent recurrence}
- **CD Impact**: {clarify/correct/redo count if applicable}
```

### Review Promotion
When a recurring issue is confirmed:

1. Record a lesson candidate with evidence.
2. Ask for human approval if the lesson changes future agent behavior.
3. Add the approved entry to the relevant domain section.
4. Run manifest sync/check when this protected file changes.

### Coordinator Responsibilities
When there are failed tasks at session end:

1. Analyze failure cause.
2. Record the candidate in `HISTORY.md` or `.agents/traces/experiment-ledger.md`.
3. Promote only approved durable lessons.

### Experiment-Derived Lesson Candidates

At session end, discarded experiments with **delta <= -5** from `.agents/traces/experiment-ledger.md` may become lesson candidates.

Candidate entries use the RCA Entry Format above, with these additions:
- **Root Cause** field specifies which quality dimension regressed and why
- Append `(Source: Experiment Ledger #{N}, Session {session_id})` to the summary line

Do not append experiment-derived candidates to this file until human approval is recorded.

### When Lessons Become Too Many (50+)
- Move old lessons (6+ months) to archive
- Delete lessons invalidated by framework version upgrades
- This cleanup is performed manually (agents should not delete arbitrarily)

## Skill 수정 매핑

> `[SKILL_STAT]` 집계 기반으로 업데이트한다. outcome=FAIL 누적 ≥ 3회 시 해당 스킬 [EVOLUTION_PROPOSAL] 트리거.

| Skill | 마지막 수정일 | PASS | FAIL | PARTIAL | 비고 |
|-------|------------|------|------|---------|------|
| (최초 항목은 [SKILL_STAT] 태그 3회 이상 누적 후 자동 기재) | - | - | - | - | - |
