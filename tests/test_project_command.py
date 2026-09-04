from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app
from agentos.commands import project as project_command

runner = CliRunner()


def _skill(home: Path, source: Path) -> None:
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0
    assert runner.invoke(app, ["skill", "install", str(source)], env={"AGENTOS_HOME": str(home)}).exit_code == 0


def test_project_init_is_opt_in_and_status_is_cwd_scoped(tmp_path):
    home, project, source = tmp_path / "home", tmp_path / "project", tmp_path / "source"
    project.mkdir()
    _skill(home, source)
    before = runner.invoke(app, ["project", "status", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})
    assert '"not_initialized"' in before.stdout
    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json", "--skills", "source"], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 0 and '"current"' in result.stdout
    assert (project / ".agentos" / "agentos-project" / "skills" / "source" / "SKILL.md").is_file()
    assert not (project / ".agentos" / "config.toml").exists()
    assert (project / ".agentos" / "project" / "00-project-index.md").is_file()
    assert '"project_documents": {"missing": [], "state": "current"}' in result.stdout


def test_project_init_preserves_existing_and_partial_project_documents(tmp_path):
    home, project, source = tmp_path / "home", tmp_path / "project", tmp_path / "source"
    project.mkdir()
    _skill(home, source)
    documents = project / ".agentos" / "project"
    documents.mkdir(parents=True)
    sentinel = documents / "00-project-index.md"
    sentinel.write_text("user-owned\n", encoding="utf-8")

    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})

    assert result.exit_code == 0, result.output
    assert sentinel.read_text(encoding="utf-8") == "user-owned\n"
    assert '"state": "current"' in result.stdout
    assert '"missing"' in result.stdout


def test_project_init_applies_harness_resources_to_runtime_surface(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0

    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})

    assert result.exit_code == 0, result.output
    assert '"agents": ["harness"]' in result.stdout
    assert (project / ".agents" / "agents" / "harness" / "plan-reviewer.md").is_file()
    assert (project / ".agents" / "skills" / "harness" / "SKILL.md").is_file()
    assert (project / ".agents" / "skills" / "harness" / "brain" / "SKILL.md").is_file()
    assert (project / ".agents" / "skills" / "harness" / "agentos-core-guidance" / "SKILL.md").is_file()


def test_project_init_keeps_harness_root_nested_without_flat_collision(tmp_path, monkeypatch):
    project = tmp_path / "project"
    global_skills = tmp_path / "global-skills"
    harness_agents = tmp_path / "harness-agents"
    harness_skills = tmp_path / "harness-skills"
    project.mkdir()
    global_skills.mkdir()
    (global_skills / "optional").mkdir()
    (global_skills / "optional" / "SKILL.md").write_text(
        "---\nname: optional\ndescription: optional\n---\n", encoding="utf-8"
    )
    harness_agents.mkdir()
    (harness_agents / "plan-reviewer.md").write_text("agent\n", encoding="utf-8")
    (harness_skills / "child").mkdir(parents=True)
    (harness_skills / "SKILL.md").write_text(
        "---\nname: harness\ndescription: harness\n---\n", encoding="utf-8"
    )
    (harness_skills / "child" / "SKILL.md").write_text(
        "---\nname: child\ndescription: child\n---\n", encoding="utf-8"
    )
    from agentos.terminal import skills, catalog
    monkeypatch.setattr(project_command, "global_skills_dir", lambda: global_skills)
    monkeypatch.setattr(skills, "global_skills_dir", lambda home=None: global_skills)
    monkeypatch.setattr(catalog, "global_skills_dir", lambda home=None: global_skills)
    monkeypatch.setattr(project_command, "_harness_sources", lambda: (harness_agents, harness_skills))
    monkeypatch.setattr(project_command, "_settings_digest", lambda: "test")

    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json", "--skills", "optional"])

    assert result.exit_code == 0, result.output
    assert (project / ".agents" / "skills" / "optional" / "SKILL.md").is_file()
    assert (project / ".agents" / "skills" / "harness" / "SKILL.md").is_file()
    assert (project / ".agents" / "skills" / "harness" / "child" / "SKILL.md").is_file()
    assert not (project / ".agents" / "skills" / "harness" / "harness").exists()


