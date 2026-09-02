# Experiment Ledger

Optional file-first record for measurable change attempts and outcomes.

## Ledger Location

Use `.agents/traces/experiment-ledger.md` only when experiments are explicitly tracked. Do not create the ledger for ordinary implementation work.

## Ledger Format

```markdown
# Experiment Ledger - Session {SESSION_ID}
Started: {ISO timestamp}
Request: "{original user request, first 100 chars}..."

## Experiments

| # | Phase | Agent | Hypothesis | Score Before | Score After | Delta | Decision | Files Changed |
|---|-------|-------|------------|--------------|-------------|-------|----------|---------------|
| 1 | IMPL | backend-engineer | REST API with pagination | - | 72 | - | BASELINE | 3 |
| 2 | VERIFY | qa-reviewer | Add input validation | 72 | 78 | +6 | KEEP | 2 |
```

## Recording Protocol

Record an experiment only when all of these are true:

1. A discrete logical change was applied.
2. A before/after score or measurable verification result exists.
3. A keep, review, discard, or candidate decision was made.

Do not record trivial formatting, PLAN phase discussion, or changes without measurable evidence.

Append rows directly to `.agents/traces/experiment-ledger.md` in file-first mode. Include the verification command or evidence in the row notes when useful.

## Lesson Candidates

Discarded experiments with significant negative impact may produce lesson candidates. Candidates are not durable lessons by themselves.

Promotion rules:

- Keep lesson candidates in the ledger or record an `[EVOLUTION_PROPOSAL]` in `HISTORY.md`.
- Promote a candidate to `lessons-learned.md` only after human approval and the protected-path rules in `AGENTS.md`.
- Never mutate `AGENTS.md`, skill files, or lessons as an autonomous side effect of scoring.

## Integration Points

| Component | Use |
|-----------|-----|
| `quality-score.md` | Provides scores for delta calculation |
| `exploration-loop.md` | Records alternative hypotheses and selection |
| `session-metrics.md` | Can summarize experiment count at session end |
| `lessons-learned.md` | Receives approved lesson candidates only |
