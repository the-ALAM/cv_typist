"""Tests for ContentCache — file I/O, no LLM or Typst required."""

from __future__ import annotations

import pytest

from src.infra.cache import ContentCache
from src.domain.models import ResolvedContent


class TestContentCacheInterface:
    def test_instantiates_and_creates_dir(self, tmp_cache_dir) -> None:
        cache = ContentCache(cache_dir=tmp_cache_dir)
        assert tmp_cache_dir.exists()

    def test_get_raises_not_implemented(self, tmp_cache_dir) -> None:
        cache = ContentCache(cache_dir=tmp_cache_dir)
        with pytest.raises(NotImplementedError):
            cache.get("some-key")

    def test_set_raises_not_implemented(self, tmp_cache_dir, sample_resolved) -> None:
        cache = ContentCache(cache_dir=tmp_cache_dir)
        with pytest.raises(NotImplementedError):
            cache.set("some-key", sample_resolved)

    def test_path_helper_is_deterministic(self, tmp_cache_dir) -> None:
        cache = ContentCache(cache_dir=tmp_cache_dir)
        assert cache._path("abc123").name == "abc123.json"
