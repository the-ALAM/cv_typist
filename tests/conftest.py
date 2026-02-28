"""Shared fixtures and mock factories for all ACTE tests.

Fast fixtures (domain/) have zero I/O.
Integration fixtures (infra/) are lazily imported so domain tests run
without Typst or an LLM configured.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.domain.models import (
    ExperienceItem,
    LayoutParams,
    MasterExperience,
    ResolvedContent,
    TailoredConfig,
)
from src.application.ports import CachePort, LLMClientPort, RendererPort


# ── Domain fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_experience() -> ExperienceItem:
    return ExperienceItem(
        id="exp-001",
        role="Software Engineer",
        company="Acme Corp",
        date="2022-01 – 2024-01",
        bullets=["Built scalable APIs in Python", "Led a team of 3 engineers"],
        keywords=["Python", "FastAPI", "PostgreSQL"],
        priority=0.9,
    )


@pytest.fixture
def low_priority_experience() -> ExperienceItem:
    return ExperienceItem(
        id="exp-002",
        role="Intern",
        company="Small Co",
        date="2021-06 – 2021-12",
        bullets=["Wrote unit tests"],
        keywords=["Python"],
        priority=0.2,
    )


@pytest.fixture
def sample_master(sample_experience: ExperienceItem) -> MasterExperience:
    return MasterExperience(experiences=[sample_experience])


@pytest.fixture
def default_layout() -> LayoutParams:
    return LayoutParams()


@pytest.fixture
def default_config() -> TailoredConfig:
    return TailoredConfig()


@pytest.fixture
def sample_resolved(sample_experience: ExperienceItem) -> ResolvedContent:
    return ResolvedContent(
        experiences=[sample_experience],
        job_description="Senior Python engineer role at a fintech startup",
    )


# ── Mock port fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def mock_renderer() -> RendererPort:
    """RendererPort mock that returns a 1-page PDF stub."""
    renderer = MagicMock(spec=RendererPort)
    renderer.render.return_value = (b"%PDF-1.4 mock", 1)
    return renderer


@pytest.fixture
def mock_renderer_2pages() -> RendererPort:
    """RendererPort mock that always returns 2 pages (forces loop adjustments)."""
    renderer = MagicMock(spec=RendererPort)
    renderer.render.return_value = (b"%PDF-1.4 mock 2p", 2)
    return renderer


@pytest.fixture
def mock_llm() -> LLMClientPort:
    llm = MagicMock(spec=LLMClientPort)
    llm.complete.return_value = '{"ranked_ids": ["exp-001"], "rewrites": {}}'
    return llm


@pytest.fixture
def mock_cache() -> CachePort:
    return MagicMock(spec=CachePort)


# ── Filesystem fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def tmp_work_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tmp_cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "cache"
    d.mkdir()
    return d
