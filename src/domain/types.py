"""Shared type aliases for the ACTE domain.

Dependency rule: stdlib only.
"""

from __future__ import annotations

from typing import NewType

# Opaque identifiers
JobId = NewType("JobId", str)
CacheKey = NewType("CacheKey", str)
ExperienceId = NewType("ExperienceId", str)

# Scalar aliases — use these instead of bare float/str to make signatures readable
MatchScore = float   # 0.0 – 1.0
PageCount = int
FontSize = float     # points

# Discriminated string literal for heuristic loop actions
Action = str  # "reduce_spacing" | "reduce_font" | "prune_item" | "done"

ACTIONS: tuple[Action, ...] = ("reduce_spacing", "reduce_font", "prune_item", "done")
