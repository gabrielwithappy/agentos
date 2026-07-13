---
name: ascii-art
description: Create text banners, boxes, and small ASCII/Unicode art.
license: MIT
source: Hermes ascii-art reference, adapted for AHA catalog use.
---

# ASCII Art

Use this skill when the user asks for ASCII art, terminal banners, text logos, boxes, or small Unicode text illustrations.

Prefer local commands when available. Do not call a remote ASCII API unless the user explicitly wants an online source and network use is acceptable.

## Workflow

1. Clarify the target text, width, and output context when they are not obvious.
2. For banners, try local `figlet` or `python3 -m pyfiglet` if installed.
3. For documentation callouts, use simple boxed text that stays readable in monospace.
4. Keep line width appropriate for the target medium.
5. Provide plain text output and avoid hidden control characters.

## Safety

- Do not install packages without user approval.
- Do not use offensive generated text or misleading terminal prompts.
- Avoid ANSI color unless the user asks for terminal styling.
