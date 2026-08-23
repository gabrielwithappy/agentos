---
name: spike
description: Run short throwaway experiments to validate technical uncertainty.
license: MIT
source: Hermes spike reference, adapted for AgentOS catalog use.
---

# Spike

Use this skill when the user wants to validate feasibility before committing to a full implementation.

Spikes are disposable experiments with a clear question, observable result, and written verdict.

## Workflow

1. Frame 1-3 feasibility questions in Given/When/Then form.
2. Pick the riskiest question first.
3. Research only enough to choose an approach.
4. Build the smallest experiment that can answer the question.
5. Record the verdict: proceed, change approach, defer, or stop.

## Boundaries

- Do not ship spike code as production code without review.
- Do not expand a spike into a full feature.
- If the answer is available by reading local code or docs, inspect first instead of building an experiment.
