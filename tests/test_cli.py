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
    with mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path)}):
        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        assert "Setting up AgentOS..." in result.stdout
        assert "PASS agentos-setup" in result.stdout
        assert (tmp_path / "sessions").is_dir()
        assert (tmp_path / "context").is_dir()
        assert (tmp_path / "state-manifest.json").is_file()
        assert not (tmp_path / "core" / ".agents").exists()

def test_doctor_command_success(tmp_path):
    # Set up a healthy environment
    runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(tmp_path)})
    
    with mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path)}):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "All systems go" in result.stdout

def test_doctor_command_missing_env(tmp_path):
    with mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path)}):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
        assert "not configured at" in result.stdout
        assert "Diagnosis completed with errors" in result.stdout

def test_run_command():
    result = runner.invoke(app, ["run", "--once", "hello"])
    assert result.exit_code == 0
    assert "Mock response" in result.stdout

@mock.patch("agentos.commands.harness.os.execv")
def test_harness_command(mock_execv):
    result = runner.invoke(app, ["harness", "--project-root", ".", "--flag", "value"])
    assert "Starting Python harness engine" in result.stdout
    assert result.exit_code == 0
    mock_execv.assert_called_once()

def test_skill_list_empty(tmp_path):
    skills_dir = tmp_path / "core" / ".agents" / "skills"
    skills_dir.mkdir(parents=True)
    
    with mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path)}):
        result = runner.invoke(app, ["skill", "list"])
        assert result.exit_code == 0
        assert "No skills installed" in result.stdout

def test_skill_add_success(tmp_path):
    skills_dir = tmp_path / "core" / ".agents" / "skills"
    skills_dir.mkdir(parents=True)
    
    # Create a mock skill source
    source_skill = tmp_path / "mock_skill"
    source_skill.mkdir()
    (source_skill / "SKILL.md").touch()
    
    with mock.patch.dict(os.environ, {"AGENTOS_HOME": str(tmp_path)}):
        result = runner.invoke(app, ["skill", "add", str(source_skill)])
        assert result.exit_code == 0
        assert "Successfully installed skill" in result.stdout
        assert (skills_dir / "mock_skill").is_dir()
