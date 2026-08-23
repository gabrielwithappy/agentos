---
name: design-md
description: Author, review, and export DESIGN.md design-token specifications.
license: MIT
source: Hermes design-md reference, adapted for AgentOS catalog use.
---

# DESIGN.md

Use this skill when the user asks for a `DESIGN.md`, design tokens, a reusable visual identity spec, accessibility review of tokens, or a machine-readable design-system document.

## Workflow

1. Identify brand intent, surfaces, typography, colors, spacing, radius, and component tokens.
2. Write YAML front matter for normative token values.
3. Add Markdown rationale explaining how agents should apply the tokens.
4. Check contrast-sensitive pairs manually or with available tooling.
5. If the user asks for export, generate Tailwind or DTCG-style JSON only from the reviewed tokens.

## Boundary

Use this for durable design specifications. For a one-off visual HTML artifact, use `claude-design`; for a known brand visual vocabulary, use `popular-web-designs`.
