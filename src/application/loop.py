"""HeuristicLoop — layout constraint controller.

Fits ResolvedContent into TailoredConfig.max_pages via iterative adjustments
in this fixed order:
  Step A — reduce margin + gutter  (up to SPACING_MAX_ITERATIONS)
  Step B — font size binary search  (floor: config.min_font_size_pt)
  Step C — prune the lowest-priority ExperienceItem

Dependency rule: domain/ and application/ports ONLY.
MUST NOT import from infra/, selection.py, grounding.py, or litellm.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..domain.actions import Action
from ..domain.exceptions import LayoutError
from ..domain.models import GenerationArtifact, LayoutParams, ResolvedContent, TailoredConfig
from ..domain.state import GenerationState
from .ports import RendererPort

logger = logging.getLogger(__name__)


class HeuristicLoop:
    """Fits ResolvedContent into TailoredConfig.max_pages.

    Inject a RendererPort — never instantiate Renderer directly here.

    Example::

        loop = HeuristicLoop(renderer=my_renderer)
        artifact = loop.run(content, config, tmp_dir)
    """

    SPACING_MAX_ITERATIONS = 3
    SPACING_MARGIN_DELTA_PT = -4.0
    SPACING_GUTTER_DELTA_PT = -1.0
    FONT_BINARY_SEARCH_MAX_ITER = 8
    STALL_DETECTION_WINDOW = 2

    def __init__(self, renderer: RendererPort) -> None:
        self._renderer = renderer

    # ── public ────────────────────────────────────────────────────────────────

    def run(
        self,
        content: ResolvedContent,
        config: TailoredConfig,
        tmp_dir: Path,
    ) -> GenerationArtifact:
        """Run the heuristic loop.

        Returns:
            GenerationArtifact with PDF bytes and audit log.

        Raises:
            LayoutError: if content cannot fit even after all pruning.
        """
        raise NotImplementedError
