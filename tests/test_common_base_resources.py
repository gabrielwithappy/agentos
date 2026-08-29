import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app
from agentos.terminal.base_resources import (
    BASE_MANIFEST_SCHEMA,
    BASE_MANIFEST_NAME,
    harness_manifest,
    harness_sources,
    install_harness_base,
    read_harness_manifest,
    resource_digest,
)


runner = CliRunner()


def test_source_harness_bundle_has_stable_agent_and_skill_digest():
    agents, skills = harness_sources()
    manifest = harness_manifest(agents, skills)

    assert manifest["schema_version"] == BASE_MANIFEST_SCHEMA
    assert manifest["agents"] == {"harness": resource_digest(agents)}
    assert manifest["skills"] == {"harness": resource_digest(skills)}
    assert (agents / "plan-reviewer.md").is_file()
    assert (skills / "writing-plans" / "SKILL.md").is_file()


def test_setup_installs_common_base_and_writes_manifest(tmp_path):
    home = tmp_path / "home"
    result = runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)})

    assert result.exit_code == 0, result.output
    manifest_path = home / "core" / ".agents" / BASE_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == BASE_MANIFEST_SCHEMA
    assert (home / "core" / ".agents" / "agents" / "harness" / "plan-reviewer.md").is_file()
    assert (home / "core" / ".agents" / "skills" / "harness" / "writing-plans" / "SKILL.md").is_file()
    assert read_harness_manifest(home) == manifest


def test_install_harness_base_replaces_only_managed_base(tmp_path):
    home = tmp_path / "home"
    install_harness_base(home)
    custom = home / "core" / ".agents" / "skills" / "custom" / "SKILL.md"
    custom.parent.mkdir()
    custom.write_text("custom\n", encoding="utf-8")

    install_harness_base(home)

    assert custom.read_text(encoding="utf-8") == "custom\n"


def test_read_harness_manifest_rejects_invalid_schema(tmp_path):
    root = tmp_path / "home" / "core" / ".agents"
    root.mkdir(parents=True)
    (root / BASE_MANIFEST_NAME).write_text('{"schema_version":"wrong"}\n', encoding="utf-8")

    try:
        read_harness_manifest(tmp_path / "home")
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("invalid manifest was accepted")


def test_packaged_copy_has_same_manifest(tmp_path, monkeypatch):
    source_agents, source_skills = harness_sources()
    packaged = tmp_path / "packaged"
    shutil.copytree(source_agents, packaged / "agents" / "harness")
    shutil.copytree(source_skills, packaged / "skills" / "harness")
    from agentos.terminal import base_resources

    monkeypatch.setattr(base_resources, "_source_checkout_root", lambda: None)
    monkeypatch.setattr(base_resources, "_packaged_harness_root", lambda: packaged)

    assert harness_manifest(*base_resources.harness_sources()) == harness_manifest(source_agents, source_skills)
