# Antigravity (agy) Hook Adapter

This directory contains the AgentOS hook adapter for the Antigravity CLI (`agy`).

Since Antigravity does not use static JSON configuration for hooks (unlike Claude Code and Codex), it relies on a Plugin architecture. 

## Structure
- `plugin.json`: Antigravity plugin manifest.
- `main.py`: The Python entrypoint that intercepts Antigravity tool calls and routes them to the common AgentOS SSOT scripts located in `.agents/hooks/scripts/`.

## Installation
To enable this hook bridge in Antigravity, run:
```bash
agy plugin install .agents/hooks/adapters/agy
agy plugin enable agentos-unified-hooks
```
