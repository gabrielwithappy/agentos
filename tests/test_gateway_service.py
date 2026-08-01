import json

from typer.testing import CliRunner

from agentos.cli import app

runner = CliRunner()


def test_gateway_submit_requires_project_marker(tmp_path, monkeypatch):
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))

    result = runner.invoke(app, ["gateway", "submit", "--provider", "mock", "--cwd", str(plain), "hello", "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "project_root_missing"


def test_gateway_submit_worker_status_events_retry_cancel(tmp_path, monkeypatch):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    monkeypatch.setenv("AGENTOS_HOME", str(home))

    submit = runner.invoke(app, ["gateway", "submit", "--provider", "mock", "--cwd", str(project), "hello", "--json"])
    assert submit.exit_code == 0
    run = json.loads(submit.stdout)
    assert run["status"] == "queued"

    worker = runner.invoke(app, ["gateway", "worker", "--once", "--json"])
    assert worker.exit_code == 0
    worker_payload = json.loads(worker.stdout)
    assert worker_payload["processed"] == 1
    assert worker_payload["run"]["status"] == "succeeded"
    assert "prompt" not in worker_payload["run"]

    status = runner.invoke(app, ["gateway", "status", run["run_id"], "--json"])
    assert status.exit_code == 0
    assert json.loads(status.stdout)["status"] == "succeeded"

    events = runner.invoke(app, ["gateway", "events", run["run_id"], "--json"])
    assert events.exit_code == 0
    lines = [json.loads(line) for line in events.stdout.splitlines()]
    assert [line["seq"] for line in lines] == sorted(line["seq"] for line in lines)
    assert any(line["type"].startswith("provider.") for line in lines)

    retry_preview = runner.invoke(app, ["gateway", "retry", run["run_id"], "--json"])
    assert retry_preview.exit_code == 2
    assert json.loads(retry_preview.stdout)["error"]["code"] == "retry_not_allowed"

    failed = json.loads(runner.invoke(app, ["gateway", "submit", "--provider", "bad", "--cwd", str(project), "fail me", "--json"]).stdout)
    runner.invoke(app, ["gateway", "worker", "--once", "--json"])
    retry = runner.invoke(app, ["gateway", "retry", failed["run_id"], "hello again", "--yes", "--json"])
    assert retry.exit_code == 0
    retry_payload = json.loads(retry.stdout)
    assert retry_payload["status"] == "queued"

    cancel = runner.invoke(app, ["gateway", "cancel", retry_payload["run_id"], "--json"])
    assert cancel.exit_code == 0
    assert json.loads(cancel.stdout)["status"] == "cancelled"


def test_gateway_full_policy_worker_succeeds_and_redacts_secret(tmp_path, monkeypatch):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    monkeypatch.setenv("AGENTOS_HOME", str(home))
    monkeypatch.setenv("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")

    submit = runner.invoke(
        app,
        [
            "gateway",
            "submit",
            "--provider",
            "mock",
            "--cwd",
            str(project),
            "--record-policy",
            "full",
            "hello SENTINEL_SECRET",
            "--json",
        ],
    )
    assert submit.exit_code == 0
    run = json.loads(submit.stdout)

    worker = runner.invoke(app, ["gateway", "worker", "--once", "--json"])
    assert worker.exit_code == 0
    payload = json.loads(worker.stdout)
    assert payload["run"]["status"] == "succeeded"

    events = runner.invoke(app, ["gateway", "events", run["run_id"], "--json"])
    assert events.exit_code == 0
    assert "SENTINEL_SECRET" not in events.stdout


def test_gateway_help_exposes_expected_commands():
    result = runner.invoke(app, ["gateway", "--help"])

    assert result.exit_code == 0
    normalized = " ".join(result.output.split())
    for name in ["doctor", "submit", "list", "status", "events", "cancel", "retry", "prune", "worker"]:
        assert name in normalized
