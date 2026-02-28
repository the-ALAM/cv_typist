"""Pure unit tests for domain models, state, actions, types, and exceptions.

Zero I/O. Zero mocks. Runs in milliseconds with no external deps installed.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain.actions import (
    Action,
    FontAction,
    NoOpAction,
    PruneAction,
    SpacingAction,
)
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
    GenerationArtifact,
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

    def test_priority_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ExperienceItem(
                id="e1", role="SWE", company="C", date="2024",
                bullets=["x"], keywords=[], priority=1.5,
            )

    def test_match_score_optional(self) -> None:
        item = ExperienceItem(
            id="e1", role="SWE", company="C", date="2024",
            bullets=["x"], keywords=[], priority=0.5,
        )
        assert item.match_score is None

    def test_keywords_default_empty(self) -> None:
        item = ExperienceItem(
            id="e1", role="SWE", company="C", date="2024",
            bullets=["x"], priority=0.5,
        )
        assert item.keywords == []


class TestMasterExperience:
    def test_wraps_list(self, sample_master: MasterExperience) -> None:
        assert len(sample_master.experiences) == 1

    def test_empty_is_valid(self) -> None:
        m = MasterExperience(experiences=[])
        assert m.experiences == []

    def test_unique_ids_enforced(self) -> None:
        item = ExperienceItem(
            id="e1", role="SWE", company="C", date="2024",
            bullets=["x"], keywords=[], priority=0.5,
        )
        with pytest.raises(ValidationError, match="unique"):
            MasterExperience(experiences=[item, item])


class TestLayoutParams:
    def test_defaults_are_positive(self) -> None:
        layout = LayoutParams()
        assert layout.margin_pt > 0
        assert layout.gutter_pt > 0
        assert layout.font_size_pt > 0
        assert layout.item_spacing_pt > 0

    def test_custom_values(self) -> None:
        layout = LayoutParams(margin_pt=50.0, font_size_pt=10.0)
        assert layout.margin_pt == 50.0
        assert layout.font_size_pt == 10.0

    def test_constraint_bounds(self) -> None:
        with pytest.raises(ValidationError):
            LayoutParams(margin_pt=10.0)  # below ge=20.0


class TestTailoredConfig:
    def test_defaults(self) -> None:
        config = TailoredConfig()
        assert config.max_pages >= 1
        assert config.min_font_size_pt > 0

    def test_allow_rephrasing_default_false(self) -> None:
        assert TailoredConfig().allow_rephrasing is False

    def test_alpha_default(self) -> None:
        assert TailoredConfig().alpha == 0.5


class TestResolvedContent:
    def test_is_boundary_object(self, sample_experience: ExperienceItem) -> None:
        rc = ResolvedContent(experiences=[sample_experience])
        assert len(rc.experiences) == 1
        assert rc.job_description is None

    def test_metadata_defaults_empty(self, sample_experience: ExperienceItem) -> None:
        rc = ResolvedContent(experiences=[sample_experience])
        assert rc.metadata == {}

    def test_round_trip_json(self, sample_resolved: ResolvedContent) -> None:
        restored = ResolvedContent.model_validate_json(sample_resolved.model_dump_json())
        assert restored == sample_resolved


class TestGenerationArtifact:
    def test_construction(self) -> None:
        artifact = GenerationArtifact(
            pdf_bytes=b"%PDF",
            final_page_count=1,
            final_layout=LayoutParams(),
        )
        assert artifact.final_page_count == 1
        assert artifact.action_log == []
        assert artifact.warnings == []


class TestGenerationState:
    def _make_state(self, page_count: int = 2) -> GenerationState:
        from tests.conftest import sample_experience
        content = ResolvedContent(
            experiences=[ExperienceItem(
                id="e1", role="SWE", company="Corp", date="2024",
                bullets=["Did stuff"], keywords=["Python"], priority=0.8,
            )]
        )
        return GenerationState(
            layout=LayoutParams(), content=content, page_count=page_count,
        )

    def test_is_immutable(self) -> None:
        state = self._make_state()
        with pytest.raises(Exception):
            state.page_count = 1  # type: ignore[misc]

    def test_apply_action_returns_new(self) -> None:
        state = self._make_state(page_count=2)
        action = SpacingAction(delta_margin_pt=-4.0, delta_gutter_pt=-1.0)
        new = state.apply_action(action, new_page_count=1)
        assert new.page_count == 1
        assert state.page_count == 2
        assert len(new.actions) == 1

    def test_add_warning(self) -> None:
        state = self._make_state()
        new = state.add_warning("oops")
        assert "oops" in new.warnings
        assert len(state.warnings) == 0

    def test_pruning_score_no_match_score(self) -> None:
        state = self._make_state()
        score = state.pruning_score("e1", alpha=0.5)
        assert score == 0.8  # falls back to priority when match_score is None


class TestActions:
    def test_spacing_action_frozen(self) -> None:
        a = SpacingAction(delta_margin_pt=-4.0)
        with pytest.raises(Exception):
            a.delta_margin_pt = 0  # type: ignore[misc]

    def test_action_union(self) -> None:
        actions: list[Action] = [
            SpacingAction(), FontAction(), PruneAction(), NoOpAction()
        ]
        assert len(actions) == 4


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
