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
uv tool install agentos
agentos --help
cd /path/to/your-project && agentos setup
agentos doctor
agentos run --once "hello from AgentOS"
agentos hook list
```

Checkout 개발 검증은 source repository에서 `bash scripts/verify-public-test-suite.sh`를 실행합니다. `uv run ...`은 checkout 개발 흐름에만 사용하며, 전역 설치 후 일반 프로젝트에서는 bare `agentos` 명령을 사용합니다.

Each command ends with `PASS`. If a check fails, fix the reported condition and
run the same command again.

For automation, use `agentos run --once "prompt" --json`. For detailed command
behavior, session handling, hooks, recovery, and the raw token privacy boundary,
see [CLI reference](docs/cli-reference.md) and
[Getting started](docs/getting-started.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
