#!/usr/bin/env python3
import json
import re
import sys
from typing import Any, Optional


def _load_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _decode_tool_response(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _extract_exit_code(response: Any) -> Optional[int]:
    if isinstance(response, dict):
        for key in ("exit_code", "exitCode"):
            value = response.get(key)
            if isinstance(value, int):
                return value
        nested = response.get("output")
        if isinstance(nested, dict):
            for key in ("exit_code", "exitCode"):
                value = nested.get(key)
                if isinstance(value, int):
                    return value
    return None


def main() -> int:
    payload = _load_payload()
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "")
    response = _decode_tool_response(payload.get("tool_response"))
    exit_code = _extract_exit_code(response)

    if exit_code not in (None, 0):
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        f"Bash command failed with exit code {exit_code}. "
                        "Read stdout/stderr carefully, do not assume success, "
                        "fix or escalate, then rerun the relevant verification."
                    ),
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            "A Bash command just failed. Stay in evidence-first mode: "
                            "inspect the full output, explain the actual failure, and "
                            "avoid claiming success until a fresh rerun passes."
                        ),
                    },
                }
            )
        )
        return 0

    completion_actions = re.compile(
        r"\b(git\s+commit|git\s+push|gh\s+pr\s+(create|merge)|npm\s+publish|cargo\s+publish)\b"
    )
    if completion_actions.search(command):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            "You just ran a completion-adjacent command. Follow the "
                            "verification-before-completion rule: only describe success "
                            "with fresh command evidence, and state clearly if verification "
                            "was not run in this turn."
                        ),
                    }
                }
            )
        )
        return 0

    review_actions = re.compile(r"\baha\s+(project\s+plan\s+review|plans\s+review)\b")
    if review_actions.search(command):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            "Gate 2 review evidence changed. Refresh lifecycle state and verify "
                            "the active plan only reports reviewed=true when independent review "
                            "artifacts are valid."
                        ),
                    }
                }
            )
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
