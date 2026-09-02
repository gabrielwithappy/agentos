# Dynamic Context Loading Guide

Agents should not read every brain resource. Use Progressive Disclosure: read the minimum context that makes the current task executable and verifiable.

No Hermes skill runtime, no `skill_view` tool, and no plugin-runtime import are part of this contract.

---

## Skill Inspection Rule

When a task maps to a skill, inspect context progressively:

1. Read the selected `SKILL.md` first.
2. If both a user skill and harness skill share a name, use the user skill first and use the harness skill only as fallback.
3. Resolve relative references from the selected skill directory.
4. Open referenced files only when they are needed for the current task.
5. Stop loading once the task can be executed and verified.

---

## Load only when needed

| Resource | Trigger |
|----------|---------|
| `difficulty-guide.md` | Scope or verification depth is unclear |
| `context-budget.md` | Many files, large files, or long-running analysis |
| `clarification-protocol.md` | User intent, success criteria, or risk is ambiguous |
| `common-checklist.md` | Complex task closeout or high-risk verification |
| `reasoning-templates.md` | Multi-step debugging, architecture decisions, or repeated failures |
| `quality-score.md` | Quantitative scoring is explicitly useful |
| `experiment-ledger.md` | Measurable experiments are explicitly tracked |
| `exploration-loop.md` | Same gate fails twice or user requests alternatives |
| `memory-protocol.md` | Explicit delegated CLI handoff needs file-first artifacts |
| `session-metrics.md` | Clarification debt is explicitly tracked |
| `skill-routing.md` | Delegating or reviewing role selection |
| `vendor-detection.md` | Runtime compatibility or vendor guide selection |

For vendor-specific behavior, prefer `.agents/vendors/{claude,codex,gemini}.md` and then load `resources/execution/*.md` only for delegated handoff details.

---

## Prompt Composition

When composing subagent prompts:

1. Include the target role and success criteria.
2. Include only the referenced files needed by that role.
3. Include exact verification commands with Expected: PASS.
4. Include write ownership boundaries when edits are allowed.
5. Use `memory-protocol.md` only for explicit handoff artifacts, not normal single-session work.

This keeps subagent context small and prevents stale brain resources from acting as hidden runtime instructions.
