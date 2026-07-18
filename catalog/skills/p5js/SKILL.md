---
name: p5js
description: Create p5.js generative art, interactive sketches, and canvas demos.
license: MIT
source: Hermes p5js reference, adapted for AgentOS catalog use.
---

# p5.js

Use this skill when the user asks for p5.js, generative art, creative coding, interactive sketches, shaders, canvas visuals, or browser-based motion studies.

Default output is a self-contained HTML file using a pinned p5.js CDN version unless the existing repo already has a frontend build system.

## Workflow

1. Define the concept, interaction, palette, and canvas size.
2. Build a complete sketch with stable first paint.
3. Add mouse, keyboard, or time-based interaction only when useful.
4. Keep dependencies explicit and pinned.
5. Verify that the canvas renders and is not blank.

## Boundaries

- Do not use p5.js for ordinary app UI.
- Do not require audio, camera, or external files unless the user supplied them or approved the dependency.
- For production 3D, prefer Three.js when the application needs a true 3D scene.
