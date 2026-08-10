import argparse
import sys
from knowledge_core import KnowledgeCore

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    p_init = subparsers.add_parser("init")
    p_init.add_argument("--remote")
    p_init.add_argument("--branch")
    p_init.add_argument("--project")
    p_init.add_argument("--adopt-existing", action="store_true")
    
    p_status = subparsers.add_parser("status")
    p_status.add_argument("--project")
    
    p_backup = subparsers.add_parser("backup")
    p_backup.add_argument("--message")
    p_backup.add_argument("--project")
    
    p_sync = subparsers.add_parser("sync")
    p_sync.add_argument("--push", action="store_true")
    p_sync.add_argument("--confirm-branch")
    p_sync.add_argument("--project")
    
    args = parser.parse_args()
    
    core = KnowledgeCore()
    
    if args.command == "init":
        core.init(args.remote, args.branch, args.project, args.adopt_existing)
    elif args.command == "backup":
        core.backup(args.project, args.message)

if __name__ == "__main__":
    main()
