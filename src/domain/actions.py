"""Immutable action types emitted by the HeuristicLoop.

Dependency rule: stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


@dataclass(frozen=True)
class SpacingAction:
    kind: Literal["spacing"] = "spacing"
    delta_margin_pt: float = 0.0
    delta_gutter_pt: float = 0.0


@dataclass(frozen=True)
class FontAction:
    kind: Literal["font"] = "font"
    new_font_size_pt: float = 0.0


@dataclass(frozen=True)
class PruneAction:
    kind: Literal["prune"] = "prune"
    pruned_experience_id: str = ""
    pruning_score: float = 0.0


@dataclass(frozen=True)
class NoOpAction:
    """Emitted when a step has no further moves available."""
    kind: Literal["noop"] = "noop"
    reason: str = ""


@dataclass(frozen=True)
class PruneSectionAction:
    """Prune an entire named template section (experiences, projects, education, skills)."""
    kind: Literal["prune_section"] = "prune_section"
    section: str = ""
    pruning_score: float = 0.0


@dataclass(frozen=True)
class PruneBulletAction:
    """Prune a single bullet from an ExperienceItem."""
    kind: Literal["prune_bullet"] = "prune_bullet"
    experience_id: str = ""
    bullet_index: int = 0
    reason: str = ""


Action = Union[
    SpacingAction, FontAction, PruneAction, NoOpAction,
    PruneSectionAction, PruneBulletAction,
]
