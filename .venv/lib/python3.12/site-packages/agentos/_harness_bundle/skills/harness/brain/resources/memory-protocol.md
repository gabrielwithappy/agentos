# File-First Handoff Protocol

Current runtime does not configure MCP-backed memory tools. This document is only for explicit delegated CLI handoffs that need shared artifacts.

Do not create progress/result artifacts for normal single-session work. Prefer direct tool output, `HISTORY.md` checkpoints, reviewed plans, and final responses.

---

## Optional handoff artifacts

Use repository files only when a task is delegated across agents, workspaces, or long-running sessions and a durable handoff is necessary.

| Artifact | Use |
|----------|-----|
| `.agents/traces/task-board.md` | Optional external assignment board |
| `.agents/traces/progress/<agent-id>.md` | Optional long-running progress notes |
| `.agents/traces/result/<agent-id>.md` | Optional delegated result summary |
| `.agents/traces/experiment-ledger.md` | Optional measurable experiment log |
| `.agents/traces/session-metrics.md` | Optional clarification debt log |

If `.agents/traces/task-board.md` exists, read only the section for the assigned task. If it does not exist, use the prompt, active plan, or `HISTORY.md` as the source of truth.

---

## On Start

1. Identify the assignment source: prompt, reviewed exec plan, loop-state, or optional task board.
2. Confirm write scope and verification commands.
3. Create optional handoff artifacts only when another agent or future session must consume them.

## During Execution

- Keep normal work in the conversation and tool outputs.
- For explicit handoff mode, append concise status entries to the chosen trace file.
- Include files touched, verification run, and open blockers.

## On Completion

For explicit handoff mode, write a result summary under `.agents/traces/result/` with:

- Status: `completed`, `blocked`, or `failed`.
- Files created or modified.
- Verification commands and observed results.
- Remaining risks or follow-up work.

For normal single-session work, skip these artifacts and provide the result directly.
