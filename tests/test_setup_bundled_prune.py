from __future__ import annotations

import json
from pathlib import Path

from agentos.terminal.paths import initialize_state, atomic_write_json
from agentos.terminal.skills import (
    install_bundled_skills,
    global_skills_dir,
    _manifest_path,
    skill_digest,
)


def test_install_bundled_skills_prunes_obsolete_bundled_skill_and_preserves_custom(tmp_path):
    home = tmp_path / "home"
    dest = initialize_state(home)

    # First initial install
    summary1 = install_bundled_skills(dest)
    assert summary1.installed > 0
    assert summary1.pruned == 0

    skills_root = global_skills_dir(dest)
    manifest_file = _manifest_path(dest)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    # Create a simulated obsolete bundled skill
    obsolete_dir = skills_root / "obsolete-bundled-skill"
    obsolete_dir.mkdir()
    (obsolete_dir / "SKILL.md").write_text("# Obsolete Skill\n", encoding="utf-8")
    obsolete_digest = skill_digest(obsolete_dir)
    manifest["skills"]["obsolete-bundled-skill"] = {
        "digest": obsolete_digest,
        "source": str(obsolete_dir),
        "source_digest": obsolete_digest,
        "origin": "bundled",
    }

    # Create a simulated custom external skill
    custom_dir = skills_root / "my-custom-skill"
    custom_dir.mkdir()
    (custom_dir / "SKILL.md").write_text("# My Custom Skill\n", encoding="utf-8")
    custom_digest = skill_digest(custom_dir)
    manifest["skills"]["my-custom-skill"] = {
        "digest": custom_digest,
        "source": str(custom_dir),
        "source_digest": custom_digest,
        "origin": "external",
    }

    atomic_write_json(manifest_file, manifest)

    # Second install: should prune obsolete bundled skill, and preserve custom skill
    summary2 = install_bundled_skills(dest)
    assert summary2.pruned == 1
    assert not obsolete_dir.exists()
    assert custom_dir.exists()

    new_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert "obsolete-bundled-skill" not in new_manifest["skills"]
    assert "my-custom-skill" in new_manifest["skills"]
