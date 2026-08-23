import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/knowledge-curator/scripts/knowledge.py"


def _run(*args: str):
    return subprocess.run([sys.executable, "-S", str(SCRIPT), *args], text=True, capture_output=True)


def test_skill_contract_and_cli_parity():
    text = (ROOT / "catalog/skills/knowledge-curator/SKILL.md").read_text()
    assert "name: knowledge-curator" in text
    assert "Run commands from the copied skill directory." in text
    assert "AgentOS" not in text
    assert "catalog/skills/knowledge-curator" not in text
    assert _run("--help").returncode == 0


def test_installed_skill_discovery(tmp_path):
    destination = tmp_path / "skills" / "knowledge-curator"
    shutil.copytree(ROOT / "catalog/skills/knowledge-curator", destination)
    result = subprocess.run([sys.executable, "-S", str(destination / "scripts/knowledge.py"), "--help"], text=True, capture_output=True)
    assert result.returncode == 0 and (destination / "SKILL.md").is_file()


def test_cli_command_help():
    for command in ("init", "status", "backup", "sync", "validate"):
        assert _run(command, "--help").returncode == 0


def test_json_exit_contract(tmp_path):
    bad = _run("init", "--project", str(tmp_path), "--remote", "https://token@example.com/x.git")
    assert bad.returncode == 2
    payload = json.loads(bad.stdout)
    assert payload["ok"] is False and payload["code"] == 2 and payload["changed"] is False and "token" not in bad.stdout


def test_parser_error_json():
    """Unknown flags produce JSON error envelope, not argparse text error."""
    result = _run("init", "--remote", "file:///tmp/r.git", "--unknown-flag")
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["code"] == 2
    assert payload["changed"] is False
    assert "next" in payload


def test_guidance_contract(tmp_path):
    """init --help shows okf-starter opt-in semantics."""
    result = _run("init", "--help")
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "--okf-starter" in combined


def test_installed_help(tmp_path):
    """Installed copy supports --okf-starter in init help."""
    destination = tmp_path / "skills" / "knowledge-curator"
    shutil.copytree(ROOT / "catalog/skills/knowledge-curator", destination)
    result = subprocess.run(
        [sys.executable, "-S", str(destination / "scripts/knowledge.py"), "init", "--help"],
        text=True, capture_output=True
    )
    assert result.returncode == 0
    assert "--okf-starter" in result.stdout + result.stderr


def test_parser_error_json_validate():
    """validate --migrate emits JSON error, not argparse text."""
    result = _run("validate", "--project", "/tmp", "--migrate")
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["changed"] is False
    assert "migrate" in payload.get("message", "").lower() or "next" in payload


def test_local_policy_refuses_sync_before_network_activity(tmp_path):
    """The default local policy refuses sync without attempting a remote action."""
    project = tmp_path / "project"
    project.mkdir()
    _run("init", "--project", str(project), "--remote", "file:///tmp/test.git")
    result = _run("sync", "--project", str(project))
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["changed"] is False
    assert payload["phase"] == "policy"
    assert payload["remote_published"] is False


def test_rejects_migrate_or_visualize_or_mcp():
    """--migrate, visualize, and MCP-style commands must be refused or absent."""
    # --migrate refused
    result = _run("validate", "--project", "/tmp", "--migrate")
    assert result.returncode == 2
    # visualize / mcp commands must not exist
    result_viz = _run("visualize")
    assert result_viz.returncode != 0
    result_mcp = _run("mcp")
    assert result_mcp.returncode != 0
