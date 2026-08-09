#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from review_artifacts import check_plan
except ModuleNotFoundError:
    print("execution-gate: review_artifacts module not found", file=sys.stderr)
    sys.exit(2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    plan_path = args.plan
    if plan_path.startswith(str(root)):
        plan_path = Path(plan_path).relative_to(root).as_posix()

    check = check_plan(root, plan_path)
    if check.valid:
        sys.exit(0)
    
    issues = []
    if check.missing:
        issues.append("missing=" + ",".join(check.missing))
    if check.invalid:
        issues.append("invalid=" + ",".join(check.invalid.keys()))
        
    print(f"FAIL execution-gate { ' '.join(issues) }")
    print(f"Run recovery command: python3 .agents/skills/harness/writing-plans/scripts/review_artifacts.py check --plan {plan_path}")
    sys.exit(2)

if __name__ == "__main__":
    main()
