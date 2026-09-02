# Quality Score Continuum

Optional quantitative score for comparing implementation quality. Use it when a plan, reviewer, or user asks for measurable scoring.

## Score Dimensions

| Dimension | Weight | Measurement Method |
|-----------|--------|--------------------|
| Correctness | 0.30 | Test pass rate |
| Security | 0.25 | Security checklist or review result |
| Performance | 0.15 | No regression versus baseline |
| Coverage | 0.15 | Coverage tool output |
| Consistency | 0.15 | Lint/type errors or style contract |

Composite score:

```text
composite = correctness*0.30 + security*0.25 + performance*0.15
          + coverage*0.15 + consistency*0.15
```

## Measurement

Prefer terminal evidence:

```bash
npm test
uv run pytest -q
npm run lint
npm run type-check
```

When automated tools are unavailable, mark estimates as `(estimated)` and explain the evidence basis.

## Thresholds

| Range | Grade | Decision |
|-------|-------|----------|
| 90-100 | A | PASS |
| 75-89 | B | CONDITIONAL PASS |
| 60-74 | C | FAIL |
| 0-59 | D | HARD FAIL |

## Keep / Discard Rule

```text
IF score_after >= score_before:
    KEEP
ELSE IF score_before - score_after < 5:
    REVIEW with justification
ELSE:
    DISCARD or rollback the experiment
```

When a scored experiment is explicitly tracked, record it in `.agents/traces/experiment-ledger.md`.

## Score Record Format

```markdown
### Quality Score @ {phase}

| Dimension | Score | Detail |
|-----------|-------|--------|
| Correctness | 85 | 17/20 tests pass |
| Security | 90 | No CRITICAL/HIGH |
| Performance | 75 | estimated, no regression observed |
| Coverage | 70 | 70% line coverage |
| Consistency | 95 | 0 lint errors, 1 type warning |
| Composite | 83.5 | Grade: B |
```
