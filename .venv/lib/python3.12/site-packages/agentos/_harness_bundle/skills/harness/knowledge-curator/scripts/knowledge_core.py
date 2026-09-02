
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import re
from pathlib import Path
from urllib.parse import urlparse


class KnowledgeError(Exception):
    def __init__(self, message: str, code: int = 2, next_command: str = "Run status after fixing the reported issue.", details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.next_command = next_command
        self.details = details or {}


def _safe_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "true", "GIT_MERGE_AUTOEDIT": "no"})
    return env


def _remote_is_safe(remote: str) -> bool:
    parsed = urlparse(remote)
    if not remote or any(char.isspace() for char in remote):
        return False
    if parsed.scheme == "file":
        return bool(parsed.path) and not parsed.netloc and not parsed.query and not parsed.fragment
    if parsed.scheme in {"https", "ssh"}:
        return bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment
    return bool(re.fullmatch(r"git@[A-Za-z0-9][A-Za-z0-9.-]*:[^\s:@?#]+", remote))


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
- See [concepts](concepts/index.md) for the folder index.
- Use `knowledge.py backup --message "..."` to save a local commit.
- Use `knowledge.py status` to inspect the current checkout state.

## Structure

| File | Purpose |
|------|---------|
| `index.md` | Entry point (this file) |
| `log.md`   | Chronological decision and activity log |
| `concepts/` | Concepts and its folder index |
"""

_OKF_CONCEPTS_INDEX_TEMPLATE = """\
# Concepts

