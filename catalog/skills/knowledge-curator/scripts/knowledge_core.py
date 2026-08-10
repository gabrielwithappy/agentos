"""Portable, stdlib-only runtime for the knowledge-curator skill."""
from __future__ import annotations

import json
import os
import subprocess
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

    def init(self, remote: str | None, branch: str | None, project_root: str | None, adopt_existing: bool = False) -> dict[str, object]:
        if not remote or not _remote_is_safe(remote):
            raise KnowledgeError("Unsafe or missing remote URL; credentials are not accepted.", next_command="Use a credential-free --remote URL.")
        checkout = self._checkout(project_root)
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
