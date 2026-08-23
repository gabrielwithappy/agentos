---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, applications, prototypes, or visually strong product UI. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Working Model

Before coding, write three short anchors for yourself:
- **Visual thesis**: one sentence describing the intended mood, material, and energy
- **Content plan**: the primary sections or surfaces the user should encounter
- **Interaction thesis**: 2-3 motion or interaction ideas that improve hierarchy and feel

Start with composition and hierarchy before component count. Each section should have one main job, one dominant idea, and one primary takeaway or action.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Composition Defaults

- Prefer layout, spacing, alignment, scale, and contrast before adding extra chrome.
- Use cards only when the card itself is the interaction. Do not default to dashboard-card mosaics.
- For branded or marketing-oriented surfaces, make the brand or product unmistakable in the first screen.
- Prefer one strong visual anchor over several weak decorative ideas.
- Keep copy short enough to scan quickly. One strong line usually beats three average ones.
- Use at most two typefaces unless there is a strong reason to introduce more.

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

## Surface Guidance

### Visually Led Pages

- Treat the first viewport like a poster, not a document.
- Prefer a full-bleed hero or one dominant visual plane when the work depends on brand, atmosphere, or imagery.
- Keep the text column narrow enough to read at a glance and anchor it in a visually calm area.
- Avoid hero cards, stat strips, logo clouds, and decorative UI clutter unless the brief clearly calls for them.

### Product And Operational UI

- Default to utility copy over marketing copy.
- Start with the working surface itself: table, filters, task context, status, KPI, chart, or editor.
- Section labels should tell the user what they can inspect, operate, or decide.
- Use calm hierarchy, strong typography, and minimal chrome.
- If a panel still works after removing the card treatment, remove the card treatment.

### Motion

- Ship a small number of intentional motions instead of many ornamental ones.
- A good default is:
  - one entrance sequence
  - one scroll-linked, sticky, or depth effect
  - one hover, reveal, or layout transition
- Remove motion that does not sharpen hierarchy, affordance, or atmosphere.

## Litmus Checks

- Is the first screen unmistakably about this product, brand, or working surface?
- Does each section have one clear responsibility?
- Is there one strong visual anchor rather than several weak ones?
- Would the layout still feel strong if the decorative shadows were removed?
- If this is product UI, can someone understand it by scanning headings, labels, and numbers?

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
