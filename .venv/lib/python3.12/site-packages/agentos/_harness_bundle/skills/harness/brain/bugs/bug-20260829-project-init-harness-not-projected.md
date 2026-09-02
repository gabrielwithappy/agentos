# Bug: `proj init` did not project harness resources

- **Observed**: `agentos proj init` was rejected, and the packaged CLI had no bundled harness source to project into a target project.
- **Root cause**: The CLI registered only the `project` command; `_harness_sources()` only searched the source checkout, while the package build included neither harness resource tree.
- **Fix**: Register `proj` as an alias, include harness agents and skills in the package bundle, and use that bundle when the source checkout is unavailable.
- **Regression coverage**: `test_proj_is_project_init_alias` plus the existing project-init harness projection test.
- **Verification**: Focused tests passed; package build execution remains environment-blocked because neither `build` nor `hatchling` is installed in `.venv`.
