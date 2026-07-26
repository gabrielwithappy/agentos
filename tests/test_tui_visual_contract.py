from __future__ import annotations

import asyncio
from pathlib import Path

from rich.cells import cell_len
from rich.style import Style

from agentos.terminal.tui.app import AgentOSTui
from agentos.terminal.tui.state import TuiStatus
from agentos.terminal.tui.widgets import StatusFooter, Transcript


def _contrast(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        value = value.lstrip("#")
        channels = [int(value[index : index + 2], 16) / 255 for index in range(0, 6, 2)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    left, right = sorted((luminance(first), luminance(second)), reverse=True)
    return (left + 0.05) / (right + 0.05)


def test_activity_emphasis_meets_contrast_in_dark_and_light(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            colors: list[str] = []
            for theme in ("textual-dark", "textual-light"):
                pilot.app.theme = theme
                await pilot.pause()
                variables = pilot.app.get_css_variables()
                colors.append(variables["text-primary"])
                assert _contrast(variables["text-primary"], variables["background"]) >= 4.5
                assert _contrast(variables["text-primary"], variables["surface"]) >= 4.5
            assert colors[0] != colors[1]

    import asyncio
    asyncio.run(run())


def test_transcript_scrollbar_is_one_cell_wide(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test() as pilot:
            assert pilot.app.query_one("#transcript", Transcript).styles.scrollbar_size_vertical == 1

    import asyncio
    asyncio.run(run())


def test_composer_border_fits_within_screen_width(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        for size in ((80, 24), (140, 40)):
            app = AgentOSTui(provider="mock", create_session_on_start=False)
            async with app.run_test(size=size) as pilot:
                composer = pilot.app.query_one("#composer")
                assert composer.region.x + composer.region.width <= pilot.app.size.width

    import asyncio
    asyncio.run(run())


def test_compact_footer_fits_cell_width_at_eighty_and_sixty_columns():
    status = TuiStatus(
        cwd="/작업/매우-긴-프로젝트-경로",
        provider="provider-with-a-long-name",
        model="모델-긴-이름",
        session="abcdefgh",
        hooks="3",
        last_turn="error",
        git_branch="feature/아주-긴-브랜치",
        conversation_branch="fork-대화-분기",
        total_input_chars=12345,
        total_output_chars=67890,
    )
    for width in (80, 60, 20):
        text = status.compact_footer_text(width)
        assert cell_len(text) <= width
        if width >= 60:
            for label in ("pm:", "sid:", "turn:", "in:", "out:"):
                assert label in text
        assert "hooks" not in text and "mode" not in text


def test_status_footer_uses_resolved_muted_label_style_in_both_themes(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test(size=(80, 24)) as pilot:
            footer = pilot.app.query_one("#status", StatusFooter)
            for theme in ("textual-dark", "textual-light"):
                pilot.app.theme = theme
                pilot.app._render_status_footer()
                await pilot.pause()
                rendered = footer.render()
                assert "pm:" in str(rendered) and "mock/mock" in str(rendered)
                assert footer.styles.color.a < 1
                assert footer.rich_style.color is not None
                assert _contrast(footer.rich_style.color.get_truecolor().hex, footer.rich_style.bgcolor.get_truecolor().hex) >= 4.5
                assert _contrast(value_style := pilot.app.get_css_variables()["text-primary"], footer.rich_style.bgcolor.get_truecolor().hex) >= 4.5
                assert Style.parse(value_style).color is not None
                assert any(span.style is not None for span in rendered.spans)

    import asyncio
    asyncio.run(run())


def test_compact_footer_mount_never_overflows_screen_width(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        for width in (80, 60, 20):
            app = AgentOSTui(provider="mock", create_session_on_start=False)
            async with app.run_test(size=(width, 24)) as pilot:
                footer = pilot.app.query_one("#status", StatusFooter)
                assert cell_len(str(footer.render())) <= footer.size.width

    import asyncio
    asyncio.run(run())


def test_status_footer_updates_through_all_app_status_paths(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test(size=(80, 24)) as pilot:
            footer = pilot.app.query_one("#status", StatusFooter)
            calls = 0
            original = footer.update_status
            def tracked(status):
                nonlocal calls
                calls += 1
                original(status)
            monkeypatch.setattr(footer, "update_status", tracked)
            pilot.app._update_status(pilot.app.status.with_last_turn("running"))
            pilot.app._open_theme_picker()
            await pilot.pause()
            pilot.app.screen.dismiss("textual-light")
            await pilot.pause()
            assert calls >= 2
            assert "turn:running" in str(footer.render())
            source = Path("agentos/terminal/tui/app.py").read_text(encoding="utf-8")
            assert source.count("_render_status_footer()") >= 7
            assert "summary = self.status.footer_text()" in source
            assert "console.print(status.footer_text())" in source

    import asyncio
    asyncio.run(run())


def test_compact_footer_keeps_ascii_labels_with_no_color(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        monkeypatch.setenv("NO_COLOR", "1")
        app = AgentOSTui(provider="mock", create_session_on_start=False)
        async with app.run_test(size=(80, 24)) as pilot:
            footer = str(pilot.app.query_one("#status", StatusFooter).render())
            for label in ("pm:", "sid:", "turn:", "in:", "out:"):
                assert label in footer

    import asyncio
    asyncio.run(run())


def test_compact_footer_keeps_required_labels_and_recovery_semantics():
    status = TuiStatus(cwd="/workspace", provider="mock", model="mock", session="session", hooks="0", last_turn="error", git_branch="main", conversation_branch="fork-a", total_input_chars=1, total_output_chars=2)
    text = status.compact_footer_text(120)
    for label in ("cwd:", "pm:", "sid:", "git:", "convo:", "turn:error", "in:1", "out:2"):
        assert label in text
    assert "/status" in Path("docs/cli-reference.md").read_text(encoding="utf-8")


def test_theme_and_status_panel_exports_dark_and_light_svg_evidence(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        evidence_dir = Path.cwd() / ".agents/traces/visual/2026-07-26-tui-theme-and-status-panel"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        for theme, filename in (("textual-dark", "dark-80x24.svg"), ("textual-light", "light-80x24.svg")):
            app = AgentOSTui(provider="mock", create_session_on_start=False)
            async with app.run_test(size=(80, 24)) as pilot:
                pilot.app.theme = theme
                pilot.app._render_status_footer()
                await pilot.pause()
                path = evidence_dir / filename
                path.write_text(pilot.app.export_screenshot(title=f"AgentOS {theme} theme/status"), encoding="utf-8")
                assert path.is_file() and path.stat().st_size > 0

    import asyncio
    asyncio.run(run())


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


def test_user_background_block_preserves_no_color_role_contract(tmp_path, monkeypatch):
    """NO_COLOR still leaves headers and left boundaries as the role signal."""

    async def run() -> None:
        monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "home"))
        monkeypatch.setenv("NO_COLOR", "1")
        evidence_dir = Path.cwd() / ".agents/traces/visual/2026-07-26-tui-message-box-format"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        for size, label in (((80, 24), "80x24"), ((140, 40), "140x40")):
            app = AgentOSTui(provider="mock", create_session_on_start=False)
            async with app.run_test(size=size) as pilot:
                transcript = pilot.app.query_one("#transcript", Transcript)
                transcript.add_message("user", "A request readable without colour.")
                assistant = transcript.add_message("assistant", "A result with the existing boundary.")
                assistant.set_presentation_status("complete")
                await pilot.pause()
                svg = pilot.app.export_screenshot(title=f"AgentOS message block {label}")
                (evidence_dir / f"message-box-{label}.svg").write_text(svg, encoding="utf-8")

                assert "You" in svg
                assert "AgentOS&#160;·&#160;complete" in svg

    asyncio.run(run())
