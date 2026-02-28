"""Tests for GroundingGuard — requires LLM mock or live key.

Mark: @pytest.mark.integration for live LLM calls.
"""

from __future__ import annotations

import pytest

from src.infra.grounding import GroundingGuard


class TestGroundingGuardInterface:
    def test_instantiates(self, mock_llm) -> None:
        guard = GroundingGuard(llm=mock_llm)
        assert guard is not None

    def test_verify_raises_not_implemented(self, mock_llm, sample_resolved, sample_master) -> None:
        guard = GroundingGuard(llm=mock_llm)
        with pytest.raises(NotImplementedError):
            guard.verify(sample_resolved, sample_master)
