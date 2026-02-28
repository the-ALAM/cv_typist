"""Domain models — pure Pydantic schemas.

Dependency rule: stdlib + pydantic only. No imports from acte.*.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    id: str
    role: str
    company: str
    date: str
    bullets: list[str]
    keywords: list[str]
    priority: float  # 0.0 – 1.0; higher = keep under pressure


class MasterExperience(BaseModel):
    experiences: list[ExperienceItem]


class LayoutParams(BaseModel):
    margin: float = 72.0       # points
    gutter: float = 6.0        # points
    font_size: float = 11.0    # points
    item_spacing: float = 4.0  # points


class TailoredConfig(BaseModel):
    max_pages: int = 1
    min_font_size: float = 9.0
    allow_rephrasing: bool = False
    output_format: str = "pdf"  # "pdf" | "png"


class ResolvedContent(BaseModel):
    """Boundary object between the AI layer (infra) and the layout layer (application).

    HeuristicLoop consumes ResolvedContent. SelectionAgent produces it.
    Nothing in domain/ creates ResolvedContent — callers assemble it.
    """

    experiences: list[ExperienceItem]
    job_description: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
