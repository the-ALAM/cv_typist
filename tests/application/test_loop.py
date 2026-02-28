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
    """Verify the loop accepts the right types and raises NotImplementedError (Phase 1)."""

    def test_instantiates_with_renderer(self, mock_renderer) -> None:
        loop = HeuristicLoop(renderer=mock_renderer)
        assert loop is not None

    def test_run_raises_not_implemented(self, mock_renderer, sample_resolved, default_config, tmp_work_dir) -> None:
        loop = HeuristicLoop(renderer=mock_renderer)
        with pytest.raises(NotImplementedError):
            loop.run(sample_resolved, default_config, tmp_work_dir)


# ── Phase 2 tests (uncomment when HeuristicLoop.run is implemented) ───────────

# class TestHeuristicLoopFitsOnePage:
#     def test_already_fits_returns_immediately(self, mock_renderer, sample_resolved, default_config, tmp_work_dir):
#         loop = HeuristicLoop(renderer=mock_renderer)
#         pdf_bytes, state = loop.run(sample_resolved, default_config, tmp_work_dir)
#         assert state.current_page_count == 1
#         assert mock_renderer.render.call_count == 1
#
#     def test_spacing_reduction_applied_first(self, mock_renderer_2pages, sample_resolved, tmp_work_dir):
#         config = TailoredConfig(max_pages=1)
#         # After 3 spacing iterations renderer starts returning 1 page
#         call_count = 0
#         def render_side_effect(content, layout, tmp_dir):
#             nonlocal call_count
#             call_count += 1
#             return (b"%PDF", 2 if call_count <= 3 else 1)
#         mock_renderer_2pages.render.side_effect = render_side_effect
#         loop = HeuristicLoop(renderer=mock_renderer_2pages)
#         pdf_bytes, state = loop.run(sample_resolved, config, tmp_work_dir)
#         assert state.current_page_count == 1
