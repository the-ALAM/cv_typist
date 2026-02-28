"""Tests for Pipeline — Phase 4 implementation target.

Uses mocked ports throughout. No LLM or Typst required.
"""

from __future__ import annotations

import pytest

from src.application.pipeline import Pipeline
from src.domain.models import MasterExperience, TailoredConfig


class TestPipelineInterface:
    def test_instantiates_with_ports(self, mock_llm, mock_renderer, mock_cache) -> None:
        pipeline = Pipeline(llm=mock_llm, renderer=mock_renderer, cache=mock_cache)
        assert pipeline is not None

    def test_run_raises_not_implemented(
        self, mock_llm, mock_renderer, mock_cache, sample_master, default_config, tmp_work_dir
    ) -> None:
        pipeline = Pipeline(llm=mock_llm, renderer=mock_renderer, cache=mock_cache)
        with pytest.raises(NotImplementedError):
            pipeline.run(sample_master, "Python engineer", default_config, tmp_work_dir)

    def test_cache_key_is_deterministic(self, sample_master: MasterExperience) -> None:
        jd = "Python engineer at a startup"
        key1 = Pipeline._cache_key(sample_master, jd)
        key2 = Pipeline._cache_key(sample_master, jd)
        assert key1 == key2

    def test_cache_key_differs_on_different_jd(self, sample_master: MasterExperience) -> None:
        key1 = Pipeline._cache_key(sample_master, "Python role")
        key2 = Pipeline._cache_key(sample_master, "Go role")
        assert key1 != key2
