# Execution Handoff Notes - Codex

Current runtime does not configure MCP-backed memory tools. Codex sessions should rely on the prompt, reviewed exec plans, tool output, and `HISTORY.md` unless an explicit delegated CLI handoff requires trace files.

## Optional handoff artifacts

- If `.agents/traces/task-board.md` exists, read only the assigned task section.
- Use `.agents/mission/plan.json` and `.agentos/project/exec-plans/` for execution plan state.
- Do not create progress/result artifacts for normal single-session work.

For long-running delegated work, follow `../memory-protocol.md` and write concise files under `.agents/traces/progress/` or `.agents/traces/result/`.
