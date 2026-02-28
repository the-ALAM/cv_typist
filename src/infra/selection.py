"""SelectionAgent — ranks and optionally rephrases experience items.

Input:  MasterExperience + JobDescription text
Output: ResolvedContent (filtered, ranked, bullets optionally rewritten)

MUST NOT be imported by HeuristicLoop or anything in application/.
All LLM calls go through llm.py, never directly to litellm.

Dependency rule: domain/ + application/ports + infra/llm.
"""

from __future__ import annotations

import logging

from ..application.ports import LLMClientPort
from ..domain.exceptions import SelectionError
from ..domain.models import MasterExperience, ResolvedContent, TailoredConfig

logger = logging.getLogger(__name__)


class SelectionAgent:
    """Ranks MasterExperience items against a JD and produces ResolvedContent.

    If config.allow_rephrasing is True, bullet points are rewritten to
    highlight JD keywords — but GroundingGuard must verify the result before
    it is returned.

    Example::

        agent = SelectionAgent(llm=llm_client)
        resolved = agent.select(master, jd_text, config)
    """

    def __init__(self, llm: LLMClientPort) -> None:
        self._llm = llm

    def select(
        self,
        master: MasterExperience,
        job_description: str,
        config: TailoredConfig,
    ) -> ResolvedContent:
        """Return ranked/rephrased content ready for the HeuristicLoop.

        Raises:
            SelectionError: if the LLM fails or returns unparseable JSON.
        """
        raise NotImplementedError
