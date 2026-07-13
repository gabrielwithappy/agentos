# Vendor Detection Protocol

Use this only when selecting the current runtime vendor guide or writing compatibility guidance.

## Detection Order

1. Claude Code: Claude-specific system prompt or Claude task/delegation tool.
2. Codex CLI: Codex-specific system prompt or `apply_patch` tool.
3. Gemini CLI: Gemini-specific prompt or delegation syntax.
4. Fallback CLI: no native subagent support detected.

## Vendor Guide Mapping

| Vendor | Guide | Result Handling |
|--------|-------|-----------------|
| Claude Code | `.agents/vendors/claude.md` | Native task result or file-first handoff |
| Codex CLI | `.agents/vendors/codex.md` | Subagent result notification or file-first handoff |
| Gemini CLI | `.agents/vendors/gemini.md` | Vendor guide plus file-first handoff |
| Fallback CLI | No vendor guide beyond `AGENTS.md` | Explicit trace/result file only when delegated |

Prefer `AGENTS.md` for shared policy and the current vendor guide for runtime-specific interpretation.
