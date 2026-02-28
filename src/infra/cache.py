"""ContentCache — file-based CachePort implementation.

Persists ResolvedContent to disk keyed by a SHA-256 hash of (master, jd).
Cache hits skip Phase 3 (AI selection) entirely and go straight to the loop.

Dependency rule: domain/ + application/ports + stdlib (json, pathlib).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..application.ports import CachePort
from ..domain.exceptions import CacheError
from ..domain.models import ResolvedContent

logger = logging.getLogger(__name__)


class ContentCache:
    """File-based CachePort. Each entry is a JSON file named <key>.json.

    Example::

        cache = ContentCache(cache_dir=Path("output/cache"))
        hit = cache.get(key)
        if hit is None:
            cache.set(key, resolved_content)
    """

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> ResolvedContent | None:
        """Return cached ResolvedContent, or None on miss.

        Raises:
            CacheError: if the cache file exists but is corrupted.
        """
        raise NotImplementedError

    def set(self, key: str, value: ResolvedContent) -> None:
        """Write ResolvedContent to disk under <key>.json.

        Raises:
            CacheError: on write failure.
        """
        raise NotImplementedError

    def _path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"
