---
name: claude-design
description: Design one-off HTML artifacts, prototypes, decks, and component studies.
license: MIT
source: Hermes claude-design reference, adapted for AgentOS catalog use.
---

# Claude Design

Use this skill when the user asks for a one-off designed HTML artifact, landing page, prototype, deck-like visual, component lab, or motion study.

This is a CLI/API adaptation. Ignore hosted-only Claude Design concepts such as preview panes, callbacks, special artifact tools, and hidden verifier agents. Build with the tools available in the current workspace.

## Workflow

1. Clarify the audience, job to be done, content hierarchy, and visual references when needed.
2. Choose the real implementation medium: existing app stack when in a repo, otherwise standalone HTML.
3. Produce a polished artifact with responsive layout and stable dimensions.
4. Verify locally with the available browser or static checks.
5. Report the file path and verification performed.

## Boundaries

- Use `popular-web-designs` when the user asks to match a known brand style.
- Use `design-md` when the deliverable is a design-token spec.
- Do not create marketing copy instead of the requested usable artifact.
