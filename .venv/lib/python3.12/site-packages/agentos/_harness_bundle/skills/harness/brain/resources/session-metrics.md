# Session Metrics and Clarification Debt

Optional file-first metrics for sessions where clarification debt should be tracked.

## Location

Use `.agents/traces/session-metrics.md` only when metrics are explicitly tracked. For normal sessions, `HISTORY.md` checkpoints and the final response are enough.

## Clarification Debt Scoring

| Event Type | Points | Description |
|------------|--------|-------------|
| `clarify` | +10 | Simple clarification question |
| `correct` | +25 | User correction changes direction |
| `redo` | +40 | Scope violation or rejected work requires restart |
| `blocked` | +0 | Agent correctly stopped and asked |

Modifiers:

| Condition | Modifier |
|-----------|----------|
| Charter not read before action | +15 |
| File outside scope | +20 |
| Same error repeated in session | x1.5 |

## Thresholds

| Threshold | Action |
|-----------|--------|
| CD >= 50 | Record an RCA candidate |
| CD >= 80 | Pause and request user re-specification |
| `redo` count >= 2 | Request explicit scope confirmation |

RCA entries are lesson candidates until reviewed. Durable promotion to `lessons-learned.md` requires human approval when it changes future agent behavior.

## Session Log Format

```markdown
## Session: {SESSION_ID}
Started: {ISO timestamp}
Request: "{original user request, first 100 chars}..."

| Turn | Agent | Event | Points | Detail |
|------|-------|-------|--------|--------|
| 5 | backend-engineer | correct | 25 | Changed from REST to GraphQL |
```

## Recording Steps

1. Classify the event type.
2. Append an event row to `.agents/traces/session-metrics.md`.
3. Check thresholds.
4. If a threshold is exceeded, record an RCA candidate and ask for approval before durable lesson promotion.

## Optional Quality Extension

When `quality-score.md` is active, append score progression and experiment summary from `.agents/traces/experiment-ledger.md`.
