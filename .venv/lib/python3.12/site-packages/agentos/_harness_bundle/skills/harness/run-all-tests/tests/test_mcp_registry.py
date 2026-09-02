import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
HELPER = REPO_ROOT / ".agents" / "mcp" / "scripts" / "render-codex-mcp-config.py"


def run_helper(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(HELPER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_real_mcp_list_outputs_runnable_servers_only():
    result = run_helper("--list")

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line]
    assert lines[0] == "name\tactivation\tpurpose"
    rows = {line.split("\t")[0]: line.split("\t") for line in lines[1:]}
    for name in ["penpot", "figma", "stitch", "chrome-devtools", "n8n"]:
        assert name in rows
        assert rows[name][1] == "on_demand"
        assert rows[name][2]
    assert "playwright" not in result.stdout
    assert "serena" not in result.stdout


def test_real_mcp_free_render_outputs_closed_codex_config():
    result = run_helper("--server", "none", "--print-argv")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["-c", "mcp_servers={}"]


def test_real_selected_mcp_render_outputs_only_selected_servers():
    result = run_helper(
        "--server",
        "penpot",
        "--server",
        "stitch",
        "--print-argv",
    )

    assert result.returncode == 0, result.stderr
    assert "mcp_servers.penpot.url" in result.stdout
    assert "mcp_servers.stitch.command" in result.stdout
    assert "mcp_servers.stitch.args" in result.stdout
    assert "mcp_servers={}" not in result.stdout
    assert "figma" not in result.stdout
    assert "playwright" not in result.stdout


def test_real_n8n_mcp_render_uses_project_wrapper():
    result = run_helper("--server", "n8n", "--print-argv")

    assert result.returncode == 0, result.stderr
    assert 'mcp_servers.n8n.command="bash"' in result.stdout
    assert 'mcp_servers.n8n.args=[".codex/scripts/start-n8n-mcp.sh"]' in result.stdout
    assert "mcp_servers={}" not in result.stdout


def test_real_unknown_mcp_render_fails():
    result = run_helper("--server", "unknown", "--print-argv")

    assert result.returncode == 2
    assert "unknown runnable MCP server: unknown" in result.stderr


@pytest.mark.parametrize(
    ("codex", "expected"),
    [
        ({"url": 123}, "codex.url must be a non-empty string"),
        ({"command": 123}, "codex.command must be a non-empty string"),
        ({"command": "bash", "args": "not-a-list"}, "codex.args must be a list of strings"),
        ({"command": "bash", "args": ["ok", 3]}, "codex.args must be a list of strings"),
    ],
)
def test_registry_codex_value_types_are_validated(tmp_path, codex, expected):
    registry = tmp_path / "mcp.json"
    registry.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "bad": {
                        "purpose": "Bad test server",
                        "activation": "on_demand",
                        "codex": codex,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = run_helper("--registry", str(registry), "--server", "bad", "--print-argv")

    assert result.returncode == 2
    assert expected in result.stderr
