import pytest
from agentos.terminal.paths import StateError
from agentos.terminal.catalog import (
    load_catalog, load_available_optional_skills, 
    validate_selection, parse_skills_input, SkillMetadata
)

def test_load_catalog():
    catalog = load_catalog()
    assert "future-slide" in catalog
    assert "harness" in catalog
    assert catalog["harness"].is_harness
    assert not catalog["future-slide"].is_harness

def test_load_available_optional_skills(tmp_path):
    # Empty home -> no global skills
    skills = load_available_optional_skills(home=tmp_path)
    assert len(skills) == 0

def test_parse_skills_input():
    assert parse_skills_input(None) is None
    assert parse_skills_input("none") == []
    assert parse_skills_input("NONE") == []
    assert parse_skills_input("a, b,c") == ["a", "b", "c"]
    assert parse_skills_input("a,,b") == ["a", "b"]

def test_validate_selection():
    available = [
        SkillMetadata("a", "summary", "기타", False),
        SkillMetadata("b", "summary", "기타", False),
    ]
    
    # Valid
    assert validate_selection(["a"], available) == ["a"]
    assert validate_selection(["a", "b"], available) == ["a", "b"]
    assert validate_selection([], available) == []
    
    # Invalid (unknown)
    with pytest.raises(StateError, match="is not installed as an optional project skill"):
        validate_selection(["c"], available)
        
    # Invalid (duplicate)
    with pytest.raises(StateError, match="Duplicate skill in selection"):
        validate_selection(["a", "a"], available)

def test_catalog_only_skill_not_in_available(tmp_path):
    # If home=tmp_path, then global_skills_dir is empty (nothing installed)
    # Therefore, load_available_optional_skills should return empty list
    skills = load_available_optional_skills(home=tmp_path)
    assert len(skills) == 0

    # Let's mock a global installation of 'future-slide' only
    global_dir = tmp_path / "core" / ".agents" / "skills"
    skill_dir = global_dir / "future-slide"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---")
    
    skills2 = load_available_optional_skills(home=tmp_path)
    names = [s.name for s in skills2]
    assert "future-slide" in names
    assert "codex-imagegen-2" not in names # catalog has it, but not installed
