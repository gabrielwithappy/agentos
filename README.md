# agentOS

agentOS installs an independent Python CLI for local agent workflows. Profiles,
routines, knowledge, Discord, and runtime data are not created by the initial
install.

Canonical slug: `agentos`.
Display name: `agentOS`.

Prerequisites: `bash`, `git`, `python3`, and `uv`.

```bash
git clone https://github.com/gabrielwithappy/agentos.git
cd agentos
uv run agentos setup
uv run agentos doctor
uv run agentos run --once "hello from AgentOS"
uv run agentos hook list
bash scripts/verify-public-test-suite.sh
```

Each command ends with `PASS`. If a check fails, fix the reported condition and
run the same command again.

For automation, use `agentos run --once "prompt" --json`. For detailed command
behavior, session handling, hooks, recovery, and the raw token privacy boundary,
see [CLI reference](docs/cli-reference.md) and
[Getting started](docs/getting-started.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
