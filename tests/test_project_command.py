from pathlib import Path

from typer.testing import CliRunner

from agentos.cli import app

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
    result = runner.invoke(app, ["project", "init", "--path", str(project), "--json"], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 0 and '"current"' in result.stdout
    assert (project / ".agentos" / "agentos-project" / "skills" / "source" / "SKILL.md").is_file()
    assert not (project / ".agentos" / "config.toml").exists()


def test_setup_installs_default_skills_for_project_init(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    assert runner.invoke(app, ["setup"], env={"AGENTOS_HOME": str(home)}).exit_code == 0
    result = runner.invoke(app, ["project", "init", "--path", str(project)], env={"AGENTOS_HOME": str(home)})
    assert result.exit_code == 0
    assert (home / "core" / ".agents" / "skills" / "xlsx" / "SKILL.md").is_file()


def test_project_status_detects_stale_global_skill(tmp_path):
    home, project, source = tmp_path / "home", tmp_path / "project", tmp_path / "source"
    project.mkdir()
    _skill(home, source)
    assert runner.invoke(app, ["project", "init", "--path", str(project)], env={"AGENTOS_HOME": str(home)}).exit_code == 0
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
