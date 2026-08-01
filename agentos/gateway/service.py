from __future__ import annotations

from pathlib import Path
from typing import Any

from agentos.gateway.store import GatewayStore
from agentos.gateway.types import GatewayUsageError, RunRecord, canonical_project_root
from agentos.runtime.protocol import RecordPolicy
from agentos.terminal.paths import read_preferred_provider


class GatewayService:
    def __init__(self, store: GatewayStore | None = None):
        self.store = store or GatewayStore()

    def doctor(self, provider: str | None = None) -> dict[str, Any]:
        self.store.initialize()
        selected = provider or read_preferred_provider()
        payload: dict[str, Any] = {
            "state": "ready",
            "gateway_home": str(self.store.root),
            "database": str(self.store.db_path),
            "provider_required": selected is None,
            "next_action": "agentos gateway submit --provider mock \"prompt\"" if selected is None else "agentos gateway submit \"prompt\"",
        }
        if selected:
            payload["provider"] = selected
        return payload

    def submit(
        self,
        prompt: str,
        *,
        provider: str | None,
        cwd: str | Path | None,
        record_policy: RecordPolicy,
        idempotency_key: str | None = None,
    ) -> RunRecord:
        if not prompt.strip():
            raise GatewayUsageError("A prompt is required. Next: agentos gateway submit \"prompt\"", code="prompt_required")
        selected_provider = provider or read_preferred_provider()
        if not selected_provider:
            raise GatewayUsageError(
                "Gateway submit requires --provider or a saved preferred provider. Next: agentos gateway submit --provider mock \"prompt\"",
                code="provider_required",
            )
        root = canonical_project_root(cwd or Path.cwd())
        return self.store.create_run(
            prompt=prompt,
            provider=selected_provider,
            cwd=str(root),
            record_policy=record_policy,
            idempotency_key=idempotency_key,
        )

    def list_runs(self, status: str | None = None) -> list[RunRecord]:
        return self.store.list_runs(status=status)

    def status(self, run_id: str) -> RunRecord:
        return self.store.get_run(run_id)

    def events(self, run_id: str):
        self.store.get_run(run_id)
        return self.store.events(run_id)

    def cancel(self, run_id: str) -> RunRecord:
        return self.store.cancel(run_id)

    def retry(self, run_id: str, *, prompt: str | None, yes: bool) -> RunRecord:
        return self.store.retry(run_id, prompt=prompt, yes=yes)

    def prune(self, *, before: str, yes: bool) -> dict[str, Any]:
        return self.store.prune(before=before, yes=yes)
