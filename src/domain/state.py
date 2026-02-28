"""Immutable generation state tracked across heuristic loop iterations.

Dependency rule: stdlib + domain/models only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .models import LayoutParams


@dataclass(frozen=True)
class GenerationState:
    """Snapshot of layout params and page count at a single loop iteration.
    By using immutable dataclass and copy-on-write methods we enforce immutability as structural, not just a convention.

    Use `with_layout` and `with_page_count` to produce updated copies.
    The original instance is never mutated.
    """

    layout_params: LayoutParams
    current_page_count: int
    iteration: int = 0

    def with_layout(self, layout_params: LayoutParams) -> GenerationState:
        """Return a new state with updated layout, incrementing iteration."""
        return replace(self, layout_params=layout_params, iteration=self.iteration + 1)

    def with_page_count(self, page_count: int) -> GenerationState:
        """Return a new state with updated page count."""
        return replace(self, current_page_count=page_count)
