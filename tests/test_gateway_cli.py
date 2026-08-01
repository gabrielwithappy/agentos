import json

from typer.testing import CliRunner

from agentos.cli import app

runner = CliRunner()


def test_gateway_cli_help_json_jsonl_commands_provider_required_project_marker_recovery(tmp_path, monkeypatch):
    help_result = runner.invoke(app, ["gateway", "--help"])
    assert help_result.exit_code == 0
    for command in ("doctor", "submit", "list", "status", "events", "cancel", "retry", "prune", "worker"):
        assert command in help_result.output

    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    doctor = runner.invoke(app, ["gateway", "doctor", "--json"])
    assert doctor.exit_code == 0
    assert json.loads(doctor.stdout)["provider_required"] is True

    project = tmp_path / "project"
    project.mkdir()
    missing_provider = runner.invoke(app, ["gateway", "submit", "--cwd", str(project), "hello", "--json"])
    assert missing_provider.exit_code == 2
    assert json.loads(missing_provider.stdout)["error"]["code"] == "provider_required"

    marker_missing = runner.invoke(app, ["gateway", "submit", "--provider", "mock", "--cwd", str(project), "hello", "--json"])
    assert marker_missing.exit_code == 2
    assert json.loads(marker_missing.stdout)["error"]["code"] == "project_root_missing"


def test_gateway_cli_submit_worker_status_git_project_initialized_project_persistence_retry_cancel_recovery_metadata_prompt_required_full_prompt_reuse_no_prompt_leak(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()

    submit = runner.invoke(app, ["gateway", "submit", "--provider", "mock", "--cwd", str(project), "--record-policy", "full", "hello", "--json"])
    assert submit.exit_code == 0
    run_id = json.loads(submit.stdout)["run_id"]

    worker = runner.invoke(app, ["gateway", "worker", "--once", "--json"])
    assert worker.exit_code == 0
    assert json.loads(worker.stdout)["run"]["status"] == "succeeded"

    status = runner.invoke(app, ["gateway", "status", run_id, "--json"])
    assert status.exit_code == 0
    assert json.loads(status.stdout)["status"] == "succeeded"

    events = runner.invoke(app, ["gateway", "events", run_id, "--json"])
    assert events.exit_code == 0
    assert all(json.loads(line)["run_id"] == run_id for line in events.stdout.splitlines())

    retry = runner.invoke(app, ["gateway", "retry", run_id, "--json"])
    assert retry.exit_code == 2
    assert json.loads(retry.stdout)["error"]["code"] == "retry_not_allowed"


def test_gateway_cli_prune_retention_metadata_terminal_purge_full_secure_delete_preview_and_yes(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()

    submit = runner.invoke(app, ["gateway", "submit", "--provider", "mock", "--cwd", str(project), "--record-policy", "full", "hello", "--json"])
    run_id = json.loads(submit.stdout)["run_id"]
    runner.invoke(app, ["gateway", "worker", "--once", "--json"])

    preview = runner.invoke(app, ["gateway", "prune", "--before", "9999-01-01T00:00:00Z", "--json"])
    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["matched"] == 1

    deleted = runner.invoke(app, ["gateway", "prune", "--before", "9999-01-01T00:00:00Z", "--yes", "--json"])
    assert deleted.exit_code == 0
    assert json.loads(deleted.stdout)["deleted"] == 1

    status = runner.invoke(app, ["gateway", "status", run_id, "--json"])
    assert status.exit_code == 2
    assert json.loads(status.stdout)["error"]["code"] == "unknown_run"
