import json

from agentos.llm.auth.store import AUTH_SCHEMA_VERSION, AuthFileStore
from agentos.llm.auth.types import AuthRecord


def test_auth_record_summary_excludes_secret_values():
    record = AuthRecord(
        provider="codex",
        credential_type="account-login",
        authenticated=True,
        secrets={"access_token": "SENTINEL_SECRET", "refresh_token": "REFRESH_SECRET"},
        account_label="primary",
    )

    payload = record.summary().to_dict()
    serialized = json.dumps(payload)

    assert payload["provider"] == "codex"
    assert payload["credential_type"] == "account-login"
    assert payload["authenticated"] is True
    assert payload["secret_fields"] == ["access_token", "refresh_token"]
    assert "SENTINEL_SECRET" not in serialized
    assert "REFRESH_SECRET" not in serialized


def test_auth_store_round_trips_record(tmp_path):
    store = AuthFileStore(home=tmp_path)
    record = AuthRecord(
        provider="codex",
        credential_type="account-login",
        authenticated=True,
        secrets={"access_token": "token-1"},
        metadata={"source": "test"},
    )

    store.upsert(record)
    loaded = store.get("codex")

    assert loaded is not None
    assert loaded.provider == "codex"
    assert loaded.secrets["access_token"] == "token-1"
    assert loaded.metadata["source"] == "test"


def test_auth_store_uses_user_only_permissions(tmp_path):
    store = AuthFileStore(home=tmp_path)
    store.upsert(
        AuthRecord(
            provider="mock",
            credential_type="mock",
            authenticated=False,
        )
    )

    mode = store.path.stat().st_mode & 0o777

    assert mode == 0o600


def test_auth_store_serializes_modify_and_delete(tmp_path):
    store = AuthFileStore(home=tmp_path)
    store.upsert(
        AuthRecord(
            provider="codex",
            credential_type="account-login",
            authenticated=False,
            secrets={"refresh_token": "old"},
        )
    )
    store.upsert(
        AuthRecord(
            provider="codex",
            credential_type="account-login",
            authenticated=True,
            secrets={"refresh_token": "new"},
        )
    )
    store.upsert(
        AuthRecord(
            provider="mock",
            credential_type="mock",
            authenticated=False,
        )
    )

    assert [record.provider for record in store.list_records()] == ["codex", "mock"]
    assert store.get("codex").authenticated is True
    assert store.delete("codex") is True
    assert store.get("codex") is None
    assert store.delete("codex") is False


def test_auth_store_persists_schema_and_redacts_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")
    store = AuthFileStore(home=tmp_path)
    store.upsert(
        AuthRecord(
            provider="codex",
            credential_type="account-login",
            authenticated=True,
            secrets={"access_token": "SENTINEL_SECRET"},
        )
    )

    data = json.loads(store.path.read_text(encoding="utf-8"))
    summary_json = json.dumps(store.get("codex").summary().to_dict())

    assert data["schema_version"] == AUTH_SCHEMA_VERSION
    assert "SENTINEL_SECRET" not in summary_json
