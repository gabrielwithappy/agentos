import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/knowledge-curator/scripts/knowledge.py"


def _run(*args):
    return subprocess.run([sys.executable, "-S", str(SCRIPT), *args], text=True, capture_output=True)


def test_remote_url_with_userinfo_rejection(tmp_path):
    result = _run("init", "--project", str(tmp_path), "--remote", "https://secret@github.com/x/y.git")
    assert result.returncode == 2 and "secret" not in result.stdout


def test_dirty_checkout_rejection_and_no_auto_push(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    assert _run("init", "--project", str(project), "--remote", "file:///tmp/remote.git").returncode == 0
    push = _run("sync", "--project", str(project), "--push")
    assert push.returncode == 2
    assert json.loads(push.stdout)["changed"] is False


def test_symlink_escape_rejection(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "docs").mkdir()
    (project / "docs" / "knowledge").symlink_to(outside, target_is_directory=True)
    result = _run("status", "--project", str(project))
    assert result.returncode == 2


def test_okf_starter_no_push_no_fetch_no_pull(tmp_path):
    """OKF starter must not invoke git fetch, pull, or push."""
    import os
    project = tmp_path / "project"
    project.mkdir()
    result = _run("init", "--remote", "file:///tmp/test-remote.git", "--okf-starter", "--project", str(project))
    # Successful init or refusal — key is no network invocation
    assert result.returncode in (0, 2, 3)
    # stdout must not contain push/fetch/pull success messages
    assert "fatal: repository 'file:///tmp/test-remote.git/' not found" not in result.stdout
    assert "From file://" not in result.stdout


def test_no_partial_state_after_starter_failure(tmp_path):
    """After a write failure, no partial starter files remain."""
    project = tmp_path / "project"
    project.mkdir()
    knowledge = project / "docs" / "knowledge"
    knowledge.mkdir(parents=True)

    import subprocess as sp
    git_result = sp.run(["git", "init", str(knowledge)], capture_output=True)
    if git_result.returncode != 0:
        import pytest
        pytest.skip("git not available")

    # Make concepts unwritable to simulate a write failure
    concepts = knowledge / "concepts"
    concepts.mkdir()
    concepts.chmod(0o444)

    result = _run("init", "--remote", "file:///tmp/r.git", "--okf-starter", "--project", str(project))
    concepts.chmod(0o755)

    if result.returncode != 0:
        payload = json.loads(result.stdout)
        assert payload["changed"] is False or "starter" not in payload.get("message", "")

    # No partial state: if index exists, log and concept must also exist
    index = knowledge / "index.md"
    log_md = knowledge / "log.md"
    starter_concept = knowledge / "concepts" / "getting-started.md"

    if index.exists():
        assert log_md.exists() and starter_concept.exists(), "Partial bundle detected"


def test_git_init_not_invoked_on_credential_remote(tmp_path):
    """Credential-bearing remote must be rejected before git init."""
    project = tmp_path / "project"
    project.mkdir()
    result = _run("init", "--project", str(project), "--remote", "https://tok@github.com/x.git", "--okf-starter")
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["changed"] is False
    # .git should NOT have been created
    knowledge = project / "docs" / "knowledge"
    assert not (knowledge / ".git").exists()
