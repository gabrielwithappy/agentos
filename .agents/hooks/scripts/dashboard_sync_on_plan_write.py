#!/usr/bin/env python3
"""PostToolUse hook: after Claude Code edits an active exec-plan file,
run `plan_lifecycle.py refresh` so the board/registry (and, best-effort,
the GitHub dashboard) stay in sync without a manual command. Fail-open:
any error here must never block the session, matching
`post_tool_use_review.py`'s contract.

`root` is passed as argv[1] by the shell wrapper in `.claude/settings.json`
(the same `${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}`
resolution every other hook in this repo already uses) rather than
re-derived from the PostToolUse payload's `cwd` field, which may be
empty or relative depending on invocation context."""
import json
import subprocess
import sys
from pathlib import Path

ACTIVE_PREFIX = ".agentos/project/exec-plans/active/"


def _load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _touched_paths(payload: dict) -> list[str]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    paths = []
    if "file_path" in tool_input:
        paths.append(str(tool_input["file_path"]))
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict) and "file_path" in edit:
                paths.append(str(edit["file_path"]))
    return paths


def main() -> int:
    payload = _load_payload()
    if payload.get("tool_name") not in ("Edit", "Write", "MultiEdit"):
        return 0

    touched = _touched_paths(payload)
    if not any(ACTIVE_PREFIX in path.replace("\\", "/") for path in touched):
        return 0

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    script = root / ".agents" / "skills" / "harness" / "writing-plans" / "scripts" / "plan_lifecycle.py"
    if not script.is_file():
        return 0
    try:
        subprocess.run(
            [sys.executable, str(script), "refresh"],
            cwd=root,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
