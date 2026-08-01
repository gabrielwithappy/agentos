# Release checklist

1. Run `python3 scripts/security/scan-public-boundary.py --stage-allowlisted --require-staged-equals-allowlist`.
2. Run `bash scripts/verify-clean-install.sh` and `bash scripts/verify-public-test-suite.sh`.
3. Verify the exact staged tree, Git identity, and required CI before release.
4. Do not publish credentials, profiles, runtime data, or private sync procedures.
