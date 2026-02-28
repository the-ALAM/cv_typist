"""Abstract port interfaces — the architecture enforcer.

`application/` depends on these Protocols, never on concrete infra/ classes.
This means:
  - HeuristicLoop is testable with a 3-line mock renderer
  - Swapping LLM providers requires touching only infra/llm.py
  - Type checkers enforce the boundary at import time

Dependency rule: stdlib + domain/models only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..domain.models import LayoutParams, ResolvedContent


@runtime_checkable
class RendererPort(Protocol):
    """Renders ResolvedContent + LayoutParams to a compiled document."""

    def render(
        self,
        content: ResolvedContent,
        layout: LayoutParams,
        tmp_dir: Path,
    ) -> tuple[bytes, int]:
        """Return (document_bytes, page_count).

        Raises:
            RenderError: if Jinja2 or Typst compilation fails.
        """
        ...


@runtime_checkable
class LLMClientPort(Protocol):
    """Single seam for all LLM calls."""

    def complete(self, system: str, user: str) -> str:
        """Send a chat-completion request. Returns the raw assistant message.

        Raises:
            SelectionError: on LLM API failure or malformed response.
        """
        ...


@runtime_checkable
class CachePort(Protocol):
    """Key/value store for ResolvedContent, keyed by (master, jd) hash."""

    def get(self, key: str) -> ResolvedContent | None:
        """Return cached content, or None on cache miss."""
        ...

    def set(self, key: str, value: ResolvedContent) -> None:
        """Persist content under key.

        Raises:
            CacheError: on write failure.
        """
        ...
