from pathlib import Path
import sys
sys.path.insert(0, ".agents/skills/harness/run-all-tests/tests")
from test_mcp_lifecycle import write_reviewed_active_plan

sys.path.insert(0, ".agents/skills/harness/writing-plans/scripts")
from review_artifacts import check_plan

tmp = Path("/tmp/debug-agentos")
import shutil
shutil.rmtree(tmp, ignore_errors=True)
tmp.mkdir()

plan_path = write_reviewed_active_plan(tmp, mcp_servers="[lifecycle-probe]")
check = check_plan(tmp, plan_path)
print("VALID:", check.valid)
print("MISSING:", check.missing)
print("INVALID:", check.invalid)

