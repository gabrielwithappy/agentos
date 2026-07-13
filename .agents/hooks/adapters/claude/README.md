# Generic Claude Boundary

Generic Claude environments do not have a native filesystem hook runner in this harness.

Claude Code uses native hooks through `.claude/settings.json`. Generic Claude should read `CLAUDE.md`, `AGENTS.md`, the relevant vendor guide, and the `.agents/hooks` principles as instruction text. Do not fabricate a native hook config for generic Claude.