def test_proj_is_project_init_alias(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0

    result = runner.invoke(app, ["proj", "init", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})

    assert result.exit_code == 0, result.output
    assert (project / ".agents" / "agents" / "harness" / "plan-reviewer.md").is_file()


def test_project_init_uses_packaged_harness_when_checkout_is_unavailable(tmp_path, monkeypatch):
    home, project, packaged = tmp_path / "home", tmp_path / "project", tmp_path / "package"
    project.mkdir()
    (packaged / "agents").mkdir(parents=True)
    (packaged / "skills").mkdir()
    source_root = Path(__file__).resolve().parents[1]
    import shutil
    shutil.copytree(source_root / ".agents" / "agents" / "harness", packaged / "agents" / "harness")
    shutil.copytree(source_root / ".agents" / "skills" / "harness", packaged / "skills" / "harness")
    shutil.copytree(source_root / "docs" / "project", packaged / "_project_docs")
    monkeypatch.setattr(project_command, "_source_checkout_root", lambda: None)
    monkeypatch.setattr(project_command, "_packaged_harness_root", lambda: packaged)
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0

    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})

    assert result.exit_code == 0, result.output
    assert (project / ".agents" / "agents" / "harness" / "plan-reviewer.md").is_file()
    assert (project / ".agents" / "skills" / "harness" / "brain" / "SKILL.md").is_file()


def test_project_init_preserves_unmanaged_agents_files(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    custom = project / ".agents" / "README.md"
    custom.parent.mkdir()
    custom.write_text("user-owned\n", encoding="utf-8")
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0

    result = runner.invoke(app, ["project", "init", "--path", str(project)], env={"AGENTOS_HOME": str(home)})

    assert result.exit_code == 0, result.output
    assert custom.read_text(encoding="utf-8") == "user-owned\n"


def test_setup_installs_default_skills_for_project_init(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0
    result = runner.invoke(app, ["project", "init", "--path", str(project)], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 0
    assert (home / "core" / ".agents" / "skills" / "harness" / "agentos-core-guidance" / "SKILL.md").is_file()


def test_project_status_detects_stale_global_skill(tmp_path):
    home, project, source = tmp_path / "home", tmp_path / "project", tmp_path / "source"
    project.mkdir()
    _skill(home, source)
    assert runner.invoke(app, ["project", "init", "--path", str(project), "--skills", "source"], env={"AGENTOS_HOME": str(home)}).exit_code == 0
    (home / "core" / ".agents" / "skills" / "source" / "SKILL.md").write_text("changed", encoding="utf-8")
    result = runner.invoke(app, ["project", "status", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})
    assert '"stale_global_skills"' in result.stdout


def test_skill_status_reports_stale_and_missing_source(tmp_path):
    home, source = tmp_path / "home", tmp_path / "source"
    _skill(home, source)
    (source / "SKILL.md").write_text("updated", encoding="utf-8")
    stale = runner.invoke(app, ["skill", "status", "--json"], env={"AGENTOS_HOME": str(home)})
    assert '"stale"' in stale.stdout
    import shutil
    shutil.rmtree(source)
    unavailable = runner.invoke(app, ["skill", "status", "--json"], env={"AGENTOS_HOME": str(home)})
    assert '"source_unavailable"' in unavailable.stdout


def test_project_init_rejects_symlink_path(tmp_path):
    home, project, source, link = tmp_path / "home", tmp_path / "project", tmp_path / "source", tmp_path / "link"
    project.mkdir()
    _skill(home, source)
    link.symlink_to(project, target_is_directory=True)
    result = runner.invoke(app, ["project", "init", "--path", str(link)], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 2
    assert "regular directory" in result.stderr

def test_project_init_skills_rejection(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    # Empty setup
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0
    # Add a custom skill to global so available is NOT empty
    source = tmp_path / "source"
    _skill(home, source)
    
    # Try invalid skill when installed choices are present
    result = runner.invoke(app, ["project", "init", "--path", str(project), "--skills", "invalid"], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 2
    assert "Installed choices are" in result.stderr
    assert "Next: rerun with agentos project init --skills <available-name>" in result.stderr

    # Try invalid skill when NO installed choices are present
    import shutil
    shutil.rmtree(home / "core" / ".agents" / "skills" / "demo", ignore_errors=True)
    # also remove any default ones loaded by setup? we can just mock global_skills_dir to return empty
    
def test_project_init_skills_rejection_empty(tmp_path, monkeypatch):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    from agentos.terminal import skills
    monkeypatch.setattr(skills, "global_skills_dir", lambda home=None: tmp_path / "empty")
    
    result = runner.invoke(app, ["project", "init", "--path", str(project), "--skills", "invalid"], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 2
    assert "Installed choices are: none." in result.stderr
    assert "Next: rerun without --skills to continue with default harness skills" in result.stderr
