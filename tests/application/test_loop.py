"""Tests for HeuristicLoop — Phase 2 gate tests.

All RendererPort interactions use mock renderers (no Typst binary required).
"""

from __future__ import annotations

import functools
import dataclasses
from unittest.mock import MagicMock

import pytest

from src.application.loop import HeuristicLoop
from src.application.ports import RendererPort
from src.domain.actions import (
    FontAction,
    NoOpAction,
    PruneAction,
    PruneBulletAction,
    PruneSectionAction,
    SpacingAction,
)
from src.domain.models import (
    ExperienceItem,
    LayoutParams,
    ProjectItem,
    ResolvedContent,
    TailoredConfig,
)
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


# ── Test 1 ────────────────────────────────────────────────────────────────────


class TestLoopFitsImmediately:
    def test_already_fits_returns_no_actions(self, mock_renderer, sample_resolved, tmp_work_dir):
        """If initial render is 1 page and max_pages=1, action log must be empty."""
        mock_renderer.render.return_value = (b"%PDF", 1)
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=mock_renderer).run(sample_resolved, config, tmp_work_dir)
        assert artifact.final_page_count == 1
        assert artifact.action_log == []


# ── Test 2 ────────────────────────────────────────────────────────────────────


class TestStepOrdering:
    def test_spacing_actions_precede_font_actions(self, mock_renderer, sample_resolved, tmp_work_dir):
        """All SpacingActions in the log must appear before any FontAction."""
        # 1 initial + 2 spacing (stall) + 2 binary search (probe+mid) = 5
        side_effects = [(b"%PDF", 2)] * 4 + [(b"%PDF", 1)]
        mock_renderer.render.side_effect = side_effects
        config = TailoredConfig(max_pages=1, min_font_size_pt=8.5)
        artifact = HeuristicLoop(renderer=mock_renderer).run(sample_resolved, config, tmp_work_dir)
        kinds = [a["kind"] for a in artifact.action_log]
        spacing_indices = [i for i, k in enumerate(kinds) if k == "spacing"]
        font_indices = [i for i, k in enumerate(kinds) if k == "font"]
        if spacing_indices and font_indices:
            assert max(spacing_indices) < min(font_indices)

    def test_font_actions_precede_prune_actions(self, mock_renderer, tmp_work_dir):
        """All FontActions must appear before any PruneAction."""
        exp1 = ExperienceItem(id="a", role="R", company="C", date="2024", bullets=["b"], priority=0.9)
        exp2 = ExperienceItem(id="b", role="R", company="C", date="2024", bullets=["b"], priority=0.1)
        content = ResolvedContent(experiences=[exp1, exp2])
        side_effects = [(b"%PDF", 2)] * 20 + [(b"%PDF", 1)]
        mock_renderer.render.side_effect = side_effects
        config = TailoredConfig(max_pages=1, min_font_size_pt=8.5)
        artifact = HeuristicLoop(renderer=mock_renderer).run(content, config, tmp_work_dir)
        kinds = [a["kind"] for a in artifact.action_log]
        font_indices = [i for i, k in enumerate(kinds) if k == "font"]
        prune_indices = [i for i, k in enumerate(kinds) if k == "prune"]
        if font_indices and prune_indices:
            assert max(font_indices) < min(prune_indices)


# ── Test 3 ────────────────────────────────────────────────────────────────────


class TestPruning:
    def test_lowest_priority_pruned_first_alpha_zero(self, tmp_work_dir):
        """With alpha=0.0 and no match_scores, the experience with lowest priority is pruned."""
        exp_hi = ExperienceItem(id="hi", role="R", company="C", date="2024", bullets=["b"], priority=0.9)
        exp_lo = ExperienceItem(id="lo", role="R", company="C", date="2024", bullets=["b"], priority=0.1)
        content = ResolvedContent(experiences=[exp_hi, exp_lo])
        renderer = MagicMock(spec=RendererPort)

        def side_effect(c, layout, tmp):
            if any(e.id == "lo" for e in c.experiences):
                return (b"%PDF", 2)
            return (b"%PDF", 1)

        renderer.render.side_effect = side_effect
        config = TailoredConfig(max_pages=1, alpha=0.0)
        artifact = HeuristicLoop(renderer=renderer).run(content, config, tmp_work_dir)
        prune_actions = [a for a in artifact.action_log if a["kind"] == "prune"]
        assert len(prune_actions) >= 1
        assert prune_actions[0]["pruned_experience_id"] == "lo"


# ── Test 4 ────────────────────────────────────────────────────────────────────


