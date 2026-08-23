import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/knowledge-curator/scripts/knowledge.py"


def _run(*args: str):
    return subprocess.run([sys.executable, "-S", str(SCRIPT), *args], text=True, capture_output=True)


def _payload(*args: str):
    result = _run(*args)
    return result, json.loads(result.stdout)


def _configure(checkout: Path):
    subprocess.run(["git", "-C", str(checkout), "config", "user.name", "Knowledge Test"], check=True)
    subprocess.run(["git", "-C", str(checkout), "config", "user.email", "knowledge-test@example.invalid"], check=True)


def _init(project: Path, remote: Path, policy: str = "manual") -> Path:
    project.mkdir()
    result, payload = _payload("init", "--project", str(project), "--remote", remote.as_uri(), "--sync-policy", policy)
    assert result.returncode == 0, payload
    checkout = project / "docs" / "knowledge"
    _configure(checkout)
    return checkout


def _backup(project: Path, filename: str, text: str):
    checkout = project / "docs" / "knowledge"
    (checkout / filename).write_text(text, encoding="utf-8")
    result, payload = _payload("backup", "--project", str(project), "--message", f"add {filename}")
    assert result.returncode == 0, payload


def test_initial_publish_and_empty_checkout_bootstrap(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    first = tmp_path / "first"
    _init(first, remote)
    _backup(first, "first.md", "first\n")
    result, payload = _payload("sync", "--project", str(first))
    assert result.returncode == 0 and payload["remote_published"] is True
    second = tmp_path / "second"
    second_checkout = _init(second, remote)
    result, payload = _payload("sync", "--project", str(second))
    assert result.returncode == 0 and payload["changed"] is True
    assert (second_checkout / "first.md").read_text(encoding="utf-8") == "first\n"


def test_divergent_non_conflicting_merge_publishes(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    first, second = tmp_path / "first", tmp_path / "second"
    _init(first, remote)
    _backup(first, "base.md", "base\n")
    assert _run("sync", "--project", str(first)).returncode == 0
    _init(second, remote)
    assert _run("sync", "--project", str(second)).returncode == 0
    _backup(second, "second.md", "second\n")
    _backup(first, "first.md", "first\n")
    assert _run("sync", "--project", str(first)).returncode == 0
    result, payload = _payload("sync", "--project", str(second))
    assert result.returncode == 0 and payload["remote_published"] is True
    checkout = second / "docs" / "knowledge"
    assert (checkout / "first.md").is_file() and (checkout / "second.md").is_file()


def test_local_policy_and_invalid_branch_are_fail_closed(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    project = tmp_path / "project"
    _init(project, remote, "local")
    result, payload = _payload("sync", "--project", str(project))
    assert result.returncode == 2 and payload["phase"] == "policy" and payload["changed"] is False
    bad = tmp_path / "bad"
    bad.mkdir()
    result, payload = _payload("init", "--project", str(bad), "--remote", remote.as_uri(), "--branch", "bad branch")
    assert result.returncode == 2 and payload["changed"] is False and "remote.git" not in result.stdout


def test_wizard_cancel_creates_no_checkout(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    result = subprocess.run([sys.executable, "-S", str(SCRIPT), "init", "--wizard", "--project", str(project)], input="", text=True, capture_output=True)
    payload = json.loads(result.stdout)
    assert result.returncode == 2 and payload["changed"] is False
    assert "공유 Git remote" in result.stderr
    assert not (project / "docs" / "knowledge").exists()


def test_wizard_sets_manual_policy_and_keeps_stdout_json(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    project = tmp_path / "project"
    project.mkdir()
    result = subprocess.run([sys.executable, "-S", str(SCRIPT), "init", "--wizard", "--project", str(project)], input=f"{remote.as_uri()}\nmain\nmanual\n", text=True, capture_output=True)
    payload = json.loads(result.stdout)
    assert result.returncode == 0 and payload["ok"] is True
    assert "정책:" in result.stderr
    status, state = _payload("status", "--project", str(project))
    assert status.returncode == 0 and state["sync_policy"] == "manual"


def test_status_reports_policy_without_network(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    project = tmp_path / "project"
    _init(project, remote, "manual")
    result, payload = _payload("status", "--project", str(project))
    assert result.returncode == 0 and payload["sync_policy"] == "manual" and payload["branch"] == "main"


def test_auto_policy_publishes_only_after_successful_backup(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    project = tmp_path / "project"
    _init(project, remote, "auto")
    _backup(project, "auto.md", "auto\n")
    head = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "main"], text=True, capture_output=True)
    assert head.returncode == 0


def test_conflict_leaves_knowledge_files_unchanged(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    first, second = tmp_path / "first", tmp_path / "second"
    _init(first, remote)
    _backup(first, "same.md", "base\n")
    assert _run("sync", "--project", str(first)).returncode == 0
    _init(second, remote)
    assert _run("sync", "--project", str(second)).returncode == 0
    _backup(second, "same.md", "second\n")
    _backup(first, "same.md", "first\n")
    assert _run("sync", "--project", str(first)).returncode == 0
    before = (second / "docs" / "knowledge" / "same.md").read_text(encoding="utf-8")
    result, payload = _payload("sync", "--project", str(second))
    assert result.returncode == 2 and payload["phase"] == "conflict"
    assert (second / "docs" / "knowledge" / "same.md").read_text(encoding="utf-8") == before
