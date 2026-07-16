# agentOS

agentOS installs a portable agentcore. Profiles, routines, knowledge, Discord,
and runtime data are not created by the initial install.

Canonical slug: `agentos`.
Display name: `agentOS`.

Prerequisites: `bash`, `git`, and `python3`.

```bash
git clone https://github.com/gabrielwithappy/agentos.git
cd agentos
bash setup.sh
bash scripts/verify-public-test-suite.sh
```

Each command ends with `PASS`. If a check fails, fix the reported condition and
run the same command again.

For detailed information on the installation process and future migration plans, please see
[Getting started](docs/getting-started.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
