import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/knowledge-curator/scripts/knowledge.py"

def _run(*args):
    return subprocess.run(["python3", "-S", str(SCRIPT), *args], text=True, capture_output=True)

def test_remote_url_with_userinfo_rejection(tmp_path):
    result = _run("init", "--project", str(tmp_path), "--remote", "https://secret@github.com/x/y.git")
    assert result.returncode == 2 and "secret" not in result.stdout

def test_dirty_checkout_rejection_and_no_auto_push(tmp_path):
    project = tmp_path / "project"; project.mkdir()
    assert _run("init", "--project", str(project), "--remote", "file:///tmp/remote.git").returncode == 0
    push = _run("sync", "--project", str(project), "--push")
    assert push.returncode == 2
    assert json.loads(push.stdout)["changed"] is False

def test_symlink_escape_rejection(tmp_path):
    project = tmp_path / "project"; project.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    (project / "docs").mkdir()
    (project / "docs" / "knowledge").symlink_to(outside, target_is_directory=True)
    result = _run("status", "--project", str(project))
    assert result.returncode == 2
