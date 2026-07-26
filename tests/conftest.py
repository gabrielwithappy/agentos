from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _default_skip_context_bootstrap(monkeypatch):
    """Tests run with this repo's own working directory, which has a real
    `AGENTS.md` ancestor — without this, every test that creates a new
    session would non-deterministically pick it up. Individual tests that
    actually exercise `agentos.conversation.bootstrap` override this via
    their own `monkeypatch.setenv`/`delenv` calls, which take precedence
    since they run after this fixture within the same test."""
    monkeypatch.setenv("AGENTOS_SKIP_CONTEXT_BOOTSTRAP", "1")
