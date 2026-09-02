import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from agentos.terminal.paths import StateError
from agentos.terminal.skills import global_skills_dir

@dataclass(frozen=True)
class SkillMetadata:
    name: str
    summary: str
    group_kr: str
    is_harness: bool

CATEGORY_TO_KR = {
    "visual-design-html": "시각 디자인 (HTML/UI)",
    "text-and-ideation": "텍스트/아이디에이션",
    "visual-assets": "시각 에셋",
    "software-development": "소프트웨어 개발",
    "frontend": "프론트엔드",
    "productivity": "생산성",
    "diagramming": "다이어그램",
    "harness": "Harness",
}

def load_catalog() -> dict[str, SkillMetadata]:
    catalog_path = Path(str(files("catalog").joinpath("skills", "catalog.json")))
    if not catalog_path.is_file():
        raise StateError("catalog.json not found.")
    
    with catalog_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    result = {}
    for item in data.get("skills", []):
        name = item["name"]
        if name in result:
            raise StateError(f"Duplicate skill name in catalog: {name}")
        
        category = item.get("category", "")
        summary = item.get("summary", "")
        is_harness = category == "harness"
        group_kr = CATEGORY_TO_KR.get(category, "기타") if category else "기타"
        
        result[name] = SkillMetadata(name=name, summary=summary, group_kr=group_kr, is_harness=is_harness)
        
    return result

def load_available_optional_skills(home: Path | None = None) -> list[SkillMetadata]:
    catalog = load_catalog()
    
    # Exclude harness
    optional = {k: v for k, v in catalog.items() if not v.is_harness}
    
    # Also load custom global skills
    global_dir = global_skills_dir(home)
    if global_dir.is_dir():
        for item in global_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").is_file():
                if item.name not in optional and item.name not in catalog:
                    # Parse frontmatter for summary if possible, else default
                    summary = "Custom global skill"
                    try:
                        content = (item / "SKILL.md").read_text(encoding="utf-8")
                        for line in content.splitlines():
                            if line.startswith("description:"):
                                summary = line.split(":", 1)[1].strip().strip("'\"")
                                break
                    except Exception:
                        pass
                    optional[item.name] = SkillMetadata(
                        name=item.name,
                        summary=summary,
                        group_kr="기타",
                        is_harness=False
                    )
    
    return sorted(optional.values(), key=lambda x: (x.group_kr, x.name))

def validate_selection(selection: list[str], available: list[SkillMetadata]) -> list[str]:
    available_names = {s.name for s in available}
    seen = set()
    for s in selection:
        if s not in available_names:
            raise StateError(f"Unknown or invalid skill selected: {s}")
        if s in seen:
            raise StateError(f"Duplicate skill in selection: {s}")
        seen.add(s)
    return selection


def parse_skills_input(input_str: str | None) -> list[str] | None:
    if input_str is None:
        return None
    if input_str.strip().lower() == "none":
        return []
    return [s.strip() for s in input_str.split(",") if s.strip()]
