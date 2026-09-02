# Context Budget Management

The context window is finite. Load only what the task needs.

## Core Rules

1. Prefer `find`, `grep`, and file lists before opening files.
2. Use targeted file inspection instead of reading large files wholesale.
3. Do not re-read files unless the content may have changed.
4. Keep durable facts in `HISTORY.md`, reviewed plans, or concise trace files when needed.
5. Stop loading context once implementation and verification are unblocked.

## File Reading Strategy

```text
Good:
- grep -RIn "function_name" src tests
- sed -n '40,120p' path/to/file
- find path -type f | sort

Avoid:
- reading a large file without a target
- opening every related resource just in case
- duplicating context already captured in the plan
```

## Large File Strategy

1. Use `grep -RIn` to find symbols, tests, and call sites.
2. Read imports and nearby definitions first.
3. Open only the function, class, or section being changed.
4. Read tests after identifying expected behavior.

## Resource Loading Budget

| Resource Type | Load Rule |
|---------------|-----------|
| `SKILL.md` | Selected skill only |
| Brain resource | Only when triggered by `context-loading.md` |
| Vendor guide | Only the current runtime's vendor guide |
| Tests | Focused patterns first, broader suite before completion |

## Overflow Symptoms

| Symptom | Response |
|---------|----------|
| Re-reading the same file | Summarize the needed fact and continue |
| Losing task direction | Re-check the reviewed plan or success criteria |
| Too many candidate files | Narrow with `grep` patterns and ownership boundaries |
