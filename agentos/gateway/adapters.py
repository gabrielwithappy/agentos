from __future__ import annotations

from collections.abc import Iterator

from agentos.gateway.entrypoint import execute_runtime_request
from agentos.runtime.protocol import InvocationEvent, RuntimeRequest


class RuntimeAdapter:
    def stream(self, request: RuntimeRequest, *, cwd: str) -> Iterator[InvocationEvent]:
        yield from execute_runtime_request(request, cwd=cwd, apply_hooks=True)
