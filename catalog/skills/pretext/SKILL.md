---
name: pretext
description: Build browser demos with text layout, typography, and ASCII-like motion.
license: MIT
source: Hermes pretext reference, adapted for AHA catalog use.
---

# Pretext Creative Demos

Use this skill when the user asks for kinetic typography, text-as-geometry, ASCII-like browser demos, prose flowing around shapes, or creative text layout.

Default output is a self-contained HTML file. Use `@chenglou/pretext` only when the user needs its line measurement behavior; otherwise regular canvas or CSS may be simpler.

## Workflow

1. Choose a meaningful source text.
2. Define the visual interaction or animation.
3. Build a canvas or HTML demo with readable typography.
4. Make the first frame visually complete.
5. Verify that the demo renders without blank frames.

## Boundaries

- Do not use this for ordinary rich text editors.
- Do not fetch remote text without user approval.
- Keep the demo original and avoid decorative-only clutter.
