# .agents/skills/harness/run-all-tests/tests/conftest.py
# sys.path에 .agents/harness/ 추가
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core-engine"))

import pytest

FRONTMATTER = (
    "---\nactive: true\niteration: 1\nmax_iterations: 30\n"
    'completion_promise: "HARNESS_COMPLETE"\ncli: claude\n'
    'harness_version: "1.0"\nstarted_at: "2026-01-01T00:00:00Z"\n'
    "last_run: null\n---\n\ntest prompt\n"
)

@pytest.fixture
def tmp_state_file(tmp_path):
    f = tmp_path / "loop-state.md"
    f.write_text(FRONTMATTER)
    return f

@pytest.fixture
def tmp_history_file(tmp_path):
    f = tmp_path / "HISTORY.md"
    f.write_text("")
    return f
