"""Portable, stdlib-only runtime for the knowledge-curator skill."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


class KnowledgeError(Exception):
    def __init__(self, message: str, code: int = 2, next_command: str = "Run status after fixing the reported issue.") -> None:
        super().__init__(message)
        self.code = code
        self.next_command = next_command


def _safe_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not any(token in key.lower() for token in ("token", "credential", "password", "secret", "auth"))}


def _remote_is_safe(remote: str) -> bool:
    parsed = urlparse(remote)
    return bool(remote) and not parsed.username and not parsed.password and "@" not in parsed.netloc


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# OKF starter content
# ---------------------------------------------------------------------------

_OKF_INDEX_TEMPLATE = """\
---
okf_version: "0.2"
title: Knowledge Base
description: A local-first knowledge base managed with OKF v0.2.
tags:
  - domain/knowledge-curator
  - context/local-git
---

# Knowledge Base

This knowledge base is managed with the **knowledge-curator** skill and follows the [Open Knowledge Format (OKF) v0.2](https://example.com/okf).

## Getting started

- See `concepts/getting-started.md` for an example concept.
- Use `knowledge.py backup --message "..."` to save a local commit.
- Use `knowledge.py status` to inspect the current checkout state.

## Structure

| File | Purpose |
|------|---------|
| `index.md` | Entry point (this file) |
| `log.md`   | Chronological decision and activity log |
| `concepts/` | One Markdown file per concept |
"""

_OKF_LOG_TEMPLATE = """\
---
okf_version: "0.2"
title: Activity Log
type: log
---

# Activity Log

Record decisions, milestones, and changes here in reverse-chronological order.

## {today}

- Initialized knowledge base with OKF v0.2 starter bundle.
"""

_OKF_CONCEPT_TEMPLATE = """\
---
okf_version: "0.2"
title: Getting Started with knowledge-curator
type: concept
description: An example concept to illustrate the OKF v0.2 structure.
status: draft
tags:
  - action/plan
  - task/research
  - domain/knowledge-curator
  - context/local-git
---

# Getting Started with knowledge-curator

This is an example concept. Replace it with your own knowledge.

## Purpose

Summarise what this concept captures and why it matters.

## Notes

Add your observations, references, and key decisions here.

## Sources

List your sources as a YAML list in the frontmatter (`sources:`) or inline here.
"""


class KnowledgeCore:
    def _result(self, ok: bool, code: int, action: str, changed: bool, next_command: str, message: str = "") -> dict[str, object]:
        result: dict[str, object] = {"ok": ok, "code": code, "action": action, "changed": changed, "next": next_command}
        if message:
            result["message"] = message
        return result

    def _project(self, project_root: str | None) -> Path:
        root = Path(project_root or Path.cwd()).resolve()
        if not root.is_dir():
            raise KnowledgeError("Project directory does not exist.", next_command="Choose an existing --project directory.")
        return root

    def _checkout(self, project_root: str | None) -> Path:
        target = self._project(project_root) / "docs" / "knowledge"
        if target.exists() and target.is_symlink():
            raise KnowledgeError("Knowledge checkout must not be a symlink.", next_command="Replace docs/knowledge with a real directory.")
        return target

    def _git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=cwd, env=_safe_env(), text=True, capture_output=True, check=False)

    def _require_repo(self, project_root: str | None) -> Path:
        checkout = self._checkout(project_root)
        if not (checkout / ".git").exists():
            raise KnowledgeError("Knowledge checkout is not initialized.", next_command="Run init with --project <project-root> first.")
        for marker in ("MERGE_HEAD", "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD"):
            if (checkout / ".git" / marker).exists():
                raise KnowledgeError("Git operation is already in progress; no change was made.", next_command="Finish or abort the existing Git operation, then run status.")
        return checkout

    # ------------------------------------------------------------------
    # OKF starter helpers
    # ------------------------------------------------------------------

    def _journal_path(self, checkout: Path) -> Path:
        return checkout / ".git" / "knowledge-curator-starter-state.json"

    def _starter_files(self) -> dict[str, str]:
        """Return {relative-path: content} for the three starter files."""
        import datetime
        today = datetime.date.today().isoformat()
        return {
            "index.md": _OKF_INDEX_TEMPLATE,
            "log.md": _OKF_LOG_TEMPLATE.format(today=today),
            "concepts/getting-started.md": _OKF_CONCEPT_TEMPLATE,
        }

    def _is_empty_checkout(self, checkout: Path) -> bool:
        """True if the checkout has a .git dir but no other content."""
        items = [p for p in checkout.iterdir() if p.name != ".git"]
        return len(items) == 0

    def _recover_partial_starter(self, checkout: Path, journal_path: Path) -> None:
        """
        On next invocation, if journal exists, validate each entry:
        - If digest matches the actual file content → it is an aborted starter file → remove.
        - If digest mismatches → foreign content → raise OKF_STARTER_RECOVERY_REQUIRED (exit 2).
        """
        try:
            journal = json.loads(journal_path.read_text("utf-8"))
        except Exception:
            raise KnowledgeError(
                "Starter journal is unreadable; cannot safely recover.",
                code=2,
                next_command="Run status, correct filesystem permissions, then retry init --okf-starter with the same --remote and --branch.",
            )
        for rel, digest in journal.get("created", {}).items():
            path = checkout / rel
            if not path.exists():
                continue
            try:
                actual = _sha256_text(path.read_text("utf-8"))
            except Exception:
                raise KnowledgeError(
                    f"OKF_STARTER_RECOVERY_REQUIRED: cannot read {rel} to verify digest.",
                    code=2,
                    next_command="Run status, correct filesystem permissions, then retry init --okf-starter with the same --remote and --branch.",
                )
            if actual != digest:
                raise KnowledgeError(
                    f"OKF_STARTER_RECOVERY_REQUIRED: {rel} digest mismatch; foreign content detected.",
                    code=2,
                    next_command="Run status, correct filesystem permissions, then retry init --okf-starter with the same --remote and --branch.",
                )
            # digest matches → starter file from aborted run → safe to remove
            path.unlink()
        # Clean up parent dirs that we may have created (only if empty)
        for rel in journal.get("created", {}):
            parent = (checkout / rel).parent
            if parent != checkout and parent.exists():
                try:
                    parent.rmdir()  # only removes if empty
                except OSError:
                    pass
        journal_path.unlink(missing_ok=True)

    def _check_re_entry(self, checkout: Path, remote: str, branch: str) -> bool:
        """
        Return True if this is a safe re-entry after cleanup:
        - .git exists, only entry in checkout is .git
        - existing origin matches requested remote
        - current branch matches requested branch
        """
        if not (checkout / ".git").exists():
            return False
        items = [p for p in checkout.iterdir() if p.name != ".git"]
        if items:
            return False
        # Check remote
        result = self._git(checkout, "remote", "get-url", "origin")
        if result.returncode != 0 or result.stdout.strip() != remote:
            return False
        # Check branch
        result = self._git(checkout, "rev-parse", "--abbrev-ref", "HEAD")
        if result.returncode != 0 or result.stdout.strip() != branch:
            return False
        return True

    def _install_starter(self, checkout: Path, files: dict[str, str]) -> None:
        """
        Stage files in a private temp dir, then install no-overwrite per-file.
        Journal records created paths and their SHA-256 digests.
        On write failure: cleanup only this invocation's journal-listed files.
        """
        journal_path = self._journal_path(checkout)
        created: dict[str, str] = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            staged: dict[str, Path] = {}
            for rel, content in files.items():
                tmp_file = Path(tmpdir) / rel.replace("/", "_")
                tmp_file.write_text(content, encoding="utf-8")
                staged[rel] = tmp_file

            # Write journal before installing (crash-safe)
            digests = {rel: _sha256_text(content) for rel, content in files.items()}
            journal_path.write_text(json.dumps({"created": digests}), encoding="utf-8")

            try:
                for rel, tmp_file in staged.items():
                    dest = checkout / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists():
                        raise KnowledgeError(
                            f"OKF starter file already exists: {rel}; no overwrite performed.",
                            code=2,
                            next_command="Remove the conflicting file or use a clean empty checkout.",
                        )
                    dest.write_text(files[rel], encoding="utf-8")
                    created[rel] = digests[rel]
            except KnowledgeError:
                # Roll back only this invocation's created files
                for rel in created:
                    (checkout / rel).unlink(missing_ok=True)
                # Clean up any parent dirs we created (only if empty)
                for rel in created:
                    parent = (checkout / rel).parent
                    if parent != checkout and parent.exists():
                        try:
                            parent.rmdir()
                        except OSError:
                            pass
                journal_path.unlink(missing_ok=True)
                raise
            except OSError as exc:
                # Write failure: roll back this invocation's created files
                for rel in created:
                    (checkout / rel).unlink(missing_ok=True)
                for rel in created:
                    parent = (checkout / rel).parent
                    if parent != checkout and parent.exists():
                        try:
                            parent.rmdir()
                        except OSError:
                            pass
                journal_path.unlink(missing_ok=True)
                raise KnowledgeError(
                    f"OKF starter write failed: {exc}; no partial bundle remains.",
                    code=3,
                    next_command="Run status, correct filesystem permissions, then retry init --okf-starter with the same --remote and --branch.",
                )

        # All files installed successfully → remove journal
        journal_path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Core commands
    # ------------------------------------------------------------------

    def init(self, remote: str | None, branch: str | None, project_root: str | None, adopt_existing: bool = False, okf_starter: bool = False) -> dict[str, object]:
        if not remote or not _remote_is_safe(remote):
            raise KnowledgeError("Unsafe or missing remote URL; credentials are not accepted.", next_command="Use a credential-free --remote URL.")
        checkout = self._checkout(project_root)
        branch = branch or "main"

        if okf_starter:
            # --okf-starter cannot be combined with --adopt-existing
            if adopt_existing:
                raise KnowledgeError(
                    "--okf-starter cannot be combined with --adopt-existing.",
                    code=2,
                    next_command="Run init --okf-starter without --adopt-existing on a new empty checkout.",
                )
            # Check for partial journal from a previous aborted run
            journal_path = self._journal_path(checkout) if (checkout / ".git").exists() else None
            if journal_path is not None and journal_path.exists():
                self._recover_partial_starter(checkout, journal_path)
                # After recovery, check re-entry conditions
                if not self._check_re_entry(checkout, remote, branch):
                    raise KnowledgeError(
                        "OKF_STARTER_RECOVERY_REQUIRED: checkout state after journal recovery does not match requested remote/branch.",
                        code=2,
                        next_command="Run status, correct filesystem permissions, then retry init --okf-starter with the same --remote and --branch.",
                    )
            elif checkout.exists() and not self._is_empty_checkout(checkout):
                # populated checkout
                raise KnowledgeError(
                    "Knowledge checkout already contains files; --okf-starter requires a new empty checkout.",
                    code=2,
                    next_command="Use a clean empty checkout or run init without --okf-starter.",
                )
            # Initialize git repo if not already present
            if not (checkout / ".git").exists():
                checkout.mkdir(parents=True, exist_ok=True)
                result = self._git(checkout, "init")
                if result.returncode:
                    raise KnowledgeError("Git initialization failed.", 3, "Confirm Git is installed and rerun init.")
                self._git(checkout, "remote", "add", "origin", remote)
                if branch:
                    self._git(checkout, "branch", "-M", branch)
            # Install starter files
            files = self._starter_files()
            self._install_starter(checkout, files)
            created_list = ", ".join(sorted(files.keys()))
            return self._result(True, 0, "init", True, "Add your knowledge files, then run backup.", f"OKF v0.2 starter bundle created: {created_list}")

        # Standard init (no --okf-starter)
        if checkout.exists() and any(checkout.iterdir()) and not adopt_existing:
            raise KnowledgeError("Knowledge checkout already contains files; no overwrite was performed.", next_command="Use --adopt-existing to register it without network activity.")
        if adopt_existing and checkout.exists() and any(checkout.iterdir()):
            return self._result(True, 0, "init", False, "Run status to inspect the adopted checkout.")
        checkout.mkdir(parents=True, exist_ok=True)
        result = self._git(checkout, "init")
        if result.returncode:
            raise KnowledgeError("Git initialization failed.", 3, "Confirm Git is installed and rerun init.")
        self._git(checkout, "remote", "add", "origin", remote)
        if branch:
            self._git(checkout, "branch", "-M", branch)
        return self._result(True, 0, "init", True, "Add reviewed knowledge files, then run backup.")

    def status(self, project_root: str | None) -> dict[str, object]:
        checkout = self._require_repo(project_root)
        result = self._git(checkout, "status", "--porcelain")
        if result.returncode:
            raise KnowledgeError("Git status failed.", 3, "Run status in the knowledge checkout after fixing Git.")
        dirty = bool(result.stdout.strip())
        return self._result(True, 0, "status", False, "Run backup to create a local commit." if dirty else "Knowledge checkout is clean.", "dirty" if dirty else "clean")

    def backup(self, project_root: str | None, message: str | None) -> dict[str, object]:
        if not message:
            raise KnowledgeError("Backup requires --message.", next_command="Run backup --message '<summary>'.")
        checkout = self._require_repo(project_root)
        status = self._git(checkout, "status", "--porcelain")
        if status.returncode:
            raise KnowledgeError("Git status failed.", 3, "Run status after fixing Git.")
        if not status.stdout.strip():
            return self._result(True, 0, "backup", False, "Nothing to back up; add or edit a knowledge file first.")
        add = self._git(checkout, "add", "--all")
        commit = self._git(checkout, "commit", "-m", message)
        if add.returncode or commit.returncode:
            raise KnowledgeError("Local backup commit failed.", 3, "Configure local Git user.name/user.email and rerun backup.")
        return self._result(True, 0, "backup", True, "Run status to verify the local checkout is clean.")

    def sync(self, project_root: str | None, push: bool = False, confirm_branch: str | None = None) -> dict[str, object]:
        if push:
            raise KnowledgeError("Push is not supported by the standalone skill; no network action was taken.", next_command="Run sync without --push to inspect local state.")
        return self.status(project_root) | {"action": "sync", "next": "Sync is local-only; no fetch, pull, or push was performed."}

    def emit(self, action: str, fn, *args, **kwargs) -> int:
        try:
            payload = fn(*args, **kwargs)
        except KnowledgeError as exc:
            payload = self._result(False, exc.code, action, False, exc.next_command, str(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return int(payload["code"])
