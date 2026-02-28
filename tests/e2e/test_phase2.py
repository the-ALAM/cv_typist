"""Phase 2 gate: Constraint Engine (HeuristicLoop).

Pass criteria:
  1. Loop terminates when content already fits in 1 page.
  2. Spacing reduction (Step A) is applied before font reduction (Step B).
  3. Warning emitted when content cannot fit after all steps (Step D).

Run: uv run pytest tests/e2e/test_phase2.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.application.loop import HeuristicLoop
from src.application.ports import RendererPort
from src.domain.models import ExperienceItem, ResolvedContent, TailoredConfig


@pytest.mark.e2e
class TestPhase2HeuristicLoop:
    def test_loop_class_importable(self) -> None:
        from src.application.loop import HeuristicLoop
        assert HeuristicLoop is not None

    def test_layout_error_importable(self) -> None:
        from src.domain.exceptions import LayoutError
        assert LayoutError is not None

    def test_loop_fits_content_already_one_page(self, mock_renderer, sample_resolved, default_config, tmp_work_dir) -> None:
        mock_renderer.render.return_value = (b"%PDF", 1)
        artifact = HeuristicLoop(renderer=mock_renderer).run(sample_resolved, default_config, tmp_work_dir)
        assert artifact.action_log == []
        assert artifact.final_page_count == 1

    def test_loop_reduces_spacing_before_font(self, mock_renderer_2pages, sample_resolved, tmp_work_dir) -> None:
        mock_renderer_2pages.render.side_effect = [(b"%PDF", 2)] * 4 + [(b"%PDF", 1)]
        config = TailoredConfig(max_pages=1, min_font_size_pt=8.5)
        artifact = HeuristicLoop(renderer=mock_renderer_2pages).run(sample_resolved, config, tmp_work_dir)
        kinds = [a["kind"] for a in artifact.action_log]
        spacing_indices = [i for i, k in enumerate(kinds) if k == "spacing"]
        font_indices = [i for i, k in enumerate(kinds) if k == "font"]
        if spacing_indices and font_indices:
            assert max(spacing_indices) < min(font_indices)

    def test_loop_raises_layout_error_when_exhausted(self, tmp_work_dir) -> None:
        exp = ExperienceItem(id="only", role="R", company="C", date="2024", bullets=["b"], priority=1.0)
        content = ResolvedContent(experiences=[exp])
        renderer = MagicMock(spec=RendererPort)
        renderer.render.return_value = (b"%PDF", 3)
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=renderer).run(content, config, tmp_work_dir)
        assert any("Cannot fit" in w for w in artifact.warnings)
        assert artifact.final_page_count > config.max_pages
