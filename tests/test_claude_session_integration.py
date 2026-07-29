from __future__ import annotations

import os

import pytest

from agentos.llm.session import get_provider


def test_real_claude_streaming_smoke_is_opt_in_and_reaches_done():
    """A one-request account smoke test, disabled unless a human opts in."""
    if os.environ.get("AGENTOS_CLAUDE_INTEGRATION") != "1":
        return

    provider = get_provider("claude")
    status = provider.status()
    if not status.authenticated:
        pytest.exit("STOP claude-session-integration unauthenticated", returncode=2)

    events = list(provider.stream_once("Reply with exactly: AgentOS Claude streaming OK"))
    assert any(event.type == "message_delta" for event in events)
    assert events[-1].type == "done"
    assert all("SENTINEL_SECRET" not in str(event.to_dict()) for event in events)
