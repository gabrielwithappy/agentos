from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agentos.llm.redaction import sanitize


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class AuthRecordSummary:
    provider: str
    credential_type: str
    authenticated: bool
    secret_fields: tuple[str, ...] = ()
    account_label: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": self.provider,
            "credential_type": self.credential_type,
            "authenticated": self.authenticated,
            "secret_fields": list(self.secret_fields),
        }
        if self.account_label is not None:
            payload["account_label"] = self.account_label
        if self.updated_at is not None:
            payload["updated_at"] = self.updated_at
        return sanitize(payload)


@dataclass(frozen=True)
class AuthRecord:
    provider: str
    credential_type: str
    authenticated: bool
    secrets: dict[str, str] = field(default_factory=dict)
    account_label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": self.provider,
            "credential_type": self.credential_type,
            "authenticated": self.authenticated,
            "secrets": dict(self.secrets),
            "metadata": dict(self.metadata),
            "updated_at": self.updated_at,
        }
        if self.account_label is not None:
            payload["account_label"] = self.account_label
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AuthRecord":
        return cls(
            provider=str(payload["provider"]),
            credential_type=str(payload["credential_type"]),
            authenticated=bool(payload["authenticated"]),
            secrets={str(key): str(value) for key, value in dict(payload.get("secrets", {})).items()},
            account_label=str(payload["account_label"]) if payload.get("account_label") is not None else None,
            metadata=dict(payload.get("metadata", {})),
            updated_at=str(payload.get("updated_at") or utc_now()),
        )

    def summary(self) -> AuthRecordSummary:
        return AuthRecordSummary(
            provider=self.provider,
            credential_type=self.credential_type,
            authenticated=self.authenticated,
            secret_fields=tuple(sorted(self.secrets)),
            account_label=self.account_label,
            updated_at=self.updated_at,
        )
