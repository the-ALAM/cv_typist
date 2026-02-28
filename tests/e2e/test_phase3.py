"""Phase 3 gate: AI Integration (SelectionAgent + GroundingGuard).

Pass criteria:
  1. SelectionAgent ranks ExperienceItems by JD relevance.
  2. Rephrased bullets pass GroundingGuard (no hallucinations).
  3. GroundingGuard raises GroundingError for invented roles/tech.
  4. Pipeline with allow_rephrasing=True produces ResolvedContent.
  5. Pipeline with allow_rephrasing=False skips LLM rephrasing call.

Run: uv run pytest tests/e2e/test_phase3.py -v
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestPhase3AIIntegration:
    def test_selection_agent_importable(self) -> None:
        from src.infra.selection import SelectionAgent
        assert SelectionAgent is not None

    def test_grounding_guard_importable(self) -> None:
        from src.infra.grounding import GroundingGuard
        assert GroundingGuard is not None

    def test_selection_agent_ranks_experiences(self, mock_llm, sample_master, default_config) -> None:
        pytest.skip("Implement in Phase 3: SelectionAgent.select()")

    def test_grounding_guard_rejects_hallucination(self, mock_llm, sample_master) -> None:
        pytest.skip("Implement in Phase 3: GroundingGuard.verify()")

    @pytest.mark.integration
    def test_full_phase3_pipeline_with_mock_llm(self, mock_llm, mock_renderer, mock_cache, sample_master, tmp_work_dir) -> None:
        pytest.skip("Implement in Phase 3: Pipeline.run() with AI path")
