"""Phase 2 gate: Constraint Engine (HeuristicLoop).

Pass criteria:
  1. Loop terminates when content already fits in 1 page.
  2. Spacing reduction (Step A) is applied first, up to 3 iterations.
  3. Font size reduction (Step B) respects min_font_size floor.
  4. Pruning (Step C) removes the lowest-priority ExperienceItem.
  5. LayoutError raised when content cannot fit after all steps.

Run: uv run pytest tests/e2e/test_phase2.py -v
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestPhase2HeuristicLoop:
    def test_loop_class_importable(self) -> None:
        from src.application.loop import HeuristicLoop
        assert HeuristicLoop is not None

    def test_layout_error_importable(self) -> None:
        from src.domain.exceptions import LayoutError
        assert LayoutError is not None

    def test_loop_fits_content_already_one_page(self, mock_renderer, sample_resolved, default_config, tmp_work_dir) -> None:
        pytest.skip("Implement in Phase 2: HeuristicLoop.run()")

    def test_loop_reduces_spacing_before_font(self, mock_renderer, sample_resolved, tmp_work_dir) -> None:
        pytest.skip("Implement in Phase 2: Step A before Step B")

    def test_loop_raises_layout_error_when_exhausted(self, mock_renderer, sample_resolved, tmp_work_dir) -> None:
        pytest.skip("Implement in Phase 2: LayoutError on exhaustion")