* [Getting Started](getting-started.md) - OKF v0.2 example concept.
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
        return subprocess.run(["git", *args], cwd=cwd, env=_safe_env(), text=True, stdin=subprocess.DEVNULL, capture_output=True, check=False)

    def _branch_is_safe(self, branch: str) -> bool:
        result = subprocess.run(["git", "check-ref-format", "--branch", branch], env=_safe_env(), text=True, stdin=subprocess.DEVNULL, capture_output=True, check=False)
        return result.returncode == 0

    def _sync_policy(self, checkout: Path) -> str:
        result = self._git(checkout, "config", "--local", "--get", "knowledge-curator.sync-policy")
        policy = result.stdout.strip()
        return policy if policy in {"local", "manual", "auto"} else "local"

    def _branch(self, checkout: Path) -> str:
        result = self._git(checkout, "symbolic-ref", "--quiet", "--short", "HEAD")
        if result.returncode or not self._branch_is_safe(result.stdout.strip()):
            raise KnowledgeError("Knowledge branch is invalid; no network action was taken.", next_command="Reinitialize the checkout with a valid branch name.")
        return result.stdout.strip()

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

        import datetime
        today = datetime.date.today().isoformat()
        return {
            "index.md": _OKF_INDEX_TEMPLATE,
            "log.md": _OKF_LOG_TEMPLATE.format(today=today),
            "concepts/index.md": _OKF_CONCEPTS_INDEX_TEMPLATE,
            "concepts/getting-started.md": _OKF_CONCEPT_TEMPLATE,
        }

    def _is_empty_checkout(self, checkout: Path) -> bool:

        items = [p for p in checkout.iterdir() if p.name != ".git"]
        return len(items) == 0

    def _recover_partial_starter(self, checkout: Path, journal_path: Path) -> None:


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

    def init(self, remote: str | None, branch: str | None, project_root: str | None, adopt_existing: bool = False, okf_starter: bool = False, sync_policy: str = "local") -> dict[str, object]:
        if not remote or not _remote_is_safe(remote):
            raise KnowledgeError("Unsafe or missing remote URL; credentials are not accepted.", next_command="Use a credential-free --remote URL.")
        checkout = self._checkout(project_root)
        branch = branch or "main"
        if sync_policy not in {"local", "manual", "auto"}:
            raise KnowledgeError("Invalid sync policy; no checkout was created.", next_command="Use --sync-policy local, manual, or auto.")
        if not self._branch_is_safe(branch):
            raise KnowledgeError("Invalid branch name; no checkout was created.", next_command="Use a valid Git branch name.")

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
                self._git(checkout, "branch", "-M", branch)
                self._git(checkout, "config", "--local", "knowledge-curator.sync-policy", sync_policy)
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
        self._git(checkout, "branch", "-M", branch)
        self._git(checkout, "config", "--local", "knowledge-curator.sync-policy", sync_policy)
        return self._result(True, 0, "init", True, "Add reviewed knowledge files, then run backup.")

    def status(self, project_root: str | None) -> dict[str, object]:
        checkout = self._require_repo(project_root)
        result = self._git(checkout, "status", "--porcelain")
        if result.returncode:
            raise KnowledgeError("Git status failed.", 3, "Run status in the knowledge checkout after fixing Git.")
        dirty = bool(result.stdout.strip())
        result = self._result(True, 0, "status", False, "Run backup to create a local commit." if dirty else "Knowledge checkout is clean.", "dirty" if dirty else "clean")
        result["sync_policy"] = self._sync_policy(checkout)
        result["branch"] = self._branch(checkout)
        return result

    def backup(self, project_root: str | None, message: str | None) -> dict[str, object]:
        if not message:
            raise KnowledgeError("Backup requires --message.", next_command="Run backup --message '<summary>'.")
        checkout = self._require_repo(project_root)
        has_root_bundle = (checkout / "index.md").exists() and (checkout / "log.md").exists()
        if has_root_bundle:
            from okf_bundle_validate import validate_bundle

            validation = validate_bundle(str(checkout), strict=True)
            if not validation["ok"]:
                raise KnowledgeError(
                    "Knowledge validation failed; no backup was created.",
                    2,
                    validation["next"],
                    {"diagnostics": validation["diagnostics"]},
                )
        status = self._git(checkout, "status", "--porcelain")
        if status.returncode:
            raise KnowledgeError("Git status failed.", 3, "Run status after fixing Git.")
        if not status.stdout.strip():
            return self._result(True, 0, "backup", False, "Nothing to back up; add or edit a knowledge file first.")
        add = self._git(checkout, "add", "--all")
        commit = self._git(checkout, "commit", "-m", message)
        if add.returncode or commit.returncode:
            raise KnowledgeError("Local backup commit failed.", 3, "Configure local Git user.name/user.email and rerun backup.")
        if self._sync_policy(checkout) == "auto":
            payload = self._sync(checkout, local_backup_saved=True)
            payload["action"] = "backup"
            payload["local_backup_saved"] = True
            return payload
        return self._result(True, 0, "backup", True, "Run status to verify the local checkout is clean.") | {"local_backup_saved": True, "remote_published": False}

    def _sync(self, checkout: Path, local_backup_saved: bool = False) -> dict[str, object]:
        status = self._git(checkout, "status", "--porcelain")
        if status.returncode:
            raise KnowledgeError("Git status failed.", 3, "Run status after fixing Git.", {"phase": "preflight", "local_backup_saved": local_backup_saved, "remote_published": False})
        if status.stdout.strip():
            raise KnowledgeError("Knowledge checkout is dirty; no sync was started.", next_command="Run backup first, then rerun sync.", details={"phase": "preflight", "local_backup_saved": local_backup_saved, "remote_published": False})
        branch = self._branch(checkout)
        origin = self._git(checkout, "remote", "get-url", "origin")
        if origin.returncode:
            raise KnowledgeError("Knowledge remote is not configured; no network action was taken.", next_command="Run init with a credential-free --remote URL.", details={"phase": "preflight", "local_backup_saved": local_backup_saved, "remote_published": False})
        fetched = self._git(checkout, "fetch", "--no-tags", "origin")
        if fetched.returncode:
            raise KnowledgeError("Remote fetch failed; local knowledge files were not changed.", 3, "Configure the existing Git credential helper; do not paste credentials into this CLI.", {"phase": "fetch", "local_backup_saved": local_backup_saved, "remote_published": False})
        remote_ref = f"refs/remotes/origin/{branch}"
        remote_head = self._git(checkout, "rev-parse", "--verify", remote_ref)
        local_head = self._git(checkout, "rev-parse", "--verify", "HEAD")
        if remote_head.returncode:
            if local_head.returncode:
                raise KnowledgeError("Remote and local branch are empty; no sync was started.", next_command="Add knowledge files and run backup before sync.", details={"phase": "bootstrap", "local_backup_saved": local_backup_saved, "remote_published": False})
            return self._push(checkout, branch, local_backup_saved, changed=True)
        fetched_branch = self._git(checkout, "fetch", "--no-tags", "origin", branch)
        if fetched_branch.returncode:
            raise KnowledgeError("Remote branch fetch failed; local knowledge files were not changed.", 3, "Configure the existing Git credential helper; do not paste credentials into this CLI.", {"phase": "fetch", "local_backup_saved": local_backup_saved, "remote_published": False})
        if local_head.returncode:
            merged = self._git(checkout, "merge", "--ff-only", "FETCH_HEAD")
            if merged.returncode:
                raise KnowledgeError("Remote bootstrap could not be applied; local knowledge files were not changed.", 3, "Inspect the normal Git checkout, then rerun sync.", {"phase": "merge", "local_backup_saved": local_backup_saved, "remote_published": False})
            return self._result(True, 0, "sync", True, "Remote knowledge is now available locally.") | {"phase": "merge", "local_backup_saved": local_backup_saved, "remote_published": True}
        local = local_head.stdout.strip()
        remote = remote_head.stdout.strip()
        if local == remote:
            return self._result(True, 0, "sync", False, "Local and remote knowledge are already synchronized.") | {"phase": "complete", "local_backup_saved": local_backup_saved, "remote_published": True}
        local_ancestor = self._git(checkout, "merge-base", "--is-ancestor", local, remote)
        if local_ancestor.returncode == 0:
            merged = self._git(checkout, "merge", "--ff-only", "FETCH_HEAD")
            if merged.returncode:
                raise KnowledgeError("Fast-forward failed; local knowledge files were not changed.", 3, "Inspect the normal Git checkout, then rerun sync.", {"phase": "merge", "local_backup_saved": local_backup_saved, "remote_published": False})
            return self._result(True, 0, "sync", True, "Remote knowledge was fast-forwarded locally.") | {"phase": "merge", "local_backup_saved": local_backup_saved, "remote_published": True}
        remote_ancestor = self._git(checkout, "merge-base", "--is-ancestor", remote, local)
        if remote_ancestor.returncode == 0:
            return self._push(checkout, branch, local_backup_saved, changed=True)
        preflight = self._git(checkout, "merge-tree", "--write-tree", local, remote)
        if preflight.returncode:
            raise KnowledgeError("Remote knowledge conflicts; no merge was started.", next_command="Resolve the competing knowledge edits in a normal Git checkout, then rerun sync.", details={"phase": "conflict", "local_backup_saved": local_backup_saved, "remote_published": False})
        merged = self._git(checkout, "merge", "--no-edit", "-m", f"knowledge-curator sync: merge {branch}", "FETCH_HEAD")
        if merged.returncode:
            raise KnowledgeError("Safe merge failed; no recovery action was taken automatically.", 3, "Inspect the normal Git checkout, then rerun sync.", {"phase": "merge", "local_backup_saved": local_backup_saved, "remote_published": False})
        return self._push(checkout, branch, local_backup_saved, changed=True)

    def _push(self, checkout: Path, branch: str, local_backup_saved: bool, changed: bool) -> dict[str, object]:
        pushed = self._git(checkout, "push", "origin", f"HEAD:{branch}")
        if pushed.returncode:
            return self._result(False, 3, "sync", changed, "Run sync after reconciling the remote.", "Local commit retained; remote publication failed.") | {"phase": "push", "local_backup_saved": local_backup_saved, "remote_published": False}
        return self._result(True, 0, "sync", changed, "Knowledge changes are published to the remote.") | {"phase": "push", "local_backup_saved": local_backup_saved, "remote_published": True}

    def sync(self, project_root: str | None) -> dict[str, object]:
        checkout = self._require_repo(project_root)
        policy = self._sync_policy(checkout)
        if policy == "local":
            raise KnowledgeError("Sync policy is local; no network action was taken.", next_command="Reinitialize with --sync-policy manual or auto to enable remote sync.", details={"phase": "policy", "local_backup_saved": False, "remote_published": False})
        return self._sync(checkout)

    def emit(self, action: str, fn, *args, **kwargs) -> int:
        try:
            payload = fn(*args, **kwargs)
        except KnowledgeError as exc:
            payload = self._result(False, exc.code, action, False, exc.next_command, str(exc))
            payload.update(exc.details)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return int(payload["code"])
