from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


EventType = Literal[
    "start", "message_delta", "reasoning", "tool_call", "tool_result", "done", "error"
]


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    mode: str
    credential_present: bool
    authenticated: bool
    persistent_credential: bool
    message: str
    status: str | None = None
    recovery: str | None = None
    next_command: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": self.provider,
            "mode": self.mode,
            "credential_present": self.credential_present,
            "authenticated": self.authenticated,
            "persistent_credential": self.persistent_credential,
            "message": self.message,
        }
        if self.status is not None:
            payload["status"] = self.status
        if self.recovery is not None:
            payload["recovery"] = self.recovery
        if self.next_command is not None:
            payload["next_command"] = self.next_command
        return payload


@dataclass(frozen=True)
class LLMEvent:
    type: EventType
    provider: str
    mode: str
    text: str | None = None
    usage: dict[str, int] | None = None
    error: dict[str, str] | None = None
    recovery: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "provider": self.provider,
            "mode": self.mode,
        }
        if self.text is not None:
            payload["text"] = self.text
        if self.usage is not None:
            payload["usage"] = self.usage
        if self.error is not None:
            payload["error"] = self.error
        if self.recovery is not None:
            payload["recovery"] = self.recovery
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload
