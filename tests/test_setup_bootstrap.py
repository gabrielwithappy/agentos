from __future__ import annotations

import json
import io
import os
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from agentos.cli import app
from agentos.commands import setup
from agentos.commands import vendor_hook
from agentos.commands.vendor_hook import BRIDGE_MAP, _child_env, _payload, run_bridge
from agentos.terminal import hooks_bundle
from agentos.terminal.paths import StateError


runner = CliRunner()


def _setup(project: Path, home: Path):
    return runner.invoke(app, ["setup", "--path", str(project)], env={"AGENTOS_HOME": str(home)})


def test_bootstrap_creates_only_bridge_owned_configs(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    result = _setup(project, tmp_path / "home")
    assert result.exit_code == 0, result.output
    assert "written=3" in result.output
    assert "enabled=codex,claude-code" in result.output
    codex = json.loads((project / ".codex" / "hooks.json").read_text())
    claude = json.loads((project / ".claude" / "settings.json").read_text())
    assert "agentos hook bridge codex pre-bash" in json.dumps(codex)
    assert "agentos hook bridge claude-code stop" in json.dumps(claude)
    assert ".agents/hooks" not in json.dumps(codex) + json.dumps(claude)
    assert (project / "AGENTS.md").is_file()


def test_bootstrap_preserves_existing_vendor_config_and_reports_it(tmp_path):
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    existing = project / ".codex" / "hooks.json"
    existing.write_text('{"user": "config"}\n', encoding="utf-8")
    result = _setup(project, tmp_path / "home")
    assert result.exit_code == 0, result.output
    assert existing.read_text(encoding="utf-8") == '{"user": "config"}\n'
    assert "enabled=claude-code" in result.output
    assert "skipped_vendors=codex" in result.output


def test_bootstrap_config_state_derived_summary_when_both_exist(tmp_path):
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".claude").mkdir(parents=True)
    (project / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
    (project / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    result = _setup(project, tmp_path / "home")
    assert result.exit_code == 0, result.output
    assert "enabled=none" in result.output
    assert "skipped_vendors=codex,claude-code" in result.output


def test_bootstrap_rejects_symlink_targets_without_writing(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    destination = tmp_path / "outside"
    destination.mkdir()
    os.symlink(destination, project / ".codex")
    result = _setup(project, tmp_path / "home")
    assert result.exit_code == 1
    out_no_nl = result.output.replace("\n", " ")
    assert "unsupported symlink" in out_no_nl
    assert "path=" in out_no_nl
    assert "ls -ld" in out_no_nl
    assert "No existing files were changed" in out_no_nl
    assert not (project / "AGENTS.md").exists()


def test_bootstrap_preflights_config_symlink_before_any_write(tmp_path):
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    os.symlink(outside, project / ".codex" / "hooks.json")
    result = _setup(project, tmp_path / "home")
    assert result.exit_code == 1
    assert "No existing files were changed" in result.output.replace("\n", " ")
    assert not (project / "AGENTS.md").exists()
    assert not (project / ".claude").exists()


def test_bridge_allowlist_complete_mapping_is_closed():
    assert set(BRIDGE_MAP) == {
        ("codex", "pre-bash"), ("codex", "pre-write"), ("codex", "post-bash"), ("codex", "stop"),
        ("claude-code", "pre-bash"), ("claude-code", "pre-write"), ("claude-code", "post-bash"), ("claude-code", "stop"),
    }


def test_hook_bundle_allows_only_manifest_regular_files(tmp_path, monkeypatch):
    scripts = tmp_path / "_hooks_bundle" / "hooks" / "scripts"
    scripts.mkdir(parents=True)
    allowed = scripts / "check-careful.sh"
    allowed.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(hooks_bundle, "files", lambda _package: tmp_path)
    assert hooks_bundle.bundle_script("check-careful.sh") == allowed
    try:
        hooks_bundle.bundle_script("not-in-manifest.py")
    except StateError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("expected manifest rejection")
    allowed.unlink()
    os.symlink(tmp_path / "outside", allowed)
    try:
        hooks_bundle.bundle_script("check-careful.sh")
    except StateError as exc:
        assert "not a regular file" in str(exc)
    else:
        raise AssertionError("expected symlink rejection")


def test_hook_bundle_review_artifacts_import_contract():
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    stop_script = (root / ".agents" / "hooks" / "scripts" / "stop_review_gate.py").read_text(encoding="utf-8")
    assert 'review_artifacts.py" = "agentos/_hooks_bundle/skills/harness/writing-plans/scripts/review_artifacts.py"' in pyproject
    assert 'from review_artifacts import REVIEWED_RE, check_plan' in stop_script


def test_bridge_rejects_project_local_or_unlisted_mapping(tmp_path):
    try:
        run_bridge("codex", "unknown", b"{}", tmp_path)
    except StateError as exc:
        assert "Unsupported vendor hook mapping" in str(exc)
    else:
        raise AssertionError("expected closed allowlist rejection")


def test_bridge_stdin_limit_and_object_validation(monkeypatch):
    def payload(value: bytes):
        monkeypatch.setattr(vendor_hook.sys, "stdin", io.TextIOWrapper(io.BytesIO(value), encoding="utf-8"))
        return _payload()

    assert payload(b'{"tool_input": {}}') == b'{"tool_input": {}}'
    for invalid in (b"not-json", b"[]", b"x" * (64 * 1024 + 1)):
        try:
            payload(invalid)
        except StateError:
            pass
        else:
            raise AssertionError("expected payload rejection")


def test_bridge_env_filter_excludes_untrusted_environment(tmp_path):
    with mock.patch.dict(os.environ, {"AGENTOS_TEST_SECRET": "SENTINEL_SECRET", "PATH": "/bin"}, clear=False):
        env = _child_env(tmp_path)
    assert "AGENTOS_TEST_SECRET" not in env
    assert env["AGENTOS_PROJECT_ROOT"] == str(tmp_path)
    assert env["PATH"] == "/bin"


def test_bridge_timeout_and_package_owned_child_env(tmp_path, monkeypatch):
    script = tmp_path / "check-careful.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(vendor_hook, "bundle_script", lambda _name: script)
    monkeypatch.setattr(vendor_hook.subprocess, "run", mock.Mock(side_effect=vendor_hook.subprocess.TimeoutExpired(["x"], 10)))
    try:
        run_bridge("codex", "pre-bash", b"{}", tmp_path)
    except StateError as exc:
        assert "timed out" in str(exc)
    else:
        raise AssertionError("expected timeout")


def test_bridge_redaction_and_exit_code_propagation(tmp_path, monkeypatch):
    completed = vendor_hook.subprocess.CompletedProcess(["bridge"], 7, stdout=b"SENTINEL_SECRET", stderr=b"token=SENTINEL_SECRET")
    monkeypatch.setattr(vendor_hook, "run_bridge", lambda *_args: completed)
    result = runner.invoke(
        app,
        ["hook", "bridge", "codex", "pre-bash"],
        input="{}",
        env={"AGENTOS_TEST_SECRET": "SENTINEL_SECRET"},
    )
    assert result.exit_code == 7
    assert "SENTINEL_SECRET" not in result.output
    assert "[REDACTED]" in result.output


def test_self_host_detection_requires_loaded_source_root(tmp_path, monkeypatch):
    source = tmp_path / "source"
    (source / "scripts").mkdir(parents=True)
    (source / "pyproject.toml").write_text('[project]\nname = "agentos"\n')
    (source / "scripts" / "install-hooks.sh").write_text("#!/bin/sh\n")
    monkeypatch.setattr(setup, "_source_checkout_root", lambda: source)
    assert setup._is_self_host_target(source)
    lookalike = tmp_path / "lookalike"
    lookalike.mkdir()
    assert not setup._is_self_host_target(lookalike)


def test_self_host_uses_only_trusted_installer(tmp_path, monkeypatch):
    source = tmp_path / "source"
    (source / "scripts").mkdir(parents=True)
    (source / "pyproject.toml").write_text('[project]\nname = "agentos"\n')
    installer = source / "scripts" / "install-hooks.sh"
    installer.write_text("#!/bin/sh\n")
    monkeypatch.setattr(setup, "_source_checkout_root", lambda: source)
    monkeypatch.setattr(setup, "_root", lambda _path: source)
    install = mock.Mock()
    bootstrap = mock.Mock()
    monkeypatch.setattr(setup.subprocess, "run", install)
    monkeypatch.setattr(setup, "_bootstrap_project", bootstrap)
    result = runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(tmp_path / "home")})
    assert result.exit_code == 0, result.output
    install.assert_called_once_with(["bash", str(installer)], cwd=source, check=False)
    bootstrap.assert_not_called()


def test_setup_docs_cover_global_install_and_recovery():
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    getting_started = (root / "docs" / "getting-started.md").read_text(encoding="utf-8")
    reference = (root / "docs" / "cli-reference.md").read_text(encoding="utf-8")
    assert "uv tool install agentos" in getting_started
    assert "agentos setup --path <project-dir>" in getting_started
    assert "uv tool update-shell" in getting_started
    assert "skipped_vendors" in getting_started
    assert "agentos doctor" in getting_started
    assert "uv run agentos doctor" not in getting_started
    assert "agentos doctor" in readme
    assert "uv run agentos doctor" not in readme
    assert "agentos hook bridge" in reference
