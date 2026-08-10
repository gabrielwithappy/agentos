#!/usr/bin/env python3
"""Standalone entry point. Does not import AgentOS or third-party packages."""
from __future__ import annotations

import argparse
import json
import sys

from knowledge_core import KnowledgeCore


def _parser_error_json(action: str, message: str) -> int:
    """Emit a JSON envelope for argparse errors instead of a plain text error."""
    payload = {
        "ok": False,
        "code": 2,
        "action": action,
        "changed": False,
        "next": "Run knowledge.py <command> --help to see valid options.",
        "message": message,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 2


class _JsonArgParser(argparse.ArgumentParser):
    """ArgumentParser that emits JSON on error instead of printing to stderr."""

    def __init__(self, *args, action: str = "unknown", **kwargs):
        super().__init__(*args, **kwargs)
        self._json_action = action

    def error(self, message: str):  # type: ignore[override]
        _parser_error_json(self._json_action, message)
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = _JsonArgParser(description="Safely manage a local knowledge Git checkout.", action="unknown")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", formatter_class=argparse.RawDescriptionHelpFormatter,
                               description=(
                                   "Initialise a local knowledge Git checkout.\n\n"
                                   "  --okf-starter  Opt-in: create an OKF v0.2 starter bundle\n"
                                   "                 (index.md, log.md, concepts/getting-started.md).\n"
                                   "                 Requires a new, empty checkout.\n"
                                   "                 Existing files are never overwritten.\n"
                                   "                 On write failure, leaves zero starter files.\n"
                                   "                 Cannot be combined with --adopt-existing.\n\n"
                                   "  Tags use slash-form hierarchy (e.g. action/plan, domain/knowledge-curator).\n"
                                   "  Use 'knowledge.py status' after init to verify the checkout is ready.\n"
                               ))
    init.add_argument("--remote", required=True)
    init.add_argument("--branch", default="main")
    init.add_argument("--project")
    init.add_argument("--adopt-existing", action="store_true")
    init.add_argument("--okf-starter", action="store_true",
                      help="Create an OKF v0.2 starter bundle (opt-in, no-overwrite). Cannot be combined with --adopt-existing.")

    for name in ("status", "backup", "sync"):
        command = commands.add_parser(name)
        command.add_argument("--project")
        if name == "backup":
            command.add_argument("--message", required=True)
        if name == "sync":
            command.add_argument("--push", action="store_true", help="Rejected: standalone sync never pushes.")
            command.add_argument("--confirm-branch")

    validate = commands.add_parser("validate",
                                   formatter_class=argparse.RawDescriptionHelpFormatter,
                                   description=(
                                       "Read-only OKF v0.2 structural checker.\n\n"
                                       "  Prints a single JSON line to stdout. stderr is always empty.\n"
                                       "  Exit 0: no errors. Exit 2: errors or strict warnings. Exit 3: filesystem error.\n\n"
                                       "  --strict  Treat advisory warnings as errors (exit 2).\n"
                                       "  --migrate is not supported and will be refused.\n"
                                   ))
    validate.add_argument("--project", required=True, help="Path to the OKF bundle root.")
    validate.add_argument("--strict", action="store_true", help="Treat advisory warnings as errors (exit 2).")
    validate.add_argument("--migrate", action="store_true", help=argparse.SUPPRESS)  # refused

    args = parser.parse_args(argv)
    core = KnowledgeCore()

    if args.command == "init":
        return core.emit("init", core.init, args.remote, args.branch, args.project, args.adopt_existing, args.okf_starter)
    if args.command == "status":
        return core.emit("status", core.status, args.project)
    if args.command == "backup":
        return core.emit("backup", core.backup, args.project, args.message)
    if args.command == "sync":
        return core.emit("sync", core.sync, args.project, args.push, args.confirm_branch)
    if args.command == "validate":
        if args.migrate:
            return _parser_error_json("validate", "--migrate is not supported by this skill. Edit files manually to upgrade to OKF v0.2.")
        from okf_bundle_validate import validate_bundle
        result = validate_bundle(args.project, strict=args.strict)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return int(result["code"])
    return 1  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())
