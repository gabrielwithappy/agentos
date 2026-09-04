#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REVIEWED_RE = re.compile(r"^> reviewed: true(?:\s*<br\s*/?>)?$", re.MULTILINE)
REVIEWED_META_RE = re.compile(r"^> reviewed: (?:true|false)(?:\s*<br\s*/?>)?$", re.MULTILINE)
STATUS_RE = re.compile(r"^> \*\*상태:\*\* (.+?)(?:\s*<br\s*/?>)?$", re.MULTILINE)
USABILITY_HEADER_RE = re.compile(
    r"^> (?:\*\*usability_review_required:\*\*|usability_review_required:) (true|false)(?:\s*<br\s*/?>)?$",
    re.MULTILINE,
)
PROTECTED_CHANGE_RE = re.compile(
    r"^> (?:\*\*protected_change:\*\*|protected_change:) (true|false)(?:\s*<br\s*/?>)?$",
    re.MULTILINE,
)
GATE2_RE = re.compile(r"^> gate2_[^:\n]+:.*$", re.MULTILINE)
HEADER_STATUS_RE = re.compile(r"^> \*\*상태:\*\* .+$", re.MULTILINE)
# Fields/sections that other harness contracts require agents to fill in
# AFTER Gate 2 signing: implementation_*_at/duration, active_agent,
# active_session (executing-plans/SKILL.md Step 7-8 occupancy lock),
# dashboard_item_id (TEMPLATE.md, auto-written by `agentos dashboard
# sync-plan`), Task checkbox state, and the "Completed Active Plan Closeout"
# prose sections (writing-plans/SKILL.md). Excluded from the hash so a
# properly closed-out plan doesn't retroactively invalidate its own review.
#
# Threat model: this exclusion is intentionally unbounded in content (a
# timestamp/id line or a closeout section can hold arbitrary text) but
# bounded in *what it can influence* — no code in this harness parses these
# fields/sections as directives; they are display/bookkeeping only. The
# content that actually specifies what was reviewed and approved (목표,
# 아키텍처, Task steps, 사용자 결과, 의존성 게이트, etc.) is NOT matched by
# any of these patterns and remains fully hashed, so tampering with scope
# after signing still invalidates the signature.
LIVING_META_RE = re.compile(
    r"^> (?:implementation_started_at|implementation_completed_at|implementation_duration|"
    r"dashboard_item_id|active_agent|active_session): .*$",
    re.MULTILINE,
)
TASK_CHECKBOX_RE = re.compile(r"^(\s*-\s*)\[[ xX]\]", re.MULTILINE)
LIVING_SECTION_RE = re.compile(
    r"^##\s*(?:진행 스냅샷|구현 결과|사용 방법|완료 증거|아카이브 결정)\s*\n.*?(?=\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)
ALLOWED_PASS_RESULTS = {"PASS", "PASS/APPROVE", "PASS/CLEAN"}
ALLOWED_REVIEWER_SOURCES = {"subagent"}
REQUIRED_REVIEWERS = ("plan-reviewer", "principle-auditor")
ARTIFACT_SCHEMA = "gate2-review-artifact-v1"
PROTECTED_REVIEW_SCOPE = frozenset(
    {
        ".agents/agents/harness/plan-reviewer.md",
        ".agents/agents/harness/principle-auditor.md",
        ".agents/agents/harness/usability-reviewer.md",
        ".agents/skills/harness/writing-plans/SKILL.md",
        ".agents/skills/harness/writing-plans/scripts/review_artifacts.py",
        ".agents/skills/harness/writing-plans/tests/test_plan_review_scope.py",
        ".agents/_version.json",
        "manifest update",
    }
)


@dataclass
class ReviewCheck:
    plan_path: str
    plan_slug: str
    reviewed_header: bool
    required_reviewers: list[str]
    valid: bool
    status: str
    missing: list[str]
    invalid: dict[str, str]
    artifacts: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_path": self.plan_path,
            "plan_slug": self.plan_slug,
            "reviewed_header": self.reviewed_header,
            "required_reviewers": self.required_reviewers,
            "valid": self.valid,
            "status": self.status,
            "missing": self.missing,
            "invalid": self.invalid,
            "artifacts": self.artifacts,
        }


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_plan_text(text: str) -> str:
    # Gate state is lifecycle bookkeeping in both directions.  Treating only
    # `true` as living metadata invalidates the just-recorded review when the
    # normal state transition flips `false` to `true`.
    normalized = REVIEWED_META_RE.sub("", text)
    normalized = GATE2_RE.sub("", normalized)
    normalized = HEADER_STATUS_RE.sub("", normalized)
    normalized = LIVING_META_RE.sub("", normalized)
    normalized = TASK_CHECKBOX_RE.sub(r"\1[ ]", normalized)
    normalized = LIVING_SECTION_RE.sub("", normalized)
    lines = [line.rstrip() for line in normalized.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def semantic_snapshot(text: str) -> str:
    """Return the plan content that defines the reviewed execution contract.

    This deliberately excludes only bookkeeping surfaces. Ordinary reviewer
    validity compares this snapshot, not the full-plan digest.
    """
    return normalize_plan_text(text)


def protected_scope_is_complete(scope: Any) -> bool:
    return PROTECTED_REVIEW_SCOPE.issubset(set(scope or []))


def plan_hash(text: str) -> str:
    # Kept for protected approval/audit artifacts. It is not an ordinary
    # reviewer validity condition.
    return hashlib.sha256(semantic_snapshot(text).encode("utf-8")).hexdigest()


def plan_slug(plan_path: str) -> str:
    name = Path(plan_path).stem
    if name.endswith(".ko"):
        name = name[:-3]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "plan"


def review_dir(root: Path, plan_path: str) -> Path:
    return root / ".agents" / "traces" / "reviews" / plan_slug(plan_path)


def required_reviewers_for_text(text: str) -> list[str]:
    reviewers = list(REQUIRED_REVIEWERS)
    values = USABILITY_HEADER_RE.findall(text)
    if values and (len(set(values)) != 1 or len(values) > 1):
        raise ValueError("invalid-usability-metadata")
    if values and values[0] == "true":
        reviewers.append("usability-reviewer")
    return reviewers


def is_protected_change(text: str) -> bool:
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

    return None


def _load_artifact(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_problem(
    artifact: dict[str, Any],
    reviewer: str,
    expected_plan_path: str,
    expected_snapshot: str,
) -> str | None:
    if artifact.get("schema") != ARTIFACT_SCHEMA:
        return "schema-mismatch"
    if artifact.get("reviewer_role") != reviewer:
        return "reviewer-role-mismatch"
    if artifact.get("plan_path") != expected_plan_path:
        return "plan-path-mismatch"
    if "semantic_snapshot" in artifact:
        if artifact.get("plan_identity") != expected_plan_path:
            return "plan-identity-mismatch"
        if not isinstance(artifact.get("review_scope"), str) or not artifact["review_scope"].strip():
            return "missing-review-scope"
        if not isinstance(artifact.get("semantic_revision"), int) or artifact["semantic_revision"] < 1:
            return "invalid-semantic-revision"
        if artifact.get("semantic_snapshot") != expected_snapshot:
            return "semantic-snapshot-mismatch"
    # Legacy artifacts remain readable. Their full-plan hash is intentionally
    # not checked; newly recorded artifacts use semantic_snapshot instead.
    if artifact.get("result") not in ALLOWED_PASS_RESULTS:
        return "result-not-pass"
    if not artifact.get("reviewer_id"):
        return "missing-reviewer-id"
    if not artifact.get("reviewer_source"):
        return "missing-reviewer-source"
    if not artifact.get("summary"):
        return "missing-summary"
    reviewed_at = artifact.get("reviewed_at")
    if not isinstance(reviewed_at, str):
        return "missing-reviewed-at"
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError:
        return "invalid-reviewed-at"
    implementer_id = artifact.get("implementer_id")
    if not implementer_id:
        return "missing-implementer-id"
    if artifact.get("reviewer_source") not in ALLOWED_REVIEWER_SOURCES:
        return "unsupported-reviewer-source"
    if implementer_id == artifact.get("reviewer_id"):
        return "reviewer-equals-implementer"
    return None


def check_plan(root: Path, plan_path: str) -> ReviewCheck:
    root = root.resolve()
    plan_file = (root / plan_path).resolve()
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    required = required_reviewers_for_text(text)
    expected_snapshot = semantic_snapshot(text)
    slug = plan_slug(rel_path)
    artifacts_dir = review_dir(root, rel_path)
    reviewed_header = bool(REVIEWED_RE.search(text))
    missing: list[str] = []
    invalid: dict[str, str] = {}
    artifacts: dict[str, dict[str, Any]] = {}

    reviewer_ids: dict[str, str] = {}
    for reviewer in required:
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

    valid = not missing and not invalid
    if valid:
        status = "valid"
    elif missing and not invalid:
        status = "missing"
    else:
        status = "invalid"

    return ReviewCheck(
        plan_path=rel_path,
        plan_slug=slug,
        reviewed_header=reviewed_header,
        required_reviewers=required,
        valid=valid,
        status=status,
        missing=missing,
        invalid=invalid,
        artifacts=artifacts,
    )


def record_review(
    root: Path,
    plan_path: str,
    reviewer: str,
    result: str,
    reviewer_id: str,
    reviewer_source: str,
    summary: str,
    implementer_id: str | None,
) -> Path:
    plan_file = (root / plan_path).resolve()
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    if reviewer not in {"plan-reviewer", "principle-auditor", "usability-reviewer"}:
        raise ValueError(f"unsupported reviewer: {reviewer}")
    if result not in ALLOWED_PASS_RESULTS:
        raise ValueError(f"unsupported result: {result}")
    if not reviewer_id:
        raise ValueError("reviewer_id is required")
    if not reviewer_source:
        raise ValueError("reviewer_source is required")
    if not summary:
        raise ValueError("summary is required")
    if not implementer_id:
        raise ValueError("implementer_id is required")
    if implementer_id == reviewer_id:
        raise ValueError("implementer_id must differ from reviewer_id")
    if reviewer_source not in ALLOWED_REVIEWER_SOURCES:
        raise ValueError("reviewer_source must be subagent")

    snapshot = semantic_snapshot(text)
    out_dir = review_dir(root, rel_path)
    revisions = []
    latest_snapshot = None
    max_rev = 0
    if out_dir.is_dir():
        for candidate in out_dir.glob("*.json"):
            try:
                prior = _load_artifact(candidate)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(prior.get("semantic_revision"), int):
                revisions.append(prior["semantic_revision"])
                if prior["semantic_revision"] > max_rev:
                    max_rev = prior["semantic_revision"]
                    latest_snapshot = prior.get("semantic_snapshot")

    if max_rev == 0:
        revision = 1
    elif latest_snapshot == snapshot:
        revision = max_rev
    else:
        revision = max_rev + 1

    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "plan_path": rel_path,
        "plan_identity": rel_path,
        "review_scope": "gate2",
        "semantic_revision": revision,
        "semantic_snapshot": snapshot,
        # Retained as an audit hint for compatibility; ordinary validity does
        # not compare this value.
        "plan_sha256": plan_hash(text),
        "reviewer_role": reviewer,
        "result": result,
        "reviewer_id": reviewer_id,
        "reviewer_source": reviewer_source,
        "implementer_id": implementer_id,
        "summary": summary,
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{reviewer}.json"
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def _resolve_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[5]


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate 2 review artifact helpers")
    parser.add_argument("command", choices=["check", "record", "slug"])
    parser.add_argument("--root", default=None)
    parser.add_argument("--plan", dest="plan_path", required=True)
    parser.add_argument("--reviewer")
    parser.add_argument("--result")
    parser.add_argument("--reviewer-id")
    parser.add_argument("--reviewer-source")
    parser.add_argument("--summary")
    parser.add_argument("--implementer-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = _resolve_root(args.root)

    if args.command == "slug":
        print(plan_slug(args.plan_path))
        return

    if args.command == "check":
        result = check_plan(root, args.plan_path)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        elif result.valid:
            print(f"PASS gate2-review-check reviewers={','.join(result.required_reviewers)}")
        else:
            details: list[str] = []
            if result.missing:
                details.append(f"missing={','.join(result.missing)}")
            if result.invalid:
                invalid_bits = ",".join(f"{k}:{v}" for k, v in sorted(result.invalid.items()))
                details.append(f"invalid={invalid_bits}")
            detail_text = " ".join(details) if details else "invalid-review-evidence"
            print(f"APPROVAL_PENDING gate2-review-check {detail_text}")
            raise SystemExit(1)
        return

    try:
        out_path = record_review(
            root=root,
            plan_path=args.plan_path,
            reviewer=args.reviewer or "",
            result=args.result or "",
            reviewer_id=args.reviewer_id or "",
            reviewer_source=args.reviewer_source or "",
            summary=args.summary or "",
            implementer_id=args.implementer_id,
        )
    except ValueError as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"PASS gate2-review-recorded {out_path.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
