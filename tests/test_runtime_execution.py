from pathlib import Path

from agentos.gateway.entrypoint import execute_runtime_request, scoped_cwd
from agentos.runtime.protocol import RuntimeRequest


def test_execute_runtime_request_uses_hooks_and_restores_cwd(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    before = Path.cwd()

    events = list(execute_runtime_request(RuntimeRequest(prompt="  hello  ", provider="mock"), cwd=tmp_path))

    assert Path.cwd() == before
    assert [event.type for event in events][-1] == "done"
    assert "Received 'hello'" in [event.text for event in events if event.text][-1]


def test_scoped_cwd_restores_after_success_and_exception(tmp_path):
    before = Path.cwd()
    try:
        with scoped_cwd(tmp_path):
            assert Path.cwd() == tmp_path
        assert Path.cwd() == before
        try:
            with scoped_cwd(tmp_path):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        assert Path.cwd() == before
    finally:
        import os

        os.chdir(before)
