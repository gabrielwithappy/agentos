import os
from pathlib import Path
from typer.testing import CliRunner
from agentos.cli import app
from unittest import mock

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AgentOS CLI version" in result.stdout

def test_setup_command(tmp_path):
    # Mock AGENTOS_HOME to be tmp_path
    with mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path)}):
        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        assert "Setting up AgentOS..." in result.stdout
        assert "PASS agentos-setup" in result.stdout
        
        # Check if core directory was created
        assert (tmp_path / "core").is_dir()
        
        # Check if manifest.json was created
        assert (tmp_path / "manifest.json").is_file()

def test_doctor_command():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Checking AgentOS health..." in result.stdout

def test_run_command():
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "Starting AgentOS session..." in result.stdout

@mock.patch("agentos.commands.harness.os.execv")
def test_harness_command(mock_execv):
    # Test harness execution with mocked execv
    result = runner.invoke(app, ["harness", "--flag", "value"])
    assert "Running harness loop" in result.stdout
    assert result.exit_code == 0
    mock_execv.assert_called_once()
