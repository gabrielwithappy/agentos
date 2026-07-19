from __future__ import annotations

import os
import re
from typing import Any

REDACTED = "[REDACTED]"

_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(token\s*[:=]\s*)[^\s,;]+"),
)


def sensitive_values() -> list[str]:
    values: list[str] = []
    sentinel = os.environ.get("AGENTOS_TEST_SECRET")
    if sentinel:
        values.append(sentinel)
    return values


def redact_text(value: str) -> str:
    redacted = value
    for secret in sensitive_values():
        if secret:
            redacted = redacted.replace(secret, REDACTED)
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
    return redacted


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize(item) for item in value)
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    return value
