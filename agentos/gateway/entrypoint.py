from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path

from agentos.llm.invocation import invoke_once
from agentos.runtime.protocol import InvocationEvent, RuntimeRequest
from agentos.terminal.hooks import apply_input_hooks


@contextlib.contextmanager
def scoped_cwd(path: str | Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def execute_runtime_request(request: RuntimeRequest, *, cwd: str | Path | None = None, apply_hooks: bool = True) -> Iterator[InvocationEvent]:
    prompt = apply_input_hooks(request.prompt) if apply_hooks else request.prompt
    effective = RuntimeRequest(
        prompt=prompt,
        provider=request.provider,
        session_id=request.session_id,
        transport_hint=request.transport_hint,
        record_policy=request.record_policy,
    )
    if cwd is None:
        yield from invoke_once(effective)
        return
    with scoped_cwd(cwd):
        yield from invoke_once(effective)
