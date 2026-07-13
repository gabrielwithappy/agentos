# Exploration Loop

Use this only when the normal fix path stalls or the user explicitly asks to compare alternatives.

## Activation

Activate when:

- The same gate fails twice on the same issue.
- A scored fix creates a meaningful negative delta.
- The user asks to try multiple approaches and pick the best.

Do not activate for obvious single fixes, formatting, or first-attempt implementation.

## Protocol

### 1. Hypothesize

Use `reasoning-templates.md` to define two or three alternatives.

```markdown
Problem: {what needs to be solved}
Current score or evidence: {score, failing test, or review finding}
Attempts so far: {count and outcomes}

Hypothesis A: ...
Hypothesis B: ...
```

### 2. Experiment

Run each hypothesis in isolation:

- In one session, use git stash, patch backups, or separate branches.
- In delegated work, give each worker a distinct workspace and write scope.
- Keep each experiment small enough to verify directly.

### 3. Measure

Use `quality-score.md` or exact verification commands.

```markdown
| Hypothesis | Evidence | Composite | Decision |
|------------|----------|-----------|----------|
| A | tests pass, lint clean | 82 | DISCARD |
| B | tests pass, lint clean, simpler diff | 87 | KEEP |
```

### 4. Select

Keep the strongest verified option. Discard or revert the others. If none improves the current state, stop and ask the user for guidance.

### 5. Record

When experiment tracking is explicitly active, record rows in `.agents/traces/experiment-ledger.md`. Significant discarded attempts may become lesson candidates, but durable promotion requires human approval.

## Limits

| Constraint | Value |
|------------|-------|
| Max hypotheses per round | 3 |
| Max exploration rounds per session | 2 |
| Minimum score gap to justify winner | 5 points or equivalent evidence |

## Integration

| Component | Use |
|-----------|-----|
| `quality-score.md` | Measurement |
| `experiment-ledger.md` | File-first experiment record |
| `reasoning-templates.md` | Hypothesis structure |
| `context-loading.md` | Conditional loading trigger |
