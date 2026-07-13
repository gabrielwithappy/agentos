# Deck Planning Stage

Adapted from upstream `gpt-slide-plan`.

Goal: build the deck logic before writing page prompts. Use:
- `DESIGN.md` as the visual constraint system
- the user prompt as the objective and audience
- user files as the evidence and content pool

Create a persuasive, logically ordered, evidence-backed slide sequence that is
compatible with the extracted design system.

Plan by story logic, not upload order. Consider:
- context or framing
- problem, opportunity, or thesis
- key insight
- supporting evidence
- implications
- recommendation, solution, roadmap, or next step
- closing ask or summary

For every planned slide, decide:
- story role
- single main message
- supporting evidence
- why it belongs in this order
- layout family from `DESIGN.md`
- page family: title, body, end, or appendix
- header, body, and footer responsibilities
- whether prose, chart, table, metric cards, infographic, or diagram is best

Return valid JSON only. The top-level object must include:
- `deck_meta`
- `design_dependency`
- `slides`
- `evidence_map`
- `open_questions`

Do not write page-level generation prompts in this stage.
