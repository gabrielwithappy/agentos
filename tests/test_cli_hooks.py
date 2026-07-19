import os
from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app
from agentos.terminal.hooks import HookError, apply_input_hooks, effective_hooks
from agentos.terminal.paths import initialize_state

runner = CliRunner()


def test_default_hook_registry_ordering(tmp_path):
    initialize_state(tmp_path)
    rows = effective_hooks(tmp_path)
    assert [row.name for row in rows if row.phase == "input"] == [
        "trim_whitespace",
        "reject_empty",
        "max_input_chars",
        "prepend_context_file",
    ]


def test_reject_empty_and_trim(tmp_path):
    initialize_state(tmp_path)
    assert apply_input_hooks("  hello  ", tmp_path) == "hello"
    try:
        apply_input_hooks("   ", tmp_path)
    except HookError as exc:
        assert exc.hook == "reject_empty"
    else:
        raise AssertionError("expected HookError")


def test_enable_disable_hook(tmp_path):
    env = {"AGENTOS_HOME": str(tmp_path)}
    runner.invoke(app, ["setup"], env=env)
    result = runner.invoke(app, ["hook", "disable", "reject_empty"], env=env)
    assert result.exit_code == 0
    assert "Disabled hook reject_empty" in result.stdout
    assert apply_input_hooks("   ", tmp_path) == ""


def test_context_hook_requires_direct_md_file(tmp_path):
    initialize_state(tmp_path)
    config = tmp_path / "config.toml"
    config.write_text(
        'schema_version = "agentos.hooks/v1"\n\n'
        "[hooks.prepend_context_file]\n"
        "enabled = true\n"
        'value = "../secret.txt"\n',
        encoding="utf-8",
    )
    try:
        apply_input_hooks("hello", tmp_path)
    except HookError as exc:
        assert "direct .md basename" in str(exc)
    else:
        raise AssertionError("expected HookError")


def test_secret_sentinel_not_emitted(tmp_path):
    secret = os.environ.get("AGENTOS_TEST_SECRET", "SENTINEL_SECRET")
    initialize_state(tmp_path)
    result = runner.invoke(app, ["run", "--once", "hello", "--json"], env={"AGENTOS_HOME": str(tmp_path), "AGENTOS_TEST_SECRET": secret})
    assert result.exit_code == 0
    assert secret not in result.stdout
    assert secret not in result.stderr


def test_hook_config_show_prints_effective_toml(tmp_path):
    env = {"AGENTOS_HOME": str(tmp_path)}
    runner.invoke(app, ["setup"], env=env)
    result = runner.invoke(app, ["hook", "config", "show"], env=env)
    assert result.exit_code == 0
    assert 'schema_version = "agentos.hooks/v1"' in result.stdout
    assert "[hooks.reject_empty]" in result.stdout
    assert "timeout_ms = 2000" in result.stdout
