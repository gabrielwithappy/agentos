import re
text = open(".agents/skills/harness/writing-plans/scripts/review_artifacts.py").read()

new_code = '''def is_protected_change(text: str) -> bool:
    values = PROTECTED_CHANGE_RE.findall(text)
    if values and (len(set(values)) != 1 or len(values) > 1):
        raise ValueError("invalid-protected-metadata")
    return values and values[0] == "true"


def extract_declared_scope(text: str) -> set[str]:
    match = re.search(r"^- declared protected paths:\\s*(.+)$", text, re.MULTILINE)
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

# Replace the previous implementation
start = text.find("def is_protected_change")
end = text.find("def _load_artifact")
if start != -1 and end != -1:
    text = text[:start] + new_code + "\n\n\n" + text[end:]

# Update the call in check_plan
call_start = text.find("problem = _architect_approval_problem(")
if call_start != -1:
    call_end = text.find(")", call_start)
    text = text[:call_start] + "problem = _architect_approval_problem(\n                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)\n            " + text[call_end:]

open(".agents/skills/harness/writing-plans/scripts/review_artifacts.py", "w").write(text)
