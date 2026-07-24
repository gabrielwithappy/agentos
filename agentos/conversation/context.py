from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentos.conversation.types import ConversationMessage, ConversationState

_ROLE_ORDER = {"system": 0, "user": 1, "assistant": 2, "tool": 3}


@dataclass(frozen=True)
class BuiltContext:
    """Deterministic provider-bound context for one turn.

    `messages` preserves branch prefix order with trusted system messages
    pinned first, then chronological system/user/assistant/tool history,
    always ending in the newest user message. `trimmed` records how many
    older non-pinned messages were dropped to satisfy `max_messages`, so
    trimming is observable rather than a silent truncation.
    """

    messages: list[ConversationMessage]
    trimmed: int
    max_messages: int | None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "message_count": len(self.messages),
            "trimmed": self.trimmed,
            "max_messages": self.max_messages,
        }


def build_context(
    state: ConversationState,
    branch_id: str | None = None,
    *,
    max_messages: int | None = None,
) -> BuiltContext:
    """Build deterministic provider context for `branch_id` (default: active branch).

    Ordering: trusted `system` messages first (in original chain order),
    then the remaining chain in chronological order. The newest user
    message is always the last message and is never trimmed; pending tool
    results paired with the newest user turn are protected the same way
    since trimming only removes from the oldest non-pinned end.
    """
    resolved_branch = branch_id or state.active_branch_id
    chain = state.branch_messages(resolved_branch)

    if not chain:
        return BuiltContext(messages=[], trimmed=0, max_messages=max_messages)

    trusted_system = [m for m in chain if m.is_trusted_system()]
    rest = [m for m in chain if not m.is_trusted_system()]

    newest_user_index = _last_user_index(rest)
    pinned_tail: list[ConversationMessage] = []
    trimmable: list[ConversationMessage] = rest
    if newest_user_index is not None:
        pinned_tail = rest[newest_user_index:]
        trimmable = rest[:newest_user_index]

    trimmed_count = 0
    if max_messages is not None:
        budget = max_messages - len(trusted_system) - len(pinned_tail)
        budget = max(budget, 0)
        if len(trimmable) > budget:
            trimmed_count = len(trimmable) - budget
            trimmable = trimmable[trimmed_count:]

    ordered = trusted_system + trimmable + pinned_tail
    return BuiltContext(messages=ordered, trimmed=trimmed_count, max_messages=max_messages)


def _last_user_index(messages: list[ConversationMessage]) -> int | None:
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].role == "user":
            return index
    return None
