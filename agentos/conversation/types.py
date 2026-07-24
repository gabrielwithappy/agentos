from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

CONVERSATION_SCHEMA_VERSION = "agentos.conversation/v1"

MessageRole = Literal["system", "user", "assistant", "tool"]

TRUSTED_SYSTEM_SOURCE = "agentos-config"
"""Only this source may produce a `system`-role message; every other origin
(restored JSONL/snapshot, PI reference text, provider/tool output, user
input) is untrusted data even if it claims to be `system`."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_message_id() -> str:
    return str(uuid4())


@dataclass(frozen=True)
class ConversationMessage:
    """Immutable normalized conversation message.

    `role` reflects the caller-declared role. Trust in that role for
    provider-`system` purposes is decided separately by the context
    builder using `source`, never by the message alone.
    """

    id: str
    role: MessageRole
    text: str
    source: str
    turn_id: str | None = None
    tool_name: str | None = None
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "text": self.text,
            "source": self.source,
            "turn_id": self.turn_id,
            "tool_name": self.tool_name,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    def is_trusted_system(self) -> bool:
        return self.role == "system" and self.source == TRUSTED_SYSTEM_SOURCE


@dataclass(frozen=True)
class ProviderContinuation:
    """Opaque, sanitized provider continuation metadata.

    `handle` is treated as sensitive: callers must never render it in
    TUI/CLI/JSONL/exception text. It is valid only for the exact
    (provider, model, account, branch, transport_session_epoch) tuple it
    was issued for; any mismatch requires bounded replay instead of reuse.
    """

    provider: str
    model: str
    account: str
    branch_id: str
    transport_session_epoch: str
    handle: str
    created_at: str = field(default_factory=utc_now)

    def matches(
        self,
        *,
        provider: str,
        model: str,
        account: str,
        branch_id: str,
        transport_session_epoch: str,
    ) -> bool:
        return (
            self.provider == provider
            and self.model == model
            and self.account == account
            and self.branch_id == branch_id
            and self.transport_session_epoch == transport_session_epoch
        )

    def to_dict(self) -> dict[str, Any]:
        """Sanitized representation: never includes the raw `handle`."""
        return {
            "provider": self.provider,
            "model": self.model,
            "branch_id": self.branch_id,
            "transport_session_epoch": self.transport_session_epoch,
            "created_at": self.created_at,
            "handle_present": bool(self.handle),
        }


@dataclass(frozen=True)
class BranchHead:
    """A named conversation branch pointing at an immutable message prefix."""

    branch_id: str
    label: str
    head_message_id: str | None
    parent_branch_id: str | None = None
    fork_point_message_id: str | None = None
    continuation: ProviderContinuation | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "label": self.label,
            "head_message_id": self.head_message_id,
            "parent_branch_id": self.parent_branch_id,
            "fork_point_message_id": self.fork_point_message_id,
            "continuation": self.continuation.to_dict() if self.continuation else None,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ConversationState:
    """Immutable snapshot of a session's normalized conversation.

    `messages` is the append-only, insertion-ordered set of all messages
    across all branches. Branch membership is reconstructed by walking
    `parent_message_id` links from a `BranchHead.head_message_id`, so
    forking never copies or mutates prior messages.
    """

    session_id: str
    active_branch_id: str
    branches: dict[str, BranchHead]
    messages: dict[str, ConversationMessage]
    parent_message_id: dict[str, str | None]
    schema_version: str = CONVERSATION_SCHEMA_VERSION

    def active_branch(self) -> BranchHead:
        return self.branches[self.active_branch_id]

    def branch_messages(self, branch_id: str) -> list[ConversationMessage]:
        """Ordered messages (oldest first) for `branch_id`'s immutable prefix."""
        head = self.branches[branch_id]
        chain: list[ConversationMessage] = []
        cursor = head.head_message_id
        while cursor is not None:
            message = self.messages[cursor]
            chain.append(message)
            cursor = self.parent_message_id.get(cursor)
        chain.reverse()
        return chain

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "active_branch_id": self.active_branch_id,
            "branches": {bid: b.to_dict() for bid, b in self.branches.items()},
            "messages": {mid: m.to_dict() for mid, m in self.messages.items()},
            "parent_message_id": dict(self.parent_message_id),
        }
