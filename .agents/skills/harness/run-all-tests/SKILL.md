---
name: run-all-tests
description: Run the full harness test suite (integrity check, loop tests, state logic) to ensure the Cognitive OS is stable. Use before pushing harness changes.
model: sonnet
---

# Run All Tests Skill

Use this skill to verify that the Agent Harness is 100% functional. It runs both the structural integrity checks and the logic tests (Pytest).

## Harness Principles (MANDATORY)

1. **P1: Reliability**: Never commit harness changes without a PASSing `run-all-tests` skill execution.
2. **Standardization**: All tests are unified under this skill to prevent tool drift.

## Usage

Runs both the bash integrity check and the python pytest suite.
```bash
./.agents/harness/tests/run_all_tests.sh
```

## Integration

- **Trigger**: Mandatory before any PR/Commit involving the `.agents/` directory.
- **Fail Check**: If any test fails, follow Rule 2 (Repeat Error Protocol) or escalate via Rule 1.
