import json
from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app
from agentos.terminal.skills import DEFAULT_SKILL_NAMES


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".agents" / "skills" / "harness" / "agentos-core-guidance"
runner = CliRunner()


def test_core_guidance_skill_contract_and_eval_schema():
    text = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
    assert "name: agentos-core-guidance" in text
    for phrase in ("AGENTS.md", "Plan Quality Gate", "secret", "network", "project policy"):
        assert phrase in text
    data = json.loads((SOURCE / "evals" / "evals.json").read_text(encoding="utf-8"))
    assert data["skill_name"] == "agentos-core-guidance"
    assert 2 <= len(data["evals"]) <= 3
    assert all(item["prompt"] and item["expected_output"] and item["files"] == [] for item in data["evals"])


def test_core_guidance_is_harness_base_not_flat_default():
    assert "agentos-core-guidance" not in DEFAULT_SKILL_NAMES


def test_project_init_applies_core_guidance_without_agents_file(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    assert not (project / "AGENTS.md").exists()
    setup = runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)})
    assert setup.exit_code == 0, setup.output
    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 0, result.output
    installed = project / ".agents" / "skills" / "harness" / "agentos-core-guidance" / "SKILL.md"
    assert installed.is_file()
    assert not (project / "AGENTS.md").exists()
