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
