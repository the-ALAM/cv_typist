"""Tests for Renderer — requires Typst binary and Jinja2 installed.

Mark: @pytest.mark.integration — skipped in CI without Typst.
"""

from __future__ import annotations

import pytest

from src.infra.renderer import Renderer, _typst_escape


class TestTypstEscapeFilter:
    """Unit tests for the `te` filter — no I/O, no Typst binary needed."""

    def test_escapes_hash(self) -> None:
        assert "\\#" in _typst_escape("hello #world")

    def test_escapes_at(self) -> None:
        assert "\\@" in _typst_escape("user@example.com")

    def test_escapes_dollar(self) -> None:
        assert "\\$" in _typst_escape("earn $100k")

    def test_plain_text_unchanged(self) -> None:
        assert _typst_escape("hello world") == "hello world"

    def test_empty_string(self) -> None:
        assert _typst_escape("") == ""


@pytest.mark.integration
class TestRendererConstruction:
    def test_instantiates(self, tmp_path) -> None:
        renderer = Renderer(templates_dir=tmp_path)
        assert renderer is not None

    def test_render_raises_not_implemented(self, tmp_path, sample_resolved, default_layout) -> None:
        renderer = Renderer(templates_dir=tmp_path)
        with pytest.raises(NotImplementedError):
            renderer.render(sample_resolved, default_layout, tmp_path)
