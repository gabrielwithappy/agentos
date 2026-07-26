from __future__ import annotations

import asyncio
from pathlib import Path

from agentos.terminal.tui.app import AgentOSTui
from agentos.terminal.tui.widgets import Transcript


def test_role_visual_contract_exports_narrow_and_wide_svg_evidence(tmp_path, monkeypatch):
    """The role/status boundary stays readable without relying on colour."""

    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        monkeypatch.setenv("NO_COLOR", "1")
        evidence_dir = Path.cwd() / ".agents/traces/visual/2026-07-26-tui-request-result-separation"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test(size=(80, 24)) as pilot:
            transcript = pilot.app.query_one("#transcript", Transcript)
            transcript.add_message("user", "A request that remains distinguishable in a narrow terminal.")
            assistant = transcript.add_message("assistant", "A final result with its own visible boundary.")
            assistant.set_presentation_status("complete")
            await pilot.pause()
            narrow = pilot.app.export_screenshot(title="AgentOS request/result narrow")
            (evidence_dir / "request-result-80x24.svg").write_text(narrow, encoding="utf-8")

        wide_app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with wide_app.run_test(size=(140, 40)) as pilot:
            transcript = pilot.app.query_one("#transcript", Transcript)
            transcript.add_message("user", "Wide request")
            assistant = transcript.add_message("assistant", "Wide complete result")
            assistant.set_presentation_status("complete")
            await pilot.pause()
            wide = pilot.app.export_screenshot(title="AgentOS request/result wide")
            (evidence_dir / "request-result-140x40.svg").write_text(wide, encoding="utf-8")

        # Rich's SVG serializer escapes spaces as non-breaking spaces.
        complete_header = "AgentOS&#160;·&#160;complete"
        assert "You" in narrow and complete_header in narrow
        assert "You" in wide and complete_header in wide

    asyncio.run(run())
