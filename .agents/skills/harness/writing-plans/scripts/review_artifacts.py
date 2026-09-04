#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
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
ALLOWED_RESULTS = ALLOWED_PASS_RESULTS | {"FAIL"}
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
        ".agents/hooks/scripts/check-alignment.py",
        ".agents/skills/harness/run-all-tests/tests/test_plan_reader_first_contract.py",
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
        if artifact.get("result") == "FAIL":
            return "result-failed"
        return "result-not-pass"
    if artifact.get("adjudication") in {"blocking", "required-follow-up"}:
        return "unresolved-adjudication"
    if artifact.get("blocking_findings"):
        return "blocking-findings-present"
    if artifact.get("required_follow_up"):
        return "required-follow-up-present"
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
    findings: list[dict[str, Any]] | None = None,
    triage_surface: list[str] | None = None,
    required_reviewers: list[str] | None = None,
    review_sequence: list[str] | None = None,
    adjudication: str | None = None,
    blocking_findings: list[Any] | None = None,
    required_follow_up: list[Any] | None = None,
    depends_on: str | None = None,
    sequence: int | None = None,
    review_round_id: str | None = None,
) -> Path:
    plan_file = (root / plan_path).resolve()
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    if reviewer not in {"plan-reviewer", "principle-auditor", "usability-reviewer"}:
        raise ValueError(f"unsupported reviewer: {reviewer}")
    if result not in ALLOWED_RESULTS:
        raise ValueError(f"unsupported result: {result}")
    if result == "FAIL":
        if not findings or not isinstance(findings, list):
            raise ValueError("FAIL result requires non-empty findings list")
        for f in findings:
            if not isinstance(f, dict) or not {"id", "severity", "finding", "recovery", "rereview"}.issubset(f.keys()):
                raise ValueError("each finding must contain id, severity, finding, recovery, rereview")
    if not reviewer_id:
        raise ValueError("reviewer_id is required")
    if not reviewer_source:
        raise ValueError("reviewer_source is required")
    if not summary:
        if result == "FAIL" and findings:
            summary = f"Review FAIL with {len(findings)} findings"
        else:
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

    digest = plan_hash(text)
    artifact: dict[str, Any] = {
        "schema": ARTIFACT_SCHEMA,
        "plan_path": rel_path,
        "plan_identity": rel_path,
        "review_scope": "gate2",
        "semantic_revision": revision,
        "semantic_snapshot": snapshot,
        "plan_sha256": digest,
        "review_round_id": review_round_id or f"gate2-{digest}",
        "reviewer_role": reviewer,
        "result": result,
        "reviewer_id": reviewer_id,
        "reviewer_source": reviewer_source,
        "implementer_id": implementer_id,
        "summary": summary,
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if findings is not None:
        artifact["findings"] = findings
    if triage_surface is not None:
        artifact["triage_surface"] = triage_surface
    if required_reviewers is not None:
        artifact["required_reviewers"] = required_reviewers
    if review_sequence is not None:
        artifact["review_sequence"] = review_sequence
    if adjudication is not None:
        artifact["adjudication"] = adjudication
    if blocking_findings is not None:
        artifact["blocking_findings"] = blocking_findings
    if required_follow_up is not None:
        artifact["required_follow_up"] = required_follow_up
    if depends_on is not None:
        artifact["depends_on"] = depends_on
    if sequence is not None:
        artifact["sequence"] = sequence

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{reviewer}.json"
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def dispatch(root: Path, plan_path: str, stage: str) -> int:
    root = root.resolve()
    plan_file = (root / plan_path).resolve()
    if not plan_file.is_file():
        print(f"ERROR: plan file not found: {plan_path}", file=sys.stderr)
        return 1
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    expected_digest = plan_hash(text)
    expected_snapshot = semantic_snapshot(text)
    required = required_reviewers_for_text(text)
    out_dir = review_dir(root, rel_path)

    if stage == "triage":
        pr_path = out_dir / "plan-reviewer.json"
        if not pr_path.is_file():
            print("ERROR: missing plan-reviewer.json for triage dispatch", file=sys.stderr)
            return 1
        pr = _load_artifact(pr_path)
        if pr.get("plan_sha256") != expected_digest and pr.get("semantic_snapshot") != expected_snapshot:
            print("ERROR: plan-reviewer artifact hash or snapshot mismatch", file=sys.stderr)
            return 1
        if pr.get("result") not in ALLOWED_PASS_RESULTS:
            print("ERROR: plan-reviewer result is not PASS", file=sys.stderr)
            return 1
        triage_surface = pr.get("triage_surface")
        if not triage_surface or not isinstance(triage_surface, list):
            print("ERROR: plan-reviewer missing triage_surface", file=sys.stderr)
            return 1
        seq = pr.get("review_sequence")
        if not seq or seq != required:
            print("ERROR: plan-reviewer review_sequence mismatch", file=sys.stderr)
            return 1
        handoff = {
            "schema": "gate2-triage-handoff-v1",
            "plan_path": rel_path,
            "plan_sha256": expected_digest,
            "triage_surface": triage_surface,
            "required_reviewers": required,
            "review_sequence": seq,
            "dispatched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        handoff_path = out_dir / "plan-reviewer-handoff.json"
        handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"PASS triage-dispatched {handoff_path.relative_to(root).as_posix()}")
        return 0

    elif stage == "final":
        handoff_path = out_dir / "plan-reviewer-handoff.json"
        if not handoff_path.is_file():
            print("ERROR: missing plan-reviewer-handoff.json for final dispatch", file=sys.stderr)
            return 1
        handoff = _load_artifact(handoff_path)
        if handoff.get("plan_sha256") != expected_digest and handoff.get("plan_path") != rel_path:
            print("ERROR: stale handoff in final dispatch", file=sys.stderr)
            return 1

        check = check_plan(root, rel_path)
        if not check.valid:
            print(f"ERROR: check_plan failed: missing={check.missing}, invalid={check.invalid}", file=sys.stderr)
            return 1

        for role in required:
            if role == "plan-reviewer":
                continue
            art = check.artifacts.get(role, {})
            if "depends_on" in art and art.get("depends_on") != "plan-reviewer":
                print(f"ERROR: {role} does not depend on plan-reviewer", file=sys.stderr)
                return 1

        final_path = out_dir / "plan-reviewer-final.json"
        if not final_path.is_file():
            print("ERROR: missing plan-reviewer-final.json", file=sys.stderr)
            return 1
        final_art = _load_artifact(final_path)
        final_owner = final_art.get("final_adjudicator") or final_art.get("reviewer_role")
        if final_owner != "plan-reviewer":
            print(f"ERROR: final_adjudicator is not plan-reviewer ({final_owner})", file=sys.stderr)
            return 1
        if final_art.get("adjudication") in {"blocking", "required-follow-up"}:
            print("ERROR: unresolved blocker/follow-up in final adjudication", file=sys.stderr)
            return 1
        if final_art.get("blocking_findings") or final_art.get("required_follow_up"):
            print("ERROR: unresolved findings in final adjudication", file=sys.stderr)
            return 1

        print(f"PASS final-dispatched {final_path.relative_to(root).as_posix()}")
        return 0

    else:
        print(f"ERROR: unsupported stage {stage}", file=sys.stderr)
        return 1


def verify_and_receipt(root: Path, plan_path: str, receipt_path_str: str) -> int:
    import subprocess, shlex
    root = root.resolve()
    plan_file = (root / plan_path).resolve()
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    expected_digest = plan_hash(text)

    verifiers = [
        "pytest .agents/skills/harness/writing-plans/tests/test_plan_review_scope.py -q",
        "bash .agents/skills/harness/run-all-tests/tests/harness/run_harness_tests.sh",
        "bash scripts/verify-public-test-suite.sh",
        "bash .agents/skills/harness/sync-manifest/scripts/sync-manifest.sh --check",
        "git diff --check",
    ]

    verifier_results = []
    for cmd in verifiers:
        proc = subprocess.run(shlex.split(cmd), cwd=str(root), capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"ERROR: verifier failed: {cmd}\n{proc.stderr}\n{proc.stdout}", file=sys.stderr)
            return 1
        verifier_results.append({
            "command": cmd,
            "exit_code": 0,
            "result": "PASS",
        })

    declared_scope = list(extract_declared_scope(text))
    cmd = ["git", "diff", "--name-only", "HEAD"]
    if declared_scope:
        cmd.extend(["--"] + declared_scope)
    git_diff = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    changed_paths = [p.strip() for p in git_diff.stdout.splitlines() if p.strip()]
    if not changed_paths and declared_scope:
        status_cmd = ["git", "status", "--porcelain", "--"] + declared_scope
        git_status = subprocess.run(status_cmd, cwd=str(root), capture_output=True, text=True)
        changed_paths = [line[3:].strip() for line in git_status.stdout.splitlines() if line.strip()]
    elif not changed_paths:
        git_status = subprocess.run(["git", "status", "--porcelain"], cwd=str(root), capture_output=True, text=True)
        changed_paths = [line[3:].strip() for line in git_status.stdout.splitlines() if line.strip()]

    usage_match = re.search(r"실행 명령:\s*`([^`]+)`", text)
    usage_command = usage_match.group(1) if usage_match else "python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py --help"
    usage_proc = subprocess.run(shlex.split(usage_command), cwd=str(root), capture_output=True, text=True)
    usage_exit_code = usage_proc.returncode

    receipt = {
        "schema": "closeout-verification-v1",
        "plan_path": rel_path,
        "plan_sha256": expected_digest,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changed_paths": changed_paths,
        "usage_command": usage_command,
        "usage_exit_code": usage_exit_code,
        "verifiers": verifier_results,
    }

    out_receipt = (root / receipt_path_str).resolve()
    out_receipt.parent.mkdir(parents=True, exist_ok=True)
    out_receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS closeout-receipt-written {out_receipt.relative_to(root).as_posix()}")
    return 0


def closeout_check(root: Path, plan_path: str, receipt_path_str: str) -> int:
    root = root.resolve()
    plan_file = (root / plan_path).resolve()
    rel_path = plan_file.relative_to(root).as_posix()
    text = load_text(plan_file)
    expected_digest = plan_hash(text)

    receipt_file = (root / receipt_path_str).resolve()
    if not receipt_file.is_file():
        print(f"ERROR: missing receipt file {receipt_path_str}", file=sys.stderr)
        return 1
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    if receipt.get("schema") != "closeout-verification-v1":
        print("ERROR: invalid receipt schema", file=sys.stderr)
        return 1
    if receipt.get("plan_path") != rel_path:
        print("ERROR: receipt plan_path mismatch", file=sys.stderr)
        return 1
    if receipt.get("plan_sha256") != expected_digest:
        print("ERROR: stale receipt hash", file=sys.stderr)
        return 1
    if not receipt.get("changed_paths"):
        print("ERROR: receipt has empty changed_paths", file=sys.stderr)
        return 1
    declared_scope = extract_declared_scope(text)
    if declared_scope:
        for p in receipt["changed_paths"]:
            if p not in declared_scope and not any(p.startswith(ds.rstrip("/") + "/") for ds in declared_scope):
                print(f"ERROR: unscoped changed path in receipt: {p}", file=sys.stderr)
                return 1

    for sec_name in ["구현 결과", "사용 방법", "완료 증거", "아카이브 결정"]:
        pattern = rf"##\s*{sec_name}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            print(f"ERROR: missing section ## {sec_name}", file=sys.stderr)
            return 1
        sec_content = match.group(1).strip()
        if len(sec_content) < 20 or "(구현 후 작성)" in sec_content:
            print(f"ERROR: filler content in ## {sec_name}", file=sys.stderr)
            return 1

    if not receipt.get("usage_command") or receipt.get("usage_exit_code") != 0:
        print("ERROR: missing or failing usage command in receipt", file=sys.stderr)
        return 1

    verifiers = receipt.get("verifiers", [])
    if not verifiers or any(v.get("exit_code") != 0 or v.get("result") != "PASS" for v in verifiers):
        print("ERROR: missing or failed verifiers in receipt", file=sys.stderr)
        return 1

    print("PASS closeout-check")
    return 0


def _resolve_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[5]


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate 2 review artifact helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=None)
    common.add_argument("--plan", dest="plan_path", required=True)
    common.add_argument("--json", action="store_true")

    subparsers.add_parser("slug", parents=[common], help="Print plan slug")
    subparsers.add_parser("check", parents=[common], help="Check plan review artifacts")

    rec_p = subparsers.add_parser("record", parents=[common], help="Record review artifact")
    rec_p.add_argument("--reviewer")
    rec_p.add_argument("--result")
    rec_p.add_argument("--reviewer-id")
    rec_p.add_argument("--reviewer-source")
    rec_p.add_argument("--summary")
    rec_p.add_argument("--implementer-id")

    disp_p = subparsers.add_parser("dispatch", parents=[common], help="Dispatch triage or final stage")
    disp_p.add_argument("--stage", choices=["triage", "final"], required=True, help="Stage to dispatch (triage or final)")

    var_p = subparsers.add_parser("verify-and-receipt", parents=[common], help="Verify harness and generate closeout receipt")
    var_p.add_argument("--receipt", required=True, help="Output receipt path")

    close_p = subparsers.add_parser("closeout-check", parents=[common], help="Validate closeout evidence against receipt")
    close_p.add_argument("--receipt", required=True, help="Input receipt path")

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

    if args.command == "dispatch":
        code = dispatch(root, args.plan_path, args.stage)
        sys.exit(code)

    if args.command == "verify-and-receipt":
        code = verify_and_receipt(root, args.plan_path, args.receipt)
        sys.exit(code)

    if args.command == "closeout-check":
        code = closeout_check(root, args.plan_path, args.receipt)
        sys.exit(code)

    if args.command == "record":
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
        return


if __name__ == "__main__":
    main()
