"""Tests for SelectionAgent — requires LLM mock or live key.

Mark: @pytest.mark.integration for live LLM calls.
"""

from __future__ import annotations

import pytest

from src.infra.selection import SelectionAgent
from src.domain.models import TailoredConfig


class TestSelectionAgentInterface:
    def test_instantiates(self, mock_llm) -> None:
        agent = SelectionAgent(llm=mock_llm)
        assert agent is not None

    def test_select_raises_not_implemented(self, mock_llm, sample_master, default_config) -> None:
        agent = SelectionAgent(llm=mock_llm)
        with pytest.raises(NotImplementedError):
            agent.select(sample_master, "Python engineer", default_config)
