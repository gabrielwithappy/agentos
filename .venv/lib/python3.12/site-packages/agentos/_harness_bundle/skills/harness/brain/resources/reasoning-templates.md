# Reasoning Templates

Use these templates when the task needs explicit multi-step reasoning. Keep completed reasoning in the plan, final response, `HISTORY.md`, or a requested trace file.

## 1. Debugging Hypothesis Loop

```markdown
=== Hypothesis {N} ===
Observation: {error, symptom, reproduction condition}
Hypothesis: {suspected cause}
Verification method: {command, targeted file inspection, or runtime check}
Verification result: {actual evidence}
Verdict: Correct / Incorrect
Next action: {fix, new hypothesis, or escalate}
```

After three incorrect hypotheses on the same issue, stop and ask for review or a different diagnostic path.

## 2. Architecture Decision

```markdown
=== Decision: {choice} ===

Options:
- A: {option}
- B: {option}
- C: {option}

Criteria:
| Criterion | A | B | C | Weight |
|-----------|---|---|---|--------|
| Reliability | | | | H |
| Simplicity | | | | H |
| Existing pattern fit | | | | H |
| Testability | | | | M |

Conclusion: {selected option}
Reason: {short rationale}
Trade-off: {accepted downside}
Verification: {Expected: PASS command}
```

## 3. Execution Flow Trace

```markdown
=== Execution Flow Trace ===
1. Entry: {file:function} with {input}
2. Call: {file:function} passes {value}
3. Processing: {file:function} transforms {value}
4. Failure point: {file:function}
   Expected: {expected}
   Actual: {actual}
   Cause: {evidence-backed cause}
5. Verification: {command or check}
```

## 4. Refactoring Judgment

```markdown
=== Refactoring Judgment ===
Current issue: {problem}
Relation to task: Direct / Indirect / Unrelated
Risk of changing now: Low / Medium / High
Decision: Fix now / Record only / Ask user
Reason: {one or two lines}
```

## 5. Performance Bottleneck Analysis

```markdown
=== Performance Bottleneck Analysis ===
Measurement source: {benchmark, log, trace, estimate}
Total time: {value}
Largest cost: {step}
Cause: {evidence}
Candidate fix: {change}
Expected improvement: {before -> after}
Verification: {command}
```

## 6. Exploration Decision

Use when the same issue repeatedly fails or alternative approaches are explicitly requested.

```markdown
=== Exploration Decision ===
Problem: {what needs to be solved}
Current evidence: {score, failing test, review finding}
Attempts so far: {count and outcomes}

Hypothesis A:
  Predicted impact:
  Confidence:
  Scope:

Hypothesis B:
  Predicted impact:
  Confidence:
  Scope:

Selection rule: {score, test result, simplicity, or user criterion}
Fallback: {when to stop and ask}
```

## Usage Rules

1. Use templates for Complex tasks and repeated failures.
2. Fill blanks with evidence from `grep`, targeted file inspection, tests, logs, or reviewed plans.
3. Do not keep private scratch reasoning as durable state unless the plan or user asks for a trace artifact.
4. If required fields cannot be filled, gather evidence before acting.
