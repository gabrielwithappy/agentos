from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "catalog/skills/skill-catalog-viewer/scripts/generate_html.py"


def _viewer_module():
    spec = importlib.util.spec_from_file_location("skill_catalog_viewer", VIEWER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_viewer_renders_category_for_nested_harness_source(tmp_path: Path):
    viewer = _viewer_module()
    root = tmp_path / "repo"
    skill = root / ".agents/skills/harness/example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: example\ndescription: Example harness skill\n---\n",
        encoding="utf-8",
    )
    catalog = root / "catalog/skills/catalog.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "skills": [
                    {
                        "name": "example",
                        "category": "harness",
                        "summary": "Example",
                        "triggers": ["example"],
                        "source_path": ".agents/skills/harness/example",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "catalog.html"

    viewer.generate(root, catalog, output)

    rendered = output.read_text(encoding="utf-8")
    assert "Category:</strong> harness" in rendered
    assert ".agents/skills/harness/example" in rendered
    assert "example" in rendered


def test_viewer_rejects_catalog_source_outside_root(tmp_path: Path):
    viewer = _viewer_module()
    root = tmp_path / "repo"
    root.mkdir()
    catalog = root / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "skills": [
                    {
                        "name": "escape",
                        "category": "harness",
                        "source_path": "../outside",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(viewer.CatalogError, match="escapes root"):
        viewer.generate(root, catalog, tmp_path / "catalog.html")
