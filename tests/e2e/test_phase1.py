"""Phase 1 gate: CLI & Templating foundation.

Pass criteria (spec §1 Success Gate):
  1. test_typst_escape_special_chars — #, \\, " escaped in rendered .typ string
  2. test_renderer_returns_pdf_bytes — non-empty bytes and page_count >= 1
  3. test_renderer_template_isolation — _render_template() works without Typst
  4. test_cli_produces_output_file — CLI writes a valid PDF to disk
  5. test_pdf_contains_all_experiences — open PDF with pypdf, verify all experience text

Run: uv run pytest tests/e2e/test_phase1.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from pypdf import PdfReader

from src.domain.models import ExperienceItem, LayoutParams, ResolvedContent
from src.infra.renderer import Renderer, _typst_escape


# ── Fixtures ──────────────────────────────────────────────────────────────────

TEMPLATES_DIR = Path("templates")


@pytest.fixture
def renderer() -> Renderer:
    return Renderer(templates_dir=TEMPLATES_DIR)


@pytest.fixture
def content_with_special_chars() -> ResolvedContent:
    """Content that exercises the escape filter with #, \\, and " characters."""
    return ResolvedContent(
        experiences=[
            ExperienceItem(
                id="esc-test",
                role='Engineer at "BigCo"',
                company='O"Brien & Partners',
                date="2022-01 – 2024-03",
                bullets=[
                    'Designed #custom Grafana queries for metrics',
                    'Used C:\\ paths in deployment scripts',
                    'Said "hello" to the world',
                ],
                keywords=["Python"],
                priority=0.9,
            ),
        ]
    )


@pytest.fixture
def six_experience_content() -> ResolvedContent:
    """Content with 6 experiences to test full rendering."""
    exps = [
        ExperienceItem(
            id=f"exp-{i:03d}", role=f"Role {i}", company=f"Company {i}",
            date=f"20{20+i}-01 – 20{21+i}-12",
            bullets=[f"Bullet A for role {i}", f"Bullet B for role {i}"],
            keywords=["Python"], priority=round(1.0 - i * 0.15, 2),
        )
        for i in range(1, 7)
    ]
    return ResolvedContent(experiences=exps)


# ── Gate Test 1: Escape filter ────────────────────────────────────────────────

@pytest.mark.e2e
class TestTypstEscapeSpecialChars:
    def test_hash_escaped(self) -> None:
        assert "\\#" in _typst_escape("#custom")

    def test_backslash_escaped(self) -> None:
        assert "\\\\" in _typst_escape("C:\\path")

    def test_quote_escaped(self) -> None:
        assert '\\"' in _typst_escape('"hello"')

    def test_all_three_in_rendered_typ(self, renderer: Renderer, content_with_special_chars: ResolvedContent) -> None:
        typ_source = renderer._render_template(content_with_special_chars, LayoutParams())
        assert "\\#" in typ_source
        assert "\\\\" in typ_source
        assert '\\"' in typ_source
        # Raw dangerous chars should NOT appear unescaped in string contexts
        # (They may still appear in Typst markup outside strings, which is fine)


# ── Gate Test 2: Renderer returns PDF bytes ───────────────────────────────────

@pytest.mark.e2e
@pytest.mark.integration
class TestRendererReturnsPdfBytes:
    def test_returns_non_empty_bytes(self, renderer: Renderer, sample_resolved: ResolvedContent) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_bytes, page_count = renderer.render(sample_resolved, LayoutParams(), Path(tmp))
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert page_count >= 1


# ── Gate Test 3: Template isolation (no Typst needed) ─────────────────────────

@pytest.mark.e2e
class TestRendererTemplateIsolation:
    def test_render_template_returns_typ_string(self, renderer: Renderer, sample_resolved: ResolvedContent) -> None:
        typ_source = renderer._render_template(sample_resolved, LayoutParams())
        assert isinstance(typ_source, str)
        assert "#set page(" in typ_source
        assert "#experience_block(" in typ_source
        assert "Software Engineer" in typ_source


# ── Gate Test 4: CLI produces output file ─────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.integration
class TestCliProducesOutputFile:
    def test_cli_writes_pdf(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner
        from src.entrypoints.cli import app

        output_path = tmp_path / "result.pdf"
        runner = CliRunner()
        result = runner.invoke(app, [
            "--master", "data/master_example.yaml",
            "--config", "data/config_example.yaml",
            "--output", str(output_path),
        ])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Verify it's a valid PDF
        reader = PdfReader(str(output_path))
        assert len(reader.pages) >= 1


# ── Gate Test 5: PDF contains all experiences ─────────────────────────────────

@pytest.mark.e2e
@pytest.mark.integration
class TestPdfContainsAllExperiences:
    def test_all_experiences_in_pdf(self, renderer: Renderer, six_experience_content: ResolvedContent) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_bytes, _ = renderer.render(six_experience_content, LayoutParams(), Path(tmp))

        import io
        reader = PdfReader(io.BytesIO(pdf_bytes))
        full_text = "".join(page.extract_text() or "" for page in reader.pages)

        for exp in six_experience_content.experiences:
            assert exp.role in full_text, f"Role '{exp.role}' not found in PDF"
            assert exp.company in full_text, f"Company '{exp.company}' not found in PDF"


# ── Existing tests (kept for compatibility) ───────────────────────────────────

@pytest.mark.e2e
class TestPhase1CLI:
    def test_cli_app_importable(self) -> None:
        from src.entrypoints.cli import app
        assert app is not None

    def test_cli_has_generate_command(self) -> None:
        from src.entrypoints.cli import app
        command_names = [
            cmd.name or (cmd.callback.__name__ if cmd.callback else None)
            for cmd in app.registered_commands
        ]
        assert "generate" in command_names
