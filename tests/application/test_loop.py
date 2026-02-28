"""Tests for HeuristicLoop — Phase 2 implementation target.

All RendererPort interactions use the mock_renderer fixture.
No Typst binary required.
"""

from __future__ import annotations

import pytest

from src.application.loop import HeuristicLoop
from src.domain.models import LayoutParams, ResolvedContent, TailoredConfig
from src.domain.state import GenerationState


class TestHeuristicLoopInterface:
    """Verify the loop accepts the right types and returns an artifact."""

    def test_instantiates_with_renderer(self, mock_renderer) -> None:
        loop = HeuristicLoop(renderer=mock_renderer)
        assert loop is not None

    def test_run_returns_artifact(self, mock_renderer, sample_resolved, default_config, tmp_work_dir) -> None:
        loop = HeuristicLoop(renderer=mock_renderer)
        artifact = loop.run(sample_resolved, default_config, tmp_work_dir)
        assert artifact.pdf_bytes is not None
        assert artifact.final_page_count >= 1
