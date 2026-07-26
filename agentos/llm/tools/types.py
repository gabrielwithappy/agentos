from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolExecutionResult:
    """Outcome of one tool execution, ready to become a `role="tool"`
    `ConversationMessage` text. `blocked` mirrors `bootstrap.ContextFile`'s
    `skipped`/`blocked` split: a skip/error means the file couldn't be
    produced; a block means it was read fine but content matched a threat
    pattern, so `content` already holds a `[BLOCKED: ...]` marker instead of
    the raw text."""

    content: str
    is_error: bool = False
    truncated: bool = False
    blocked: bool = False


__all__ = ["ToolExecutionResult"]
