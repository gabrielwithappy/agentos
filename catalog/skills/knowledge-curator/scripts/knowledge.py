#!/usr/bin/env python3
"""Standalone entry point. Does not import AgentOS or third-party packages."""
from __future__ import annotations

import argparse
import sys

from knowledge_core import KnowledgeCore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely manage a local knowledge Git checkout.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--remote", required=True)
    init.add_argument("--branch", default="main")
    init.add_argument("--project")
    init.add_argument("--adopt-existing", action="store_true")
    for name in ("status", "backup", "sync"):
        command = commands.add_parser(name)
        command.add_argument("--project")
        if name == "backup":
            command.add_argument("--message", required=True)
        if name == "sync":
            command.add_argument("--push", action="store_true", help="Rejected: standalone sync never pushes.")
            command.add_argument("--confirm-branch")
    args = parser.parse_args(argv)
    core = KnowledgeCore()
    if args.command == "init":
        return core.emit("init", core.init, args.remote, args.branch, args.project, args.adopt_existing)
    if args.command == "status":
        return core.emit("status", core.status, args.project)
    if args.command == "backup":
        return core.emit("backup", core.backup, args.project, args.message)
    return core.emit("sync", core.sync, args.project, args.push, args.confirm_branch)


if __name__ == "__main__":
    raise SystemExit(main())
