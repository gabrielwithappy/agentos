text = open(".agents/skills/harness/writing-plans/scripts/review_artifacts.py").read()
text = text.replace(
    "problem = _architect_approval_problem(\n                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)\n            , root\n            )",
    "problem = _architect_approval_problem(\n                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)\n            )"
)
text = text.replace(
    "problem = _architect_approval_problem(\n                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)\n            ext), root\n            )",
    "problem = _architect_approval_problem(\n                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)\n            )"
)

# Actually, I can just replace everything between _architect_approval_problem and the matching )
import re
text = re.sub(r'problem = _architect_approval_problem\([^\)]+\)[^\)]*\)', 'problem = _architect_approval_problem(\n                artifact, rel_path, plan_hash(text), root, extract_declared_scope(text)\n            )', text)

# Let's just be careful and rewrite the block from scratch
text = text.replace("is_protected = is_protected_change(text)\n    if is_protected:\n        artifact_path = artifacts_dir / \"harness-architect-approval.json\"", "###MARK###")
if "###MARK###" in text:
    pass