class TestStallDetection:
    def test_stall_fast_forwards_to_font_step(self, mock_renderer, sample_resolved, tmp_work_dir):
        """If spacing does not improve page count for STALL_DETECTION_WINDOW iterations, a NoOpAction is emitted."""
        # 1 initial + 2 spacing (stall) + 2 font (probe+mid) = 5
        calls = [(b"%PDF", 2)] * 4 + [(b"%PDF", 1)]
        mock_renderer.render.side_effect = calls
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=mock_renderer).run(sample_resolved, config, tmp_work_dir)
        noop_actions = [a for a in artifact.action_log if a["kind"] == "noop"]
        assert len(noop_actions) >= 1
        assert "stall" in noop_actions[0]["reason"]


# ── Test 5 ────────────────────────────────────────────────────────────────────


class TestStepDWarning:
    def test_oversized_warning_when_one_item_remains(self, tmp_work_dir):
        """When only 1 experience remains and still overflows, a warning is emitted and no exception raised."""
        exp = ExperienceItem(id="only", role="R", company="C", date="2024", bullets=["b"], priority=1.0)
        content = ResolvedContent(experiences=[exp])
        renderer = MagicMock(spec=RendererPort)
        renderer.render.return_value = (b"%PDF", 3)
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=renderer).run(content, config, tmp_work_dir)
        assert any("Cannot fit" in w for w in artifact.warnings)
        assert artifact.final_page_count == 3


# ── Test 6 ────────────────────────────────────────────────────────────────────


class TestActionLogReproducibility:
    def test_reduce_reproduces_final_layout(self, mock_renderer, tmp_work_dir):
        """reduce(apply_action, initial_state, action_log) must reproduce final_layout."""
        exp = ExperienceItem(id="x", role="R", company="C", date="2024", bullets=["b"], priority=0.5)
        content = ResolvedContent(experiences=[exp])
        renderer = MagicMock(spec=RendererPort)
        renderer.render.side_effect = [(b"%PDF", 2), (b"%PDF", 2), (b"%PDF", 1)]
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=renderer).run(content, config, tmp_work_dir)

        KIND_MAP = {
            "spacing": SpacingAction,
            "font": FontAction,
            "prune": PruneAction,
            "noop": NoOpAction,
            "prune_section": PruneSectionAction,
            "prune_bullet": PruneBulletAction,
        }
        actions = [
            KIND_MAP[d["kind"]](**{k: v for k, v in d.items() if k != "kind"})
            for d in artifact.action_log
        ]
        initial_layout = LayoutParams()
        final_layout = functools.reduce(
            lambda layout, act: GenerationState(
                layout=layout, content=content, page_count=0,
            )._apply_layout(act),
            actions,
            initial_layout,
        )
        assert final_layout == artifact.final_layout


# ── Test 7 ────────────────────────────────────────────────────────────────────


class TestMonotoneGuardFallback:
    def test_non_monotone_emits_warning_and_continues(self, tmp_work_dir):
        """If probe_pages < mid_pages (non-monotone), a warning is emitted and loop continues without raising."""
        exp = ExperienceItem(id="x", role="R", company="C", date="2024", bullets=["b"], priority=0.5)
        content = ResolvedContent(experiences=[exp])
        renderer = MagicMock(spec=RendererPort)
        call_count = {"n": 0}

        def side_effect(c, layout, tmp):
            call_count["n"] += 1
            n = call_count["n"]
            if n <= 3:
                return (b"%PDF", 2)    # initial + 2 spacing (stall)
            if n == 4:
                return (b"%PDF", 1)    # probe in binary search (fewer pages)
            if n == 5:
                return (b"%PDF", 2)    # mid in binary search (non-monotone!)
            return (b"%PDF", 1)        # unconditional render / linear fallback

        renderer.render.side_effect = side_effect
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=renderer).run(content, config, tmp_work_dir)
        assert any("Monotone" in w or "monotone" in w for w in artifact.warnings)


# ── Test 8 ────────────────────────────────────────────────────────────────────


class TestSectionPruning:
    def test_section_pruned_before_experience_items(self, tmp_work_dir):
        """Skills/projects sections are pruned before individual experience items are dropped."""
        exp = ExperienceItem(id="e1", role="R", company="C", date="2024", bullets=["b"], priority=0.9)
        proj = ProjectItem(name="P", date="2024", bullets=["built x"])
        content = ResolvedContent(experiences=[exp], projects=[proj])
        renderer = MagicMock(spec=RendererPort)

        def side_effect(c, layout, tmp):
            if not c.projects:
                return (b"%PDF", 1)
            return (b"%PDF", 2)

        renderer.render.side_effect = side_effect
        config = TailoredConfig(max_pages=1)
        artifact = HeuristicLoop(renderer=renderer).run(content, config, tmp_work_dir)
        kinds = [a["kind"] for a in artifact.action_log]
        assert "prune_section" in kinds
        assert "prune" not in kinds
