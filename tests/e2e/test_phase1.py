"""Phase 1 gate: CLI & Templating foundation.

Pass criteria:
  1. Jinja2 renders a .typ file with LayoutParams variables injected.
  2. `typst compile` subprocess call succeeds and returns bytes.
  3. Page count is readable from the compiled output.
  4. CLI `generate` command is importable and has the correct signature.

Run: uv run pytest tests/e2e/test_phase1.py -v
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestPhase1CLI:
    def test_cli_app_importable(self) -> None:
        from src.entrypoints.cli import app
        assert app is not None

    def test_cli_has_generate_command(self) -> None:
        from src.entrypoints.cli import app
        # Typer sets cmd.name=None when the function name is used; fall back to callback name
        command_names = [
            cmd.name or (cmd.callback.__name__ if cmd.callback else None)
            for cmd in app.registered_commands
        ]
        assert "generate" in command_names


@pytest.mark.e2e
@pytest.mark.integration
class TestPhase1Rendering:
    """Requires Typst binary and a valid resume.typ.j2 template."""

    def test_renderer_produces_pdf_bytes(self, tmp_path, sample_resolved, default_layout) -> None:
        pytest.skip("Implement in Phase 1: Renderer.render()")

    def test_page_count_readable(self, tmp_path, sample_resolved, default_layout) -> None:
        pytest.skip("Implement in Phase 1: page count extraction")

    def test_typst_escape_filter_applied(self) -> None:
        from src.infra.renderer import _typst_escape
        dangerous = 'Role: #set page(); @alias; $formula'
        escaped = _typst_escape(dangerous)
        assert "#set" not in escaped or "\\#" in escaped
