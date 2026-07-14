# agentOS

agentOS installs a portable agentcore. Profiles, routines, knowledge, Discord,
and runtime data are not created by the initial install.

Prerequisites: `bash`, `git`, and `python3`.

```bash
git clone https://github.com/gabrielwithappy/agentOS.git
cd agentOS
bash setup.sh
bash scripts/verify-public-test-suite.sh
```

Each command ends with `PASS`. If a check fails, fix the reported condition and
run the same command again.

Choose the right product and follow its install, verification, and retry path in
[Getting started](docs/getting-started.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
