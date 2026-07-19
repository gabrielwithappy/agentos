from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agentos.llm.redaction import sanitize

CLI_EVENT_SCHEMA_VERSION = "agentos.cli-event/v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class CliEvent:
    type: str
    session_id: str
    turn_id: str
    provider: str
    mode: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)
    schema_version: str = CLI_EVENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return sanitize(
            {
                "schema_version": self.schema_version,
                "type": self.type,
                "session_id": self.session_id,
                "turn_id": self.turn_id,
                "timestamp": self.timestamp,
                "provider": self.provider,
                "mode": self.mode,
                "payload": self.payload,
                "metadata": self.metadata,
            }
        )


def new_turn_id() -> str:
    return str(uuid4())


def wrap_provider_event(event: dict[str, Any], *, session_id: str, turn_id: str, provider: str, mode: str) -> dict[str, Any]:
    return CliEvent(
        type=str(event.get("type", "provider_event")),
        session_id=session_id,
        turn_id=turn_id,
        provider=provider,
        mode=mode,
        payload=event,
        metadata={"cli": {"schema_version": CLI_EVENT_SCHEMA_VERSION}},
    ).to_dict()
