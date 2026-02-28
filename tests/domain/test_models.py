"""Pure unit tests for domain models, state, types, and exceptions.

Zero I/O. Zero mocks. Runs in milliseconds with no external deps installed.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.exceptions import (
    ACTEError,
    CacheError,
    ConfigError,
    GroundingError,
    LayoutError,
    RenderError,
    SelectionError,
    TemplateNotFoundError,
)
from src.domain.models import (
    ExperienceItem,
    LayoutParams,
    MasterExperience,
    ResolvedContent,
    TailoredConfig,
)
from src.domain.state import GenerationState
from src.domain.types import ACTIONS


class TestExperienceItem:
    def test_valid_construction(self) -> None:
        item = ExperienceItem(
            id="e1",
            role="SWE",
            company="Corp",
            date="2024",
            bullets=["Did stuff"],
            keywords=["Python"],
            priority=0.8,
        )
        assert item.id == "e1"
        assert item.priority == 0.8

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExperienceItem(id="e1", role="SWE")  # type: ignore[call-arg]

    def test_bullets_is_list(self, sample_experience: ExperienceItem) -> None:
        assert isinstance(sample_experience.bullets, list)
        assert all(isinstance(b, str) for b in sample_experience.bullets)


class TestMasterExperience:
    def test_wraps_list(self, sample_master: MasterExperience) -> None:
        assert len(sample_master.experiences) == 1

    def test_empty_is_valid(self) -> None:
        m = MasterExperience(experiences=[])
        assert m.experiences == []


class TestLayoutParams:
    def test_defaults_are_positive(self) -> None:
        layout = LayoutParams()
        assert layout.margin > 0
        assert layout.gutter > 0
        assert layout.font_size > 0
        assert layout.item_spacing > 0

    def test_custom_values(self) -> None:
        layout = LayoutParams(margin=50.0, font_size=10.0)
        assert layout.margin == 50.0
        assert layout.font_size == 10.0


class TestTailoredConfig:
    def test_defaults(self) -> None:
        config = TailoredConfig()
        assert config.max_pages >= 1
        assert config.min_font_size > 0
        assert config.output_format in ("pdf", "png")

    def test_allow_rephrasing_default_false(self) -> None:
        assert TailoredConfig().allow_rephrasing is False


class TestResolvedContent:
    def test_is_boundary_object(self, sample_experience: ExperienceItem) -> None:
        rc = ResolvedContent(experiences=[sample_experience])
        assert len(rc.experiences) == 1
        assert rc.job_description == ""

    def test_metadata_defaults_empty(self, sample_experience: ExperienceItem) -> None:
        rc = ResolvedContent(experiences=[sample_experience])
        assert rc.metadata == {}

    def test_round_trip_json(self, sample_resolved: ResolvedContent) -> None:
        restored = ResolvedContent.model_validate_json(sample_resolved.model_dump_json())
        assert restored == sample_resolved


class TestGenerationState:
    def test_is_immutable(self) -> None:
        state = GenerationState(layout_params=LayoutParams(), current_page_count=2)
        with pytest.raises(Exception):  # frozen dataclass
            state.current_page_count = 1  # type: ignore[misc]

    def test_with_page_count_returns_new(self) -> None:
        state = GenerationState(layout_params=LayoutParams(), current_page_count=2)
        new = state.with_page_count(1)
        assert new.current_page_count == 1
        assert state.current_page_count == 2  # original unchanged

    def test_with_layout_increments_iteration(self) -> None:
        state = GenerationState(layout_params=LayoutParams(), current_page_count=1, iteration=0)
        new = state.with_layout(LayoutParams(font_size=10.0))
        assert new.iteration == 1
        assert state.iteration == 0  # original unchanged

    def test_chaining_preserves_independence(self) -> None:
        s0 = GenerationState(layout_params=LayoutParams(), current_page_count=3)
        s1 = s0.with_page_count(2)
        s2 = s1.with_layout(LayoutParams(font_size=10.5))
        assert s0.current_page_count == 3
        assert s1.current_page_count == 2
        assert s2.layout_params.font_size == 10.5
        assert s2.iteration == 1


class TestExceptions:
    def test_all_inherit_from_acte_error(self) -> None:
        for exc_class in (
            LayoutError, RenderError, TemplateNotFoundError,
            SelectionError, GroundingError, CacheError, ConfigError,
        ):
            assert issubclass(exc_class, ACTEError), f"{exc_class} must inherit ACTEError"

    def test_template_not_found_is_render_error(self) -> None:
        assert issubclass(TemplateNotFoundError, RenderError)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(ACTEError):
            raise LayoutError("could not fit in 1 page")


class TestTypes:
    def test_actions_tuple_contains_expected(self) -> None:
        assert "reduce_spacing" in ACTIONS
        assert "reduce_font" in ACTIONS
        assert "prune_item" in ACTIONS
        assert "done" in ACTIONS
