# Optional Image Generation Stage

Adapted from upstream `gpt-slide-generate`.

Use this stage only when the user asks for final slide images and the active
runtime has image generation available.

Inputs:
- `DESIGN.md`
- `slide_prompts.json`

Workflow:
1. Read `DESIGN.md`.
2. Read `slide_prompts.json` and confirm slide count and page order.
3. Generate slides one at a time in slide-number order.
4. Inspect each generated image.
5. Save accepted outputs into the workspace as `page_<n>.png`.
6. Report saved paths.

If image generation is unavailable:
- do not install packages
- do not write a custom SDK runner
- stop after `slide_prompts.json`
- tell the user that image generation is unavailable in this runtime

Never leave final project assets only in a tool cache. When images are
generated, copy or save the accepted files into the project workspace.
