from __future__ import annotations

import time
from collections.abc import Iterator

from agentos.llm.session import get_provider
from agentos.runtime.protocol import InvocationEvent, RuntimeRequest, RuntimeTimings


def invoke_once(request: RuntimeRequest) -> Iterator[InvocationEvent]:
    """Wrap the existing provider facade with normalized invocation timings."""
    started_at = time.perf_counter()
    provider = get_provider(request.provider)
    provider_ready_at = time.perf_counter()

    first_event_at: float | None = None
    for event in provider.stream_once(request.prompt):
        now = time.perf_counter()
        if first_event_at is None:
            first_event_at = now
        timings = RuntimeTimings(
            bootstrap_ms=(provider_ready_at - started_at) * 1000,
            provider_ms=(now - provider_ready_at) * 1000,
            first_event_ms=(first_event_at - started_at) * 1000,
            total_ms=(now - started_at) * 1000,
        )
        yield InvocationEvent.from_llm_event(
            event,
            request=request,
            timings=timings,
            metadata={"runtime": {"schema_version": "agentos.invocation-runtime/v1"}},
        )
