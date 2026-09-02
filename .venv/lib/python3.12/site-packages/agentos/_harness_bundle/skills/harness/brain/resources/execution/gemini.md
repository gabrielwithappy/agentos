# Execution Handoff Notes - Gemini

Current runtime does not configure MCP-backed memory tools. Gemini handoffs should use repository files only when explicit delegated coordination is required.

## Optional handoff artifacts

- If `.agents/traces/task-board.md` exists, read only the assigned task section.
- Prefer vendor guide instructions plus reviewed plans for execution state.
- Do not create progress/result artifacts for normal single-session work.

When persistent handoff is needed, follow `../memory-protocol.md` and store concise progress or result files under `.agents/traces/`.
