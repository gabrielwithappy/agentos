---
name: codex-imagegen-2
description: Generate and edit images using OpenAI Codex OAuth and ChatGPT Plus/Pro subscription. Bypass API limits and per-image billing.
---

# codex-imagegen-2-skill-for-kimi

A CLI skill for image generation using OpenAI's Codex OAuth proxy. Generate images from text prompts or transform existing images — all via your ChatGPT Plus/Pro subscription.

## Requirements

- **Node.js** >= 18
- **ChatGPT Plus or Pro** subscription
- **openai-oauth** installed globally (`npm install -g openai-oauth`)

## Prerequisites

1. Log in to Codex CLI to create an OAuth session:
   ```bash
   npx @openai/codex login
   ```
   This creates `~/.codex/auth.json` which the skill uses for authentication.

2. The skill auto-starts an OAuth proxy on port `10531` when needed.

## Standalone Scripts

```bash
cd .agents/skills/codex-imagegen-2-skill-for-kimi/scripts/

# Generate from text
node generate.js --prompt "a cyberpunk city at night" --quality high --size 1024x1024 --n 2

# Edit an existing image
node edit.js --input photo.png --prompt "turn into watercolor painting" --quality high --out result.png

# Verify a generated image
node verify.js --input result.png --verbose
```
