---
name: baoyu-comic
description: Plan educational comics, biography comics, and tutorial comic prompts.
license: MIT
source: Baoyu/JimLiu comic workflow via Hermes, adapted for AHA catalog use.
---

# Knowledge Comic

Use this skill when the user asks for an educational comic, biography comic, tutorial comic, storyboard, or panel-by-panel visual explanation.

This AHA catalog version is planning and prompt oriented. It does not assume a specific image-generation service. If image generation is needed, use the image tool available in the current runtime and keep generated assets under the user's requested path.

## Workflow

1. Extract the teaching goal, target audience, tone, language, and page count.
2. Define recurring characters or visual motifs in text.
3. Build a storyboard with panel count, narration, dialogue, and visual action.
4. Create image prompts per page or panel if the user wants generated images.
5. Keep a `characters.md` and `storyboard.md` when producing multi-page work.

## Constraints

- Do not claim reference images can be passed to an image model unless the current runtime supports that.
- Keep factual educational content grounded in supplied material or verified sources.
- Ask before using a real person's likeness for generated imagery.
