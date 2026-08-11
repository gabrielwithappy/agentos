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


def _wizard_value(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    print(f"{prompt}{suffix}: ", end="", file=sys.stderr, flush=True)
    value = input().strip()
    return value or (default or "")


def _wizard_init() -> tuple[str, str, str] | None:
    print("공유 Git remote는 미리 만들어야 합니다. token/password를 URL에 붙여 넣지 마세요.", file=sys.stderr)
    print("예: https://github.com/org/knowledge.git 또는 git@github.com:org/knowledge.git", file=sys.stderr)
    try:
        remote = _wizard_value("credential-free remote URL")
        branch = _wizard_value("기본 branch", "main")
        print("정책: local=원격에 연결하지 않음, manual=sync를 직접 실행할 때만 발행, auto=성공한 backup 뒤 원격 발행을 시도함", file=sys.stderr)
        policy = _wizard_value("동기화 정책 (local/manual/auto)", "local")
        if policy == "auto" and _wizard_value("auto 발행에 동의합니까? (yes/no)", "no").lower() != "yes":
            return None
        return remote, branch, policy
    except EOFError:
        return None


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
    init.add_argument("--remote")
    init.add_argument("--branch", default="main")
    init.add_argument("--project")
    init.add_argument("--adopt-existing", action="store_true")
    init.add_argument("--okf-starter", action="store_true",
                      help="Create an OKF v0.2 starter bundle (opt-in, no-overwrite). Cannot be combined with --adopt-existing.")
    init.add_argument("--sync-policy", choices=("local", "manual", "auto"), default="local")
    init.add_argument("--wizard", action="store_true", help="Choose remote, branch, and sync policy interactively on stderr.")

    for name in ("status", "backup", "sync"):
        command = commands.add_parser(name)
        command.add_argument("--project")
        if name == "backup":
            command.add_argument("--message", required=True)

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
        remote, branch, policy = args.remote, args.branch, args.sync_policy
        if args.wizard:
            selected = _wizard_init()
            if selected is None:
                return _parser_error_json("init", "Wizard cancelled before creating a checkout. Rerun init --wizard when ready.")
            remote, branch, policy = selected
        return core.emit("init", core.init, remote, branch, args.project, args.adopt_existing, args.okf_starter, policy)
    if args.command == "status":
        return core.emit("status", core.status, args.project)
    if args.command == "backup":
        return core.emit("backup", core.backup, args.project, args.message)
    if args.command == "sync":
        return core.emit("sync", core.sync, args.project)
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
