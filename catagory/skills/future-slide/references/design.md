# Design Extraction Stage

Adapted from upstream `gpt-slide-design`.

Goal: convert one or more reference slide images, deck exports, or structured
report PDFs into a reusable `DESIGN.md`.

Analyze design, not content. The output should describe how the slide system is
constructed so new slides can reuse it.

Inspect in this order:
- composition and dominant zones
- typography hierarchy and casing
- color system and contrast behavior
- grid, margins, density, and spacing
- title, body, footer, source-note, chart, table, and callout components
- data visualization language
- imagery, icon, shape, panel, and divider treatment
- repeated rules and anti-patterns

Separate:
- Observed from the reference
- Inferred but not directly visible

Never invent brand names, exact fonts, exact colors, or deck narrative from a
single image. If exact values are uncertain, mark them approximate.

Required `DESIGN.md` sections:
1. Design intent
2. Color system
3. Typography system
4. Layout families
5. Grid, alignment, and spacing
6. Components
7. Data visualization language
8. Imagery and graphic treatment
9. Slide-system rules
10. Anti-patterns

Use `assets/DESIGN_TEMPLATE.md` as the starting structure.
