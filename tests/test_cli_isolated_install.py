import json
import os
from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app
from agentos.terminal.paths import StateError, agentos_home, ensure_contained, initialize_state

runner = CliRunner()


def test_paths_resolve_absolute(tmp_path):
    assert agentos_home(tmp_path / "state").is_absolute()


def test_containment_rejects_escape(tmp_path):
    root = tmp_path / "home"
    try:
        ensure_contained(tmp_path / "outside", root)
    except StateError as exc:
        assert "escapes" in str(exc)
    else:
        raise AssertionError("expected StateError")


def test_initialize_state_creates_only_cli_state(tmp_path):
    root = initialize_state(tmp_path)
    assert (root / "sessions").is_dir()
    assert (root / "context").is_dir()
    assert (root / "config.toml").is_file()
    manifest = json.loads((root / "state-manifest.json").read_text())
    assert manifest["schema_version"] == "agentos.cli-state/v1"
    assert not (root / "core" / ".agents").exists()


def test_setup_doctor_json_contract(tmp_path):
    env = {"AGENTOS_HOME": str(tmp_path)}
    setup = runner.invoke(app, ["setup"], env=env)
    assert setup.exit_code == 0
    doctor = runner.invoke(app, ["doctor", "--json"], env=env)
    assert doctor.exit_code == 0
    payload = json.loads(doctor.stdout)
    assert payload["configured"] is True


def test_setup_rejects_symlink_home(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    os.symlink(target, link)
    result = runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(link)})
    assert result.exit_code == 1
    assert "must not be a symlink" in result.stdout
