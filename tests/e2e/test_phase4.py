"""Phase 4 gate: API & Persistence.

Pass criteria:
  1. FastAPI app starts and all routes respond.
  2. ContentCache hit skips SelectionAgent (LLM not called).
  3. Output artifacts saved to output/ with correct filenames.
  4. /status/{job_id} returns correct states: pending → running → done.
  5. Cache is invalidated when master or JD changes.

Run: uv run pytest tests/e2e/test_phase4.py -v
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestPhase4API:
    def test_api_app_importable(self) -> None:
        from src.entrypoints.api import app
        assert app is not None

    def test_api_has_generate_route(self) -> None:
        from src.entrypoints.api import app
        routes = {r.path for r in app.routes}  # type: ignore[attr-defined]
        assert "/generate" in routes

    def test_api_has_status_route(self) -> None:
        from src.entrypoints.api import app
        routes = {r.path for r in app.routes}  # type: ignore[attr-defined]
        assert "/status/{job_id}" in routes

    def test_cache_hit_skips_llm(self, mock_llm, mock_renderer, mock_cache, sample_master, default_config, tmp_work_dir) -> None:
        pytest.skip("Implement in Phase 4: Pipeline caching path")

    def test_cache_miss_calls_llm(self, mock_llm, mock_renderer, mock_cache, sample_master, default_config, tmp_work_dir) -> None:
        pytest.skip("Implement in Phase 4: Pipeline cache miss path")
