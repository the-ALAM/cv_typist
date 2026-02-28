"""All custom exceptions for ACTE.

Dependency rule: stdlib only. Import from nowhere in acte.*.

Usage:
    from src.domain.exceptions import LayoutError, RenderError
"""

from __future__ import annotations


class ACTEError(Exception):
    """Base exception. Catch this to handle any ACTE-specific error."""


# ── Layout / loop ──────────────────────────────────────────────────────────────

class LayoutError(ACTEError):
    """Raised when the heuristic loop exhausts all adjustment steps and still
    cannot fit the content within TailoredConfig.max_pages."""


# ── Rendering / compilation ────────────────────────────────────────────────────

class RenderError(ACTEError):
    """Raised when Jinja2 templating or Typst compilation fails."""


class TemplateNotFoundError(RenderError):
    """Raised when the requested .typ.j2 template cannot be located."""


# ── AI / selection ─────────────────────────────────────────────────────────────

class SelectionError(ACTEError):
    """Raised when the SelectionAgent fails to rank or return valid content."""


class GroundingError(ACTEError):
    """Raised when the GroundingGuard detects a hallucinated bullet or role."""


# ── Persistence / cache ────────────────────────────────────────────────────────

class CacheError(ACTEError):
    """Raised on cache read/write failures."""


# ── Input validation ───────────────────────────────────────────────────────────

class ConfigError(ACTEError):
    """Raised for invalid TailoredConfig values that pass Pydantic but are
    semantically wrong (e.g. min_font_size > initial font_size)."""
