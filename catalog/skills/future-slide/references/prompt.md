# Page Prompt Stage

Adapted from upstream `gpt-slide-prompt`.

Goal: convert `DESIGN.md` and approved `slide_plan.json` into detailed
page-level prompts in `slide_prompts.json`.

Preserve:
- the extracted visual system
- the approved narrative order
- factual evidence from user files
- a controlled body-slide family
- header, body, and footer zoning

For each slide prompt, include:
- slide number
- slide role
- page family
- slide title
- layout family
- objective
- narrative function
- visual intent
- content blocks
- layout instructions
- design constraints
- content constraints
- generator notes

Avoid vague instructions such as "make it modern." Specify structure, placement,
hierarchy, density, chart/table behavior, icon role, anti-patterns, and what
must not be included.

Return valid JSON only with a `slides` array ordered by slide number.
