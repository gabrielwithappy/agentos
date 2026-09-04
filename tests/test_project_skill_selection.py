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
    skills = load_available_optional_skills(home=tmp_path)
    names = [s.name for s in skills]
    assert "future-slide" in names
    assert "harness" not in names
    assert "agentos-core-guidance" not in names

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
    with pytest.raises(StateError, match="Unknown or invalid skill selected"):
        validate_selection(["c"], available)
        
    # Invalid (duplicate)
    with pytest.raises(StateError, match="Duplicate skill in selection"):
        validate_selection(["a", "a"], available)
