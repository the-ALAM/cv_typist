"""Tests for Renderer — requires Typst binary and Jinja2 installed.

Mark: @pytest.mark.integration — skipped in CI without Typst.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.domain.models import LayoutParams, ResolvedContent
from src.infra.renderer import Renderer, TypstCompilationError, _typst_escape


class TestTypstEscapeFilter:
    """Unit tests for the `te` filter — no I/O, no Typst binary needed."""

    def test_escapes_hash(self) -> None:
        assert "\\#" in _typst_escape("hello #world")

    def test_escapes_backslash(self) -> None:
        assert "\\\\" in _typst_escape("path\\to")

    def test_escapes_quote(self) -> None:
        assert '\\"' in _typst_escape('say "hello"')

    def test_plain_text_unchanged(self) -> None:
        assert _typst_escape("hello world") == "hello world"

    def test_empty_string(self) -> None:
        assert _typst_escape("") == ""

    def test_does_not_escape_dash(self) -> None:
        assert _typst_escape("2022-01 – 2024-03") == "2022-01 – 2024-03"


class TestRendererConstruction:
    def test_instantiates(self, tmp_path) -> None:
        renderer = Renderer(templates_dir=tmp_path)
        assert renderer is not None


@pytest.mark.integration
class TestRendererRender:
    def test_render_produces_pdf(self, sample_resolved, tmp_path) -> None:
        renderer = Renderer(templates_dir=Path("templates"))
        pdf_bytes, page_count = renderer.render(sample_resolved, LayoutParams(), tmp_path)
        assert len(pdf_bytes) > 0
        assert page_count >= 1

    def test_render_template_standalone(self, sample_resolved) -> None:
        renderer = Renderer(templates_dir=Path("templates"))
        typ_source = renderer._render_template(sample_resolved, LayoutParams())
        assert "#show: resume.with(" in typ_source
        assert "10.5pt" in typ_source  # default font_size_pt
