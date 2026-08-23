#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_artifacts import check_plan, plan_hash, plan_slug, review_dir, load_text
from review_policy import classify_plan


SECRET_KEY_PATH = ".agentos/secret.key"
SIGNED_ARTIFACT_SCHEMA = "crypto-signed-review-v1"


def get_or_create_secret_key(root: Path) -> bytes:
    key_file = root / SECRET_KEY_PATH
    if key_file.exists():
        return key_file.read_bytes()

    key_file.parent.mkdir(parents=True, exist_ok=True)
    new_key = secrets.token_bytes(32)
    # Write with restricted permissions
    fd = os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "wb") as f:
        f.write(new_key)
    return new_key


def sign_data(secret_key: bytes, message: str) -> str:
    return hmac.new(secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(secret_key: bytes, message: str, signature: str) -> bool:
    expected = sign_data(secret_key, message)
    return hmac.compare_digest(expected, signature)


def create_signed_review(root: Path, plan_path_str: str) -> Path:
    plan_file = (root / plan_path_str).resolve()
    if not plan_file.is_file():
        raise ValueError(f"Plan file not found: {plan_path_str}")

    rel_path = plan_file.relative_to(root).as_posix()
    check_result = check_plan(root, rel_path)

    if not check_result.valid:
        missing_str = f" missing={','.join(check_result.missing)}" if check_result.missing else ""
        invalid_str = f" invalid={check_result.invalid}" if check_result.invalid else ""
        raise ValueError(f"Gate 2 review artifacts check failed.{missing_str}{invalid_str}")

    secret_key = get_or_create_secret_key(root)
    text = load_text(plan_file)
    p_hash = plan_hash(text)
    reviewed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    message = f"{rel_path}:{p_hash}:{reviewed_at}"
    signature = sign_data(secret_key, message)

    signed_data = {
        "schema": SIGNED_ARTIFACT_SCHEMA,
        "plan_path": rel_path,
        "plan_sha256": p_hash,
        "reviewed_at": reviewed_at,
        "signature": signature,
        "gate2_artifacts": check_result.artifacts,
        "review_policy": classify_plan(text).to_dict(),
    }

    out_dir = review_dir(root, rel_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "signed_review.json"
    out_path.write_text(json.dumps(signed_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Cryptographic review signing tool")
    parser.add_argument("plan_path", help="Path to exec-plan markdown file")
    parser.add_argument("--root", default=None, help="Project root directory")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[5]

    try:
        out_path = create_signed_review(root, args.plan_path)
        rel_out = out_path.relative_to(root).as_posix()
        print(f"PASS crypto-signed-review {rel_out}")
    except ValueError as exc:
        print(f"FAIL crypto-signed-review {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
