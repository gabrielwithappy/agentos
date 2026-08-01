from __future__ import annotations

import fcntl
import os
from pathlib import Path
from typing import Any

from agentos.gateway.adapters import RuntimeAdapter
from agentos.gateway.store import GatewayStore
from agentos.gateway.types import GatewayError, canonical_project_root
from agentos.llm.redaction import sanitize
from agentos.runtime.protocol import RuntimeRequest


class WorkerLock:
    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("w", encoding="utf-8")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise GatewayError("Another gateway worker is already active.", code="worker_active", exit_code=2) from exc
        self.handle.write(str(os.getpid()))
        self.handle.flush()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.handle:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
        return False


class SingleWorker:
    def __init__(self, store: GatewayStore | None = None, adapter: RuntimeAdapter | None = None):
        self.store = store or GatewayStore()
        self.adapter = adapter or RuntimeAdapter()

    def run_once(self) -> dict[str, Any]:
        self.store.initialize()
        with WorkerLock(self.store.root / "worker.lock"):
            recovered = self.store.recover_orphans()
            run = self.store.claim_next()
            if run is None:
                return {"processed": 0, "recovered": recovered}
            try:
                canonical_project_root(run.cwd)
                if run.prompt is None:
                    raise GatewayError(
                        "Stored prompt was purged by metadata policy. Retry with a new prompt.",
                        code="prompt_unavailable",
                    )
                request = RuntimeRequest(
                    prompt=run.prompt,
                    provider=run.provider,
                    record_policy=run.record_policy,
                    transport_hint="direct_provider",
                )
                saw_done = False
                saw_error = False
                for event in self.adapter.stream(request, cwd=run.cwd):
                    payload = event.to_dict()
                    self.store.append_event(run.run_id, f"provider.{event.type}", payload)
                    if event.type == "done":
                        saw_done = True
                    if event.type == "error":
                        saw_error = True
                if saw_done and not saw_error:
                    final = self.store.transition(run.run_id, "succeeded")
                elif saw_error:
                    final = self.store.transition(run.run_id, "failed", last_error="Provider returned an error event.")
                else:
                    final = self.store.transition(run.run_id, "failed", last_error="Provider stream ended without a terminal done event.")
                return {"processed": 1, "recovered": recovered, "run": final.to_dict()}
            except Exception as exc:
                final = self.store.transition(run.run_id, "failed", last_error=str(exc))
                self.store.append_event(run.run_id, "worker.error", {"error": sanitize(str(exc))})
                return {"processed": 1, "recovered": recovered, "run": final.to_dict()}
