# Execution Handoff Notes - Claude Code

Current runtime does not configure MCP-backed memory tools. Claude Code handoffs should use the file-first protocol in `../memory-protocol.md` only when durable coordination artifacts are explicitly needed.

## Optional handoff artifacts

- If `.agents/traces/task-board.md` exists, read only the assigned task section.
- Use reviewed plans, loop-state, and `HISTORY.md` as stronger state sources.
- Do not create progress/result artifacts for normal single-session work.

When a handoff artifact is needed, place it under `.agents/traces/progress/` or `.agents/traces/result/` and keep it concise.
