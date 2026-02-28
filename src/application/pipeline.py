"""Pipeline — top-level coordinator for the full CV generation workflow.

Wires: SelectionAgent (infra) → HeuristicLoop (application) → artifact bytes.

Both cli.py and api.py call Pipeline.run(); no business logic lives in the
entrypoints.

Dependency rule: domain/ + application/ports only.
Concrete infra implementations are injected via constructor.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from ..domain.models import MasterExperience, ResolvedContent, TailoredConfig
from .loop import HeuristicLoop
from .ports import CachePort, LLMClientPort, RendererPort

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates: cache check → AI selection → heuristic layout → bytes.

    Construct once; call run() for each generation request.

    Example::

        pipeline = Pipeline(llm=llm_client, renderer=renderer, cache=cache)
        pdf_bytes = pipeline.run(master, jd_text, config, tmp_dir)
    """

    def __init__(
        self,
        llm: LLMClientPort,
        renderer: RendererPort,
        cache: CachePort,
    ) -> None:
        self._llm = llm
        self._renderer = renderer
        self._cache = cache
        self._loop = HeuristicLoop(renderer)

    def run(
        self,
        master: MasterExperience,
        job_description: str,
        config: TailoredConfig,
        tmp_dir: Path,
    ) -> bytes:
        """Run the full pipeline. Returns PDF/PNG bytes.

        Flow:
          1. Compute cache key from (master, job_description).
          2. Cache hit  → skip AI, go straight to HeuristicLoop.
          3. Cache miss → SelectionAgent, store result, then HeuristicLoop.
          4. Return compiled document bytes.

        Raises:
            SelectionError: AI selection fails.
            LayoutError: content cannot fit in max_pages after all adjustments.
            RenderError: Typst compilation fails.
        """
        raise NotImplementedError

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(master: MasterExperience, job_description: str) -> str:
        """Stable hash of (master JSON, job_description) as hex string."""
        payload = master.model_dump_json() + job_description
        return hashlib.sha256(payload.encode()).hexdigest()
