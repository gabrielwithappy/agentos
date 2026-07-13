# Global agents available from trusted AHA core

This generated index helps agents discover trusted harness agents quickly.
It is a reading surface, not a runtime, and it does not auto-install anything.

## How to use

1. Match the request to a role by name and responsibility.
2. Read the exact role file under `.agents/agents/harness/` first.
3. Keep reviewer roles within their boundary.
4. Use `aha agents search` when you need catalog discovery beyond the core set.

## Harness Core Agents

- `contrarian`
- `goal-alignment-reviewer`
- `harness-architect`
- `knowledge-curator`
- `plan-reviewer`
- `principle-auditor`
- `simplifier`
- `usability-reviewer`

## Discovery Hints

- `Request phrase` and `Recommended agent` are the primary lookup cues.
- `하네스 에이전트와 리뷰` is the user-facing explanation surface for role routing.
- `aha bridge` can route to the correct agent surface without changing runtime state.
- `agents search` helps when you need optional catalog roles beyond the harness core.
- `agents install` must not auto-install; ask the user first.
- `ask the user` is the default when a catalog agent is only a recommendation.
- `do not auto-install` is a hard boundary for optional agents.

