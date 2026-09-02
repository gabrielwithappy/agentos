import re
text = open(".agents/skills/harness/writing-plans/scripts/review_artifacts.py").read()

# Add PROTECTED_CHANGE_RE
text = text.replace(
'''USABILITY_HEADER_RE = re.compile(
    r"^> (?:\*\*usability_review_required:\*\*|usability_review_required:) (true|false)(?:\s*<br\s*/?>)?$",
    re.MULTILINE,
)''',
'''USABILITY_HEADER_RE = re.compile(
    r"^> (?:\*\*usability_review_required:\*\*|usability_review_required:) (true|false)(?:\s*<br\s*/?>)?$",
    re.MULTILINE,
)
PROTECTED_CHANGE_RE = re.compile(
    r"^> (?:\*\*protected_change:\*\*|protected_change:) (true|false)(?:\s*<br\s*/?>)?$",
    re.MULTILINE,
)'''
)

new_code = '''def is_protected_change(text: str) -> bool:
    values = PROTECTED_CHANGE_RE.findall(text)
    if values and (len(set(values)) != 1 or len(values) > 1):
        raise ValueError("invalid-protected-metadata")
    return values and values[0] == "true"


def extract_declared_scope(text: str) -> set[str]:
    match = re.search(r"^- declared protected paths:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return set()
    line = match.group(1)
    paths = set(re.findall(r"`([^`]+)`", line))
    if "manifest update" in line or "manifest data" in line:
        paths.add("manifest update")
    return paths


def _architect_approval_problem(
    artifact: dict[str, Any],
    expected_plan_path: str,
    expected_hash: str,
    root: Path,
    expected_scope: set[str],
) -> str | None:
    if artifact.get("schema") != "harness-architect-approval-v1":
        return "schema-mismatch"
    if artifact.get("plan_path") != expected_plan_path:
        return "plan-path-mismatch"
    if artifact.get("plan_sha256") != expected_hash:
        return "plan-sha256-mismatch"
    if artifact.get("reviewer_id") != "harness-architect":
        return "missing-or-unauthorized-architect-provenance"
    if artifact.get("reviewer_source") != "subagent":
        return "unsupported-reviewer-source"
    if artifact.get("decision") != "APPROVED":
        return "result-not-pass"
    
    implementer_id = artifact.get("implementer_id")
    if not implementer_id:
        return "missing-implementer-id"
    if implementer_id == artifact.get("reviewer_id"):
        return "reviewer-equals-implementer"

    auth_scope = artifact.get("authorized_scope")
    if not isinstance(auth_scope, list) or set(auth_scope) != expected_scope:
        return "extra-approval-scope"
        
    try:
        import json
        version_data = json.loads((root / ".agents" / "_version.json").read_text(encoding="utf-8"))
        if artifact.get("reviewer_id") not in version_data.get("authorized_architects", []):
            return "missing-or-unauthorized-architect-provenance"
    except Exception:
        return "missing-or-unauthorized-architect-provenance"

    return None'''

start = text.find("def _load_artifact")
if start != -1:
    text = text[:start] + new_code + "\n\n\n" + text[start:]

text = text.replace(
'''    for reviewer in required:
        artifact_path = artifacts_dir / f"{reviewer}.json"
        if not artifact_path.is_file():
            missing.append(reviewer)
            continue
        artifact = _load_artifact(artifact_path)
        problem = _artifact_problem(artifact, reviewer, rel_path, expected_snapshot)
        if problem:
            invalid[reviewer] = problem
            continue
        reviewer_id = str(artifact["reviewer_id"])
        if reviewer_id in reviewer_ids.values():
            invalid[reviewer] = "duplicate-reviewer-id"
            continue
        reviewer_ids[reviewer] = reviewer_id
        artifacts[reviewer] = artifact

    valid = not missing and not invalid''',
'''    for reviewer in required:
        artifact_path = artifacts_dir / f"{reviewer}.json"
        if not artifact_path.is_file():
            missing.append(reviewer)
            continue
        artifact = _load_artifact(artifact_path)
        problem = _artifact_problem(artifact, reviewer, rel_path, expected_snapshot)
        if problem:
            invalid[reviewer] = problem
            continue
        reviewer_id = str(artifact["reviewer_id"])
        if reviewer_id in reviewer_ids.values():
            invalid[reviewer] = "duplicate-reviewer-id"
            continue
        reviewer_ids[reviewer] = reviewer_id
        artifacts[reviewer] = artifact

    is_protected = is_protected_change(text)
    if is_protected:
        artifact_path = artifacts_dir / "harness-architect-approval.json"
        if not artifact_path.is_file():
            missing.append("harness-architect-approval")
        else:
            artifact = _load_artifact(artifact_path)
            problem = _architect_approval_problem(
                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)
            )
            if problem:
                invalid["harness-architect-approval"] = problem
            else:
                artifacts["harness-architect-approval"] = artifact

    valid = not missing and not invalid'''
)

open(".agents/skills/harness/writing-plans/scripts/review_artifacts.py", "w").write(text)
