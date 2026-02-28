"""LiteLLM wrapper — single seam for all LLM calls.

Both SelectionAgent and GroundingGuard import from here.
Nothing in the codebase imports litellm directly except this file.

Swapping LLM provider, adding logging, rate limiting, or mocking in tests
requires touching only this file.

Dependency rule: domain/ + application/ports + litellm.
"""

from __future__ import annotations

import logging

from ..application.ports import LLMClientPort
from ..domain.exceptions import SelectionError

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """LLMClientPort implementation backed by LiteLLM.

    Example::

        llm = LiteLLMClient(model="gpt-4o-mini")
        response = llm.complete(system="You are...", user="Rank these...")
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self._model = model

    def complete(self, system: str, user: str) -> str:
        """Send a chat-completion request. Returns raw assistant message text.

        Raises:
            SelectionError: on LLM API failure or empty/malformed response.
        """
        raise NotImplementedError
