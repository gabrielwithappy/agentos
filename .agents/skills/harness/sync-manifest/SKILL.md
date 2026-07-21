---
name: sync-manifest
description: Synchronize the harness asset manifests (agents, skills) to ensure integrity (P1). Use after adding/removing harness components.
model: sonnet
---

# Sync Manifest Skill

Use this skill whenever you modify the structure of the `.agents/` directory (adding new agents or skills). It ensures the `_version.json` manifests are up-to-date, preventing integrity failures.

## Harness Principles (MANDATORY)

1. **P1: Reliability**: This skill is a core reliability tool. Never skip manifest syncing after an architectural change.
2. **Authorized Architects Only**: Only agents with `harness-architect` or `antigravity` roles should use this skill to *update* the manifest. All agents can use it to *check* integrity.

## Usage

### 1. Check Integrity (--check)

Checks if the current filesystem matches the recorded manifest.
```bash
./.agents/harness/scripts/sync-manifest.sh --check
```

### 2. Update Manifest (--update)

Updates the manifest to reflect the current filesystem. (Requires authorized role).
```bash
./.agents/harness/scripts/sync-manifest.sh --update <agent-id>
```

## Integration

- **Trigger**: Automatic at the end of a successful `Evolution Proposal` implementation.
- **Fail Check**: If `--check` fails, the agent MUST run `--update` or escalate if changes were unauthorized.
