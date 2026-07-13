# Difficulty Assessment and Protocol Depth

Assess task difficulty before choosing planning and verification depth.

## Levels

| Level | Signals | Expected Handling |
|-------|---------|-------------------|
| Simple | Single file, clear requirement, existing pattern | Implement directly and verify narrowly |
| Medium | 2-3 files, some decisions, moderate risk | Brief plan, targeted file inspection, focused tests |
| Complex | 4+ files, architecture decisions, protected paths, cross-module behavior | Reviewed plan, broader inspection, explicit verification gates |

## Protocol Branching

### Simple

1. Inspect only the target file or symbol.
2. Make the smallest change.
3. Run the nearest verification command.

### Medium

1. Inspect related files with `grep` and targeted file inspection.
2. State a short plan.
3. Implement and run focused verification.

### Complex

1. Read the relevant domain section in `HISTORY.md` or `lessons-learned.md`.
2. Inspect structure with `find`, `grep`, file lists, and targeted file inspection.
3. Create or follow a reviewed plan with Expected: PASS gates.
4. Verify with focused and broader tests.

## Reassessment

- If Simple grows beyond one file or reveals uncertainty, upgrade to Medium.
- If Medium touches protected paths or architecture, upgrade to Complex.
- If Complex becomes trivial after inspection, finish with the smallest verified change.
