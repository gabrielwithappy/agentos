---
name: sketch
description: Produce quick disposable HTML mockup variants for comparison.
license: MIT
source: Hermes sketch reference, adapted for AgentOS catalog use.
---

# Sketch

Use this skill when the user wants to compare possible UI directions before committing to production implementation.

The output is disposable: two or three small HTML variants or a concise comparison artifact. It is not a substitute for production code.

## Workflow

1. Identify the core action and intended feel.
2. Pick one variation axis such as density, emphasis, layout, or aesthetic.
3. Create 2-3 distinct variants.
4. Label each variant by design stance, not by color.
5. Summarize tradeoffs and recommend one direction.

## Boundaries

- If the user wants the final production UI, build in the repo's actual stack.
- If the user wants a polished standalone artifact, use `claude-design`.
- If the user wants a diagram, use `architecture-diagram`.
