"""Immutable generation state tracked across heuristic loop iterations.

Dependency rule: stdlib + domain/models + domain/actions only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .actions import Action, FontAction, SpacingAction
from .models import LayoutParams, ResolvedContent


@dataclass(frozen=True)
class GenerationState:
    """Snapshot of layout params, content, and audit log at a single loop iteration.

    Immutable — use `apply_action` and `add_warning` to produce updated copies.
    """

    layout: LayoutParams
    content: ResolvedContent
    page_count: int
    actions: tuple[Action, ...] = ()
    warnings: tuple[str, ...] = ()

    def apply_action(
        self,
        action: Action,
        new_page_count: int,
        new_content: ResolvedContent | None = None,
    ) -> GenerationState:
        """Returns a NEW GenerationState. Never mutates self."""
        return replace(
            self,
            layout=self._apply_layout(action),
            content=new_content if new_content is not None else self.content,
            page_count=new_page_count,
            actions=self.actions + (action,),
        )

    def add_warning(self, msg: str) -> GenerationState:
        return replace(self, warnings=self.warnings + (msg,))

    def _apply_layout(self, action: Action) -> LayoutParams:
        """Returns updated LayoutParams based on action type."""
        if isinstance(action, SpacingAction):
            return LayoutParams(
                margin_pt=max(20.0, self.layout.margin_pt + action.delta_margin_pt),
                gutter_pt=max(2.0, self.layout.gutter_pt + action.delta_gutter_pt),
                font_size_pt=self.layout.font_size_pt,
                item_spacing_pt=self.layout.item_spacing_pt,
            )
        if isinstance(action, FontAction):
            return LayoutParams(
                margin_pt=self.layout.margin_pt,
                gutter_pt=self.layout.gutter_pt,
                font_size_pt=action.new_font_size_pt,
                item_spacing_pt=self.layout.item_spacing_pt,
            )
        return self.layout

    def pruning_score(self, exp_id: str, alpha: float) -> float:
        """pruning_score = alpha * match_score + (1 - alpha) * priority.

        If match_score is None, alpha is forced to 0.0.
        Lower score = pruned first.
        """
        for exp in self.content.experiences:
            if exp.id == exp_id:
                if exp.match_score is None:
                    return exp.priority
                return alpha * exp.match_score + (1 - alpha) * exp.priority
        return 0.0
