import os

import pytest

from agentos.gateway.store import GatewayStore
from agentos.gateway.types import GatewayUsageError


def test_gateway_store_state_transition_types_and_metadata_prompt_purged(tmp_path):
    store = GatewayStore(tmp_path / "home")
    run = store.create_run(prompt="secret prompt", provider="mock", cwd=str(tmp_path), record_policy="metadata")

    assert run.status == "queued"
    assert run.prompt == "secret prompt"

    claimed = store.claim_next()
    assert claimed.run_id == run.run_id
    assert claimed.status == "running"

    final = store.transition(run.run_id, "succeeded")
    assert final.status == "succeeded"
    assert final.prompt is None
    assert [event.type for event in store.events(run.run_id)] == ["queued", "running", "succeeded"]

    with pytest.raises(GatewayUsageError):
        store.transition(run.run_id, "failed")


def test_gateway_store_schema_claim_idempotency_record_policy_full_retry_and_prune(tmp_path):
    store = GatewayStore(tmp_path / "home")
    run = store.create_run(prompt="retry me", provider="mock", cwd=str(tmp_path), record_policy="full")
    same = store.create_run(prompt="retry me", provider="mock", cwd=str(tmp_path), record_policy="full")
    assert same.run_id == run.run_id
    store.claim_next()
    failed = store.transition(run.run_id, "failed", last_error="boom")

    with pytest.raises(GatewayUsageError) as preview_error:
        store.retry(failed.run_id, prompt=None, yes=False)
    assert preview_error.value.code == "confirmation_required"

    retry = store.retry(failed.run_id, prompt=None, yes=True)
    assert retry.status == "queued"
    assert retry.lineage_id == failed.lineage_id
    assert retry.attempt == 2
    assert retry.prompt == "retry me"

    preview = store.prune(before="9999-01-01T00:00:00Z", yes=False)
    assert preview["matched"] == 1
    assert preview["deleted"] == 0
    assert store.get_run(failed.run_id).run_id == failed.run_id

    deleted = store.prune(before="9999-01-01T00:00:00Z", yes=True)
    assert deleted["deleted"] == 1
    with pytest.raises(GatewayUsageError):
        store.get_run(failed.run_id)


def test_gateway_store_rejects_symlink_gateway_dir(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    os.symlink(target, home / "gateway")

    with pytest.raises(Exception) as exc:
        GatewayStore(home).initialize()

    assert "symlink" in str(exc.value)
