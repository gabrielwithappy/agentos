import glob
import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path

SECRET_KEY_PATH = ".agentos/secret.key"
REVIEWED_RE = re.compile(r"^> reviewed: true(?:\s*<br\s*/?>)?$", re.MULTILINE)
HEADER_STATUS_RE = re.compile(r"^> \*\*상태:\*\* .+$", re.MULTILINE)
GATE2_RE = re.compile(r"^> gate2_[^:\n]+:.*$", re.MULTILINE)
# Fields the "Completed Active Plan Closeout" contract (writing-plans/SKILL.md)
# requires agents to fill in AFTER Gate 2 signing. Excluded from the hash so a
# properly closed-out plan doesn't retroactively invalidate its own review.
# Kept in sync with the copy in
# .agents/skills/harness/writing-plans/scripts/review_artifacts.py.
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


def normalize_plan_text(text: str) -> str:
    normalized = REVIEWED_RE.sub("", text)
    normalized = GATE2_RE.sub("", normalized)
    normalized = HEADER_STATUS_RE.sub("", normalized)
    normalized = LIVING_META_RE.sub("", normalized)
    normalized = TASK_CHECKBOX_RE.sub(r"\1[ ]", normalized)
    normalized = LIVING_SECTION_RE.sub("", normalized)
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


def verify_signature(secret_key: bytes, message: str, signature: str) -> bool:
    expected = hmac.new(secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def get_target_plans(root: Path) -> list[str]:
    loop_state_file = root / ".agents" / "traces" / "harness" / "loop-state.md"
    if loop_state_file.is_file():
        match = re.search(r'^plan_path:\s*"([^"]*)"$', loop_state_file.read_text(encoding="utf-8"), re.MULTILINE)
        if match and match.group(1):
            target = match.group(1)
            if (root / target).is_file():
                return [target]

    active_plans = sorted(glob.glob(".agentos/project/exec-plans/active/*.md"))
    reviewed_plans = []
    for plan_str in active_plans:
        content = Path(plan_str).read_text(encoding="utf-8")
        if REVIEWED_RE.search(content):
            reviewed_plans.append(plan_str)
    return reviewed_plans


def check_alignment() -> int:
    root = Path(os.getcwd())
    target_plans = get_target_plans(root)
    if not target_plans:
        print(
            "AgentOS Unified Hook [Alignment]: No active reviewed plan found. Did you confirm the design with the user?",
            file=sys.stderr,
        )
        return 0

    key_file = root / SECRET_KEY_PATH
    if not key_file.is_file():
        print(
            "AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing.",
            file=sys.stderr,
        )
        return 1

    secret_key = key_file.read_bytes()

    for plan_str in target_plans:
        plan_path = Path(plan_str)
        rel_path = plan_path.relative_to(root).as_posix() if plan_path.is_absolute() else plan_str
        slug = plan_slug(rel_path)
        signed_file = root / ".agents" / "traces" / "reviews" / slug / "signed_review.json"

        if not signed_file.is_file():
            print(
                f"AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing for {rel_path}.",
                file=sys.stderr,
            )
            return 1

        try:
            signed_data = json.loads(signed_file.read_text(encoding="utf-8"))
            content = plan_path.read_text(encoding="utf-8")
            current_hash = plan_hash(content)

            if signed_data.get("plan_sha256") != current_hash:
                print(
                    f"AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing for {rel_path}.",
                    file=sys.stderr,
                )
                return 1

            reviewed_at = signed_data.get("reviewed_at", "")
            signature = signed_data.get("signature", "")
            message = f"{rel_path}:{current_hash}:{reviewed_at}"

            if not verify_signature(secret_key, message, signature):
                print(
                    f"AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing for {rel_path}.",
                    file=sys.stderr,
                )
                return 1
        except Exception:
            print(
                f"AgentOS Unified Hook [Alignment]: Active plan signature is invalid or missing for {rel_path}.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(check_alignment())

