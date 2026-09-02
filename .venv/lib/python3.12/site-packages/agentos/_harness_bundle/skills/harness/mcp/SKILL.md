---
name: mcp
description: >
  Use for all Model Context Protocol (MCP) server management tasks:
  - "browse MCPs": Discover available servers from the catalog
  - "install MCP <name>": Configure a new server (e.g. github, postgres)
  - "list MCPs": Show currently installed/configured servers
  - "remove MCP <name>": Uninstall or delete a server configuration
  Handles settings.json updates, credential collection, and catalog lookups.
model: sonnet
---

# MCP Management - Unified Toolset

This skill provides a unified interface for managing Model Context Protocol (MCP) servers. It consolidates the previously fragmented mcp-browse, mcp-install, mcp-list, and mcp-remove skills into a single workflow.

## When to use

- Browsing the curated catalog of MCP servers for discovery
- Installing and configuring new MCP servers with credentials
- Checking the status/configuration of already installed servers
- Removing or disabling MCP server configurations

## 1. Browse Catalog

Display the curated MCP server catalog grouped by category.

### Steps
1. **Locate Catalog**: Check `.claude/plugins/mcp-installer/data/mcp-catalog.json` or `.agents/skills/harness/mcp/resources/mcp-catalog.json`.
2. **Display**: Render a table grouped by category (Dev Tools, Productivity, Data, etc.).
3. **Filter**: If the user names a category, show only that section.

## 2. List Installed Servers

Show all MCP servers currently configured in `.claude/settings.json`.

### Steps
1. **Read `settings.json`**: Extract `mcpServers` object.
2. **Enrich**: Cross-reference with the catalog to show labels and descriptions.
3. **Display**: Render table with [Key | Label | Source | Command].

## 3. Install/Configure Server

Add a new MCP server configuration.

### Steps
1. **Identify**: Extract server name, match against catalog.
2. **Collect Env**: If `requires_env` is present, prompt user for each credential individually (e.g., GITHUB_TOKEN).
3. **Write**: Atomic write to `.claude/settings.json`. Mask sensitive inputs if displaying back to user.
4. **Confirm**: Advise user to restart the agent (or run `claude mcp list`) to activate.

## 4. Remove Server

Remove a configuration from `.claude/settings.json`.

### Steps
1. **Identify**: Exact or substring match against installed keys.
2. **Confirm**: Show the config block to be deleted and ask for "yes/no".
3. **Write**: Update `settings.json` and confirm removal.

## Platform Note

While this skill primarily manages `.claude/settings.json` (the standard for Claude Code), it serves as the logical SSOT for MCP configuration within the Agent Harness. Multi-platform adapters may translate this file to other formats (e.g. for Antigravity or Gemini) as needed.

## Common Pitfalls

- **Missing Catalog**: If `mcp-catalog.json` is missing, fallback to listing only the basic GitHub/SQLite examples.
- **Malformed JSON**: Always backup `settings.json` before writing and use atomic replace.
- **Credential Exposure**: Never output raw tokens in logs or final replies — use `***` masking.
