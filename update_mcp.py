from pathlib import Path

content = Path(".agents/skills/harness/run-all-tests/tests/test_mcp_lifecycle.py").read_text()
new_content = content.replace(
    'return relative_path\n\n\ndef mcp_config_path(root: Path) -> Path:',
    '''import sys
    script_dir = root / ".agents" / "skills" / "harness" / "writing-plans" / "scripts"
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    import review_artifacts
    review_artifacts.record_review(
        root=root, plan_path=relative_path, reviewer="plan-reviewer", result="PASS",
        reviewer_id="rev1", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    review_artifacts.record_review(
        root=root, plan_path=relative_path, reviewer="principle-auditor", result="PASS",
        reviewer_id="rev2", reviewer_source="src", summary="sum", implementer_id="impl1"
    )
    return relative_path


def mcp_config_path(root: Path) -> Path:'''
)
Path(".agents/skills/harness/run-all-tests/tests/test_mcp_lifecycle.py").write_text(new_content)
