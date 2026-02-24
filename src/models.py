"""has pydantic model definitions for the cv typist system"""

from pydantic import BaseModel

class ExperienceItem(BaseModel):
    id: str
    role: str
    company: str
    date: str
    bullets: list[str]
    keywords: list[str]
    priority: float

class MasterExperience(BaseModel):
    experiences: list[ExperienceItem]

class LayoutParams(BaseModel):
    margin: float
    gutter: float
    font_size: float
    item_spacing: float

class TailoredConfig(BaseModel):
    max_pages: int
    min_font_size: float
    allow_rephrasing: bool
    output_format: str

class GenerationState(BaseModel):
    layout_params: LayoutParams
    current_page_count: int
