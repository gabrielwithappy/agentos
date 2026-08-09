from pathlib import Path
import re

for test_file in ["test_harness_loop.py", "test_mcp_lifecycle.py"]:
    path = Path(f".agents/skills/harness/run-all-tests/tests/{test_file}")
    content = path.read_text()
    
    # replace script_dir = root / ".agents" ...
    new_content = re.sub(
        r'script_dir = root / "\.agents" / "skills" / "harness" / "writing-plans" / "scripts"',
        'script_dir = Path("/home/gabriel/agent/prj-agent/agentos-workspace/agentos/.agents/skills/harness/writing-plans/scripts")',
        content
    )
    path.write_text(new_content)
