"""HeuristicLoop — layout constraint controller.

Fits ResolvedContent into TailoredConfig.max_pages via iterative adjustments
in this fixed order:
  Step A — reduce margin + gutter  (up to _SPACING_MAX_ITERS iterations)
  Step B — reduce font_size by _FONT_STEP  (floor: config.min_font_size)
  Step C — prune the lowest-priority ExperienceItem

Uses a binary-search style approach on font sizes to converge faster.

Dependency rule: domain/ and application/ports ONLY.
MUST NOT import from infra/, selection.py, grounding.py, or litellm.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..domain.exceptions import LayoutError
from ..domain.models import LayoutParams, ResolvedContent, TailoredConfig
from ..domain.state import GenerationState
from ..domain.types import Action
from .ports import RendererPort

logger = logging.getLogger(__name__)


class HeuristicLoop:
    """Fits ResolvedContent into TailoredConfig.max_pages.

    Inject a RendererPort — never instantiate Renderer directly here.

    Example::

        loop = HeuristicLoop(renderer=my_renderer)
        pdf_bytes, final_state = loop.run(content, config, tmp_dir)
    """

    _SPACING_REDUCTION = 0.10   # fraction per spacing iteration
    _SPACING_MAX_ITERS = 3
    _FONT_STEP = 0.5            # points per font iteration

    def __init__(self, renderer: RendererPort) -> None:
        self._renderer = renderer

    # ── public ────────────────────────────────────────────────────────────────

    def run(
        self,
        content: ResolvedContent,
        config: TailoredConfig,
        tmp_dir: Path,
    ) -> tuple[bytes, GenerationState]:
        """Run the heuristic loop.

        Returns:
            (pdf_bytes, final_state) when actual_pages <= max_pages.

        Raises:
            LayoutError: if content cannot fit even after all pruning.
        """
        raise NotImplementedError

    # ── private helpers (stubs for Phase 2) ───────────────────────────────────

    def _next_action(self, state: GenerationState, config: TailoredConfig) -> Action:
        """Decide the next adjustment step given the current state."""
        raise NotImplementedError

    def _apply_spacing_reduction(self, layout: LayoutParams) -> LayoutParams:
        """Return layout with margin and gutter reduced by _SPACING_REDUCTION."""
        raise NotImplementedError

    def _apply_font_reduction(self, layout: LayoutParams) -> LayoutParams:
        """Return layout with font_size reduced by _FONT_STEP."""
        raise NotImplementedError
