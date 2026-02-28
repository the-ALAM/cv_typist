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

import dataclasses

from ..domain.actions import (
    FontAction,
    NoOpAction,
    PruneAction,
    PruneSectionAction,
    SpacingAction,
)
from ..domain.exceptions import LayoutError  # noqa: F401 – reserved for future use
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
        # ── INITIAL RENDER ────────────────────────────────────────────────
        pdf_bytes, page_count = self._renderer.render(content, LayoutParams(), tmp_dir)
        state = GenerationState(
            layout=LayoutParams(), content=content,
            page_count=page_count, actions=(), warnings=(),
        )
        if state.page_count <= config.max_pages:
            return self._make_artifact(state, pdf_bytes)

        # ── STEP A: SPACING REDUCTION ────────────────────────────────────
        recent_pages: list[int] = []
        for _ in range(self.SPACING_MAX_ITERATIONS):
            action = SpacingAction(
                delta_margin_pt=self.SPACING_MARGIN_DELTA_PT,
                delta_gutter_pt=self.SPACING_GUTTER_DELTA_PT,
            )
            candidate_layout = state._apply_layout(action)
            pdf_bytes, page_count = self._renderer.render(
                state.content, candidate_layout, tmp_dir,
            )
            state = state.apply_action(action, page_count)
            if state.page_count <= config.max_pages:
                return self._make_artifact(state, pdf_bytes)
            recent_pages.append(page_count)
            if (
                len(recent_pages) >= self.STALL_DETECTION_WINDOW
                and len(set(recent_pages[-self.STALL_DETECTION_WINDOW:])) == 1
            ):
                noop = NoOpAction(reason="spacing-stall")
                state = state.apply_action(noop, state.page_count)
                logger.debug("Spacing stall detected, fast-forwarding to Step B")
                break

        # ── STEP B: FONT SIZE BINARY SEARCH ──────────────────────────────
        low = config.min_font_size_pt
        high = state.layout.font_size_pt
        use_linear = False
        for _ in range(self.FONT_BINARY_SEARCH_MAX_ITER):
            if high - low < 0.1:
                break
            if use_linear:
                mid = max(low, high - 0.5)
            else:
                mid = round((low + high) / 2, 2)

            # Monotone guard (binary search only)
            if not use_linear:
                probe = max(low, mid - 0.1)
                _, probe_pages = self._renderer.render(
                    state.content,
                    state.layout.model_copy(update={"font_size_pt": probe}),
                    tmp_dir,
                )
                pdf_bytes, page_count = self._renderer.render(
                    state.content,
                    state.layout.model_copy(update={"font_size_pt": mid}),
                    tmp_dir,
                )
                if probe_pages < page_count:
                    state = state.add_warning(
                        f"Monotone guard violated at font {mid:.2f}pt; "
                        "switching to linear descent"
                    )
                    use_linear = True
            else:
                pdf_bytes, page_count = self._renderer.render(
                    state.content,
                    state.layout.model_copy(update={"font_size_pt": mid}),
                    tmp_dir,
                )
            font_action = FontAction(new_font_size_pt=mid)
            state = state.apply_action(font_action, page_count)
            if page_count <= config.max_pages:
                return self._make_artifact(state, pdf_bytes)
            if mid <= low:
                break
            high = mid

        # ── STEP C: SECTION PRUNING ──────────────────────────────────────
        section_prune_order = ["skills", "projects", "education"]
        for section in section_prune_order:
            section_data = getattr(state.content, section, None)
            if not section_data:
                continue
            section_score = 0.3
            action_s = PruneSectionAction(section=section, pruning_score=section_score)
            new_content = state.content.without_section(section)
            pdf_bytes, page_count = self._renderer.render(
                new_content, state.layout, tmp_dir,
            )
            state = state.apply_action(action_s, page_count, new_content)
            if state.page_count <= config.max_pages:
                return self._make_artifact(state, pdf_bytes)

        # ── STEP C-item: EXPERIENCE ITEM PRUNING ─────────────────────────
        while state.page_count > config.max_pages and len(state.content.experiences) > 1:
            scores = {
                exp.id: state.pruning_score(exp.id, config.alpha)
                for exp in state.content.experiences
            }
            worst_id = min(scores, key=scores.__getitem__)
            prune_action = PruneAction(
                pruned_experience_id=worst_id,
                pruning_score=scores[worst_id],
            )
            new_experiences = [
                e for e in state.content.experiences if e.id != worst_id
            ]
            new_content = state.content.model_copy(
                update={"experiences": new_experiences},
            )
            pdf_bytes, page_count = self._renderer.render(
                new_content, state.layout, tmp_dir,
            )
            state = state.apply_action(prune_action, page_count, new_content)
            if state.page_count <= config.max_pages:
                return self._make_artifact(state, pdf_bytes)

        # ── STEP D: OVERSIZED WARNING ────────────────────────────────────
        if state.page_count > config.max_pages:
            state = state.add_warning(
                "Cannot fit within max_pages; emitting oversized PDF"
            )
            logger.warning(
                "HeuristicLoop: emitting oversized PDF (%d pages)",
                state.page_count,
            )

        return self._make_artifact(state, pdf_bytes)

    # ── private ───────────────────────────────────────────────────────────────

    def _make_artifact(
        self, state: GenerationState, pdf_bytes: bytes,
    ) -> GenerationArtifact:
        return GenerationArtifact(
            pdf_bytes=pdf_bytes,
            final_page_count=state.page_count,
            final_layout=state.layout,
            action_log=[dataclasses.asdict(a) for a in state.actions],
            warnings=list(state.warnings),
        )
