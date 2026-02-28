"""Domain models — pure Pydantic schemas.

Dependency rule: stdlib + pydantic only. No imports from acte.*.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ExperienceItem(BaseModel):
    id: str
    role: str
    company: str
    date: str
    bullets: list[str]
    keywords: list[str] = Field(default_factory=list)
    priority: float = Field(ge=0.0, le=1.0)
    match_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class PersonalInfo(BaseModel):
    name: str
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class ProjectItem(BaseModel):
    name: str
    date: str
    bullets: list[str]
    tech_used: Optional[str] = None
    url: Optional[str] = None


class EducationItem(BaseModel):
    institution: str
    location: str
    degree: str
    date: str


class MasterExperience(BaseModel):
    experiences: list[ExperienceItem]
    personal: Optional[PersonalInfo] = None
    skills: Optional[dict[str, list[str]]] = None
    projects: Optional[list[ProjectItem]] = None
    education: Optional[list[EducationItem]] = None

    @model_validator(mode="after")
    def unique_ids(self) -> MasterExperience:
        ids = [e.id for e in self.experiences]
        if len(ids) != len(set(ids)):
            raise ValueError("ExperienceItem IDs must be unique")
        return self


class LayoutParams(BaseModel):
    margin_pt: float = Field(default=56.0, ge=20.0, le=80.0)
    gutter_pt: float = Field(default=6.0, ge=2.0, le=16.0)
    font_size_pt: float = Field(default=10.5, ge=7.0, le=14.0)
    item_spacing_pt: float = Field(default=4.0, ge=1.0, le=10.0)


class TailoredConfig(BaseModel):
    max_pages: int = Field(default=1, ge=1, le=4)
    min_font_size_pt: float = Field(default=8.5, ge=7.0, le=10.0)
    allow_rephrasing: bool = False
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    output_format: str = "pdf"


class ResolvedContent(BaseModel):
    """Boundary object between the AI layer (infra) and the layout layer (application).

    HeuristicLoop consumes ResolvedContent. SelectionAgent produces it.
    Nothing in domain/ creates ResolvedContent — callers assemble it.
    """

    experiences: list[ExperienceItem]
    personal: Optional[PersonalInfo] = None
    skills: Optional[dict[str, list[str]]] = None
    projects: Optional[list[ProjectItem]] = None
    education: Optional[list[EducationItem]] = None
    job_description: Optional[str] = None
    metadata: dict[str, str] = Field(default_factory=dict)


class GenerationArtifact(BaseModel):
    pdf_bytes: bytes
    final_page_count: int
    final_layout: LayoutParams
    action_log: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
