"""Loader — reads YAML/JSON master experience and config files from disk.

Responsibilities absorbed from: src/loader.py, src/parser.py

Dependency rule: domain/ + pyyaml + stdlib.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from ..domain.exceptions import ConfigError
from ..domain.models import MasterExperience, TailoredConfig


def load_master(path: Path) -> MasterExperience:
    """Parse a YAML or JSON file into a validated MasterExperience.

    Raises:
        ConfigError: if the file cannot be parsed or fails schema validation.
    """
    try:
        data = _read_file(path)
        return MasterExperience.model_validate(data)
    except Exception as exc:
        raise ConfigError(f"Failed to load master experience from {path}: {exc}") from exc


def load_config(path: Path) -> TailoredConfig:
    """Parse a YAML or JSON file into a validated TailoredConfig.

    Raises:
        ConfigError: if the file cannot be parsed or fails schema validation.
    """
    try:
        data = _read_file(path)
        return TailoredConfig.model_validate(data)
    except Exception as exc:
        raise ConfigError(f"Failed to load config from {path}: {exc}") from exc


def _read_file(path: Path) -> dict:
    """Read YAML or JSON file; return parsed dict."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    raise ConfigError(f"Unsupported file format: {suffix!r} (expected .yaml or .json)")
