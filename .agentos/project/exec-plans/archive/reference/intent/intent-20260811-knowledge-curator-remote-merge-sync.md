# Intent Sheet: Knowledge Curator Remote Merge Sync

**Date:** 2026-08-11
**Requester intent summary:** Let one knowledge repository be safely used from multiple locations by synchronizing through a shared Git remote.

## Hypothesis

> If knowledge-curator fetches remote history, performs only a safe Git merge, and pushes the resulting local commit under an explicitly enabled policy, users can share one knowledge base across locations without manual Git plumbing.

## Plan Quality Gate

> "After executing the plan, do the following conditions pass through automated grading?"

- [ ] Run: `python3 -m pytest tests/test_knowledge_skill.py tests/test_knowledge_remote_sync.py tests/test_knowledge_git_security.py tests/test_knowledge_okf_starter.py tests/test_okf_bundle_validation.py -q` Expected: exit `0`, including an integration test that creates divergent commits in two local clones, then verifies `sync` fetches, merges or fast-forwards, and pushes the merged history.
- [ ] Run: `python3 -S catalog/skills/knowledge-curator/scripts/knowledge.py --help` Expected: exit `0`, with JSON behavior and CLI help remaining available.

## Scope Fence

- Included: Extend the standalone knowledge-curator CLI with remote fetch, safe fast-forward or non-conflicting merge, and push; add an explicit initialization-time remote-sync/auto-push policy; make successful `backup` automatically publish only when that policy is enabled; report actionable JSON recovery guidance for remote, merge, and push failures.
- Included: Preserve credential-free remote URLs and Git's existing credential helper boundary.
- Excluded: GitHub API integration, browser OAuth, credential collection or storage, force-push, automatic conflict resolution, rebase, stash, reset/clean, and CI/GitHub Actions integration.
- Excluded: Changing unrelated AgentOS CLI behavior or user-owned changes already present in this branch.

## Technical Constraints

- Keep the package portable and stdlib-only.
- All commands continue to emit one JSON object on stdout and avoid credential-bearing output.
- Remote synchronization must stop before changing knowledge files when Git reports a merge conflict or another Git operation is in progress.
- Auto-push is opt-in and may run only after a successful local `backup` commit and validation/policy checks.

## Worktree Decision

- Required: No.
- Reason: The requester asked to retain existing changes, so a dedicated `feature/knowledge-curator-remote-merge-sync` branch is created from the current preserved work before this plan's review or implementation resumes.
- Ownership: Work only on `feature/knowledge-curator-remote-merge-sync`; retain all pre-existing working-tree modifications without reverting or overwriting them.

## Priority

- Production-level safety: remote and branch checks, conflict stop-and-recovery guidance, synchronization status, and auto-push failure handling are in scope.
