---
name: brain
description: Shared harness context guidance for difficulty assessment, context loading, verification, routing, reasoning, and file-first coordination. Load progressively by task need.
model: sonnet
---

# Brain - Shared Agent Context

This directory is an index of optional guidance, not a runtime. Agents load only the files needed for the current task, following `resources/context-loading.md`.

## Protocol Index

| File | Purpose | When to Load |
|------|---------|--------------|
| `resources/context-loading.md` | Progressive disclosure and resource selection rules | At task start when deciding what context to inspect |
| `resources/difficulty-guide.md` | Task difficulty assessment | When scope or verification depth is unclear |
| `resources/context-budget.md` | Context window budgeting rules | When reading many files or large files |
| `resources/clarification-protocol.md` | Clarifying question triggers | Before acting on ambiguous requests |
| `resources/common-checklist.md` | Final verification checklist | Before completing Complex tasks |
| `resources/reasoning-templates.md` | Debug, decision, and exploration templates | Complex bugs or architecture decisions |
| `resources/quality-score.md` | Optional quantitative quality scoring | VERIFY / SHIP phase when scoring is requested |
| `resources/quality-principles.md` | Core quality principles | On demand |
| `resources/skill-routing.md` | Harness role routing reference | When composing or reviewing delegated work |
| `resources/prompt-structure.md` | Subagent prompt structure guidelines | When composing subagent prompts |
| `resources/experiment-ledger.md` | Optional experiment record format | When measurable experiments are explicitly tracked |
| `resources/exploration-loop.md` | Alternative-approach loop | When the same gate fails twice |
| `resources/memory-protocol.md` | file-first subagent artifact protocol | Load only when composing an explicit delegated CLI handoff |
| `resources/session-metrics.md` | Optional clarification debt metrics | End of session or when explicitly tracking CD |
| `resources/vendor-detection.md` | Runtime vendor detection reference | Orchestrator or compatibility work only |
| `resources/execution/claude.md` | Claude handoff notes | Claude subagent handoffs only |
| `resources/execution/gemini.md` | Gemini handoff notes | Gemini subagent handoffs only |
| `resources/execution/codex.md` | Codex handoff notes | Codex subagent handoffs only |

## Lessons

Cumulative cross-session lessons: `lessons-learned.md`.

Read only the relevant domain section for Complex or related tasks. Do not treat this file as permission to mutate lessons without the approval and manifest rules in `AGENTS.md`.
