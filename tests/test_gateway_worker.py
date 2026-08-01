from pathlib import Path

from agentos.gateway.entrypoint import scoped_cwd
from agentos.gateway.store import GatewayStore
from agentos.gateway.worker import SingleWorker, WorkerLock


def test_scoped_cwd_restores_after_exception(tmp_path):
    before = Path.cwd()
    try:
        try:
            with scoped_cwd(tmp_path):
                assert Path.cwd() == tmp_path
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        assert Path.cwd() == before
    finally:
        import os

        os.chdir(before)


def test_worker_lock_rejects_second_owner(tmp_path):
    lock_path = tmp_path / "worker.lock"
    with WorkerLock(lock_path):
        try:
            with WorkerLock(lock_path):
                raise AssertionError("second lock should fail")
        except Exception as exc:
            assert "worker" in str(exc).lower()


def test_worker_recovers_orphaned_running(tmp_path):
    store = GatewayStore(tmp_path / "home")
    run = store.create_run(prompt="hello", provider="mock", cwd=str(tmp_path), record_policy="full")
    store.claim_next()

    result = SingleWorker(store=store).run_once()

    assert result["processed"] == 0
    assert result["recovered"] == 1
    assert store.get_run(run.run_id).status == "interrupted"


def test_adapter_terminal_event_protocol_failure_event_mapping_redaction(tmp_path, monkeypatch):
    from agentos.gateway.adapters import RuntimeAdapter
    from agentos.runtime.protocol import InvocationEvent, RuntimeRequest, RuntimeTimings

    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    class NoDoneAdapter(RuntimeAdapter):
        def stream(self, request: RuntimeRequest, *, cwd: str):
            yield InvocationEvent(
                type="message_delta",
                provider="mock",
                mode="mock",
                request=request,
                timings=RuntimeTimings(bootstrap_ms=0, provider_ms=0),
                text="SENTINEL_SECRET",
            )

    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    store = GatewayStore(tmp_path / "home")
    run = store.create_run(prompt="hello", provider="mock", cwd=str(project), record_policy="full")

    result = SingleWorker(store=store, adapter=NoDoneAdapter()).run_once()

    assert result["run"]["status"] == "failed"
    events = [event.to_dict() for event in store.events(run.run_id)]
    assert any(event["type"] == "provider.message_delta" for event in events)
    assert "SENTINEL_SECRET" not in str(events)
