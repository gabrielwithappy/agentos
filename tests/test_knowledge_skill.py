import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/knowledge-curator/scripts/knowledge.py"

def _run(*args: str):
    return subprocess.run(["python3", "-S", str(SCRIPT), *args], text=True, capture_output=True)

def test_skill_contract_and_cli_parity():
    text = (ROOT / "catalog/skills/knowledge-curator/SKILL.md").read_text()
    assert "name: knowledge-curator" in text and "Copy the folder" in text
    assert _run("--help").returncode == 0

def test_installed_skill_discovery(tmp_path):
    destination = tmp_path / "skills" / "knowledge-curator"
    shutil.copytree(ROOT / "catalog/skills/knowledge-curator", destination)
    result = subprocess.run(["python3", "-S", str(destination / "scripts/knowledge.py"), "--help"], text=True, capture_output=True)
    assert result.returncode == 0 and (destination / "SKILL.md").is_file()

def test_cli_command_help():
    for command in ("init", "status", "backup", "sync"):
        assert _run(command, "--help").returncode == 0

def test_json_exit_contract(tmp_path):
    bad = _run("init", "--project", str(tmp_path), "--remote", "https://token@example.com/x.git")
    assert bad.returncode == 2
    payload = json.loads(bad.stdout)
    assert payload["ok"] is False and payload["code"] == 2 and payload["changed"] is False and "token" not in bad.stdout
