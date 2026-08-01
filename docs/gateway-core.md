# AgentOS Gateway Core

Gateway Core adds a local managed execution path without replacing direct vendor CLI usage. Direct `codex`, `claude`, and `agentos run --once` paths continue to work.

Gateway state lives under `AGENTOS_HOME/gateway/gateway.db`. It stores run status, sanitized events, and enough metadata to recover after a process restart. Credentials, raw provider stderr, and full environment dumps are not stored.

## First Use

```bash
agentos project init --path .
agentos gateway doctor --provider mock
agentos gateway submit --provider mock "summarize this project"
agentos gateway worker --once
agentos gateway list
agentos gateway status RUN_ID
agentos gateway events RUN_ID
```

`submit` requires a `.git` checkout or an initialized AgentOS project marker. If no preferred provider is saved, pass `--provider`; Gateway does not silently default to `mock`.

## Retry And Cancel

Queued runs can be cancelled:

```bash
agentos gateway cancel RUN_ID
```

Running cancellation is intentionally rejected in Gateway Core MVP. Failed or interrupted runs can be retried:

```bash
agentos gateway retry RUN_ID "replacement prompt" --yes
```

Runs created with `--record-policy metadata` purge the prompt at terminal state, so retry needs a replacement prompt. Runs created with `--record-policy full` can reuse the stored prompt.

## Prune

Terminal run data is retained until the user previews and confirms deletion:

```bash
agentos gateway prune --before 2026-09-01T00:00:00Z
agentos gateway prune --before 2026-09-01T00:00:00Z --yes
```

Active runs are never pruned by this command.
