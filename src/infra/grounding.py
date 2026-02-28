"""GroundingGuard — verifies that AI-rewritten bullets don't hallucinate.

Compares ResolvedContent bullets against the source MasterExperience.
Flags any bullet that introduces roles, companies, dates, or tech stack
items not present in the original.

MUST NOT be imported by HeuristicLoop or anything in application/.
All LLM calls go through llm.py.

Dependency rule: domain/ + application/ports + infra/llm.
"""

from __future__ import annotations

import logging

from ..application.ports import LLMClientPort
from ..domain.exceptions import GroundingError
from ..domain.models import MasterExperience, ResolvedContent

logger = logging.getLogger(__name__)


class GroundingGuard:
    """Checks that ResolvedContent bullets are grounded in MasterExperience.

    Performs a diff-check on major entities: dates, titles, companies, and
    tech-stack keywords. Raises GroundingError on the first violation found.

    Example::

        guard = GroundingGuard(llm=llm_client)
        guard.verify(resolved, source_master)  # raises GroundingError or returns None
    """

    def __init__(self, llm: LLMClientPort) -> None:
        self._llm = llm

    def verify(self, resolved: ResolvedContent, source: MasterExperience) -> None:
        """Raise GroundingError if any bullet cannot be traced to source data.

        Raises:
            GroundingError: with details of the offending bullet and item id.
        """
        raise NotImplementedError
