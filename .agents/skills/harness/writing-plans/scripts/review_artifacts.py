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
STATUS_RE = re.compile(r"^> \*\*상태:\*\* (.+?)(?:\s*<br\s*/?>)?$", re.MULTILINE)
USABILITY_REQUIRED_RE = re.compile(
    r"^> \*\*usability_review_required:\*\* true(?:\s*<br\s*/?>)?$", re.MULTILINE
)
GATE2_RE = re.compile(r"^> gate2_[^:\n]+:.*$", re.MULTILINE)
HEADER_STATUS_RE = re.compile(r"^> \*\*상태:\*\* .+$", re.MULTILINE)
ALLOWED_PASS_RESULTS = {"PASS", "PASS/APPROVE", "PASS/CLEAN"}
REQUIRED_REVIEWERS = ("plan-reviewer", "principle-auditor")
ARTIFACT_SCHEMA = "gate2-review-artifact-v1"


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
    normalized = REVIEWED_RE.sub("", text)
    normalized = GATE2_RE.sub("", normalized)
    normalized = HEADER_STATUS_RE.sub("", normalized)
    lines = [line.rstrip() for line in normalized.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def plan_hash(text: str) -> str:
    return hashlib.sha256(normalize_plan_text(text).encode("utf-8")).hexdigest()


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
    if USABILITY_REQUIRED_RE.search(text):
        reviewers.append("usability-reviewer")
    return reviewers


def _load_artifact(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_problem(
    artifact: dict[str, Any],
    reviewer: str,
    expected_plan_path: str,
    expected_hash: str,
) -> str | None:
    if artifact.get("schema") != ARTIFACT_SCHEMA:
        return "schema-mismatch"
    if artifact.get("reviewer_role") != reviewer:
        return "reviewer-role-mismatch"
    if artifact.get("plan_path") != expected_plan_path:
        return "plan-path-mismatch"
    if artifact.get("plan_sha256") != expected_hash:
        return "plan-hash-mismatch"
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
    if implementer_id and implementer_id == artifact.get("reviewer_id"):
        return "reviewer-equals-implementer"
    return None


def check_plan(root: Path, plan_path: str) -> ReviewCheck:
    plan_file = (root / plan_path).resolve()
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    required = required_reviewers_for_text(text)
    expected_hash = plan_hash(text)
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
        problem = _artifact_problem(artifact, reviewer, rel_path, expected_hash)
        if problem:
            invalid[reviewer] = problem
            continue
        reviewer_id = str(artifact["reviewer_id"])
        if reviewer_id in reviewer_ids.values():
            invalid[reviewer] = "duplicate-reviewer-id"
            continue
        reviewer_ids[reviewer] = reviewer_id
        artifacts[reviewer] = artifact

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
    if implementer_id and implementer_id == reviewer_id:
        raise ValueError("implementer_id must differ from reviewer_id")

    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "plan_path": rel_path,
        "plan_sha256": plan_hash(text),
        "reviewer_role": reviewer,
        "result": result,
        "reviewer_id": reviewer_id,
        "reviewer_source": reviewer_source,
        "implementer_id": implementer_id,
        "summary": summary,
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    out_dir = review_dir(root, rel_path)
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
            print(f"FAIL gate2-review-check {detail_text}")
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
