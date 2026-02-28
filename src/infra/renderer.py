"""Renderer — implements RendererPort using Jinja2 + Typst.

Responsibilities absorbed from:
  src/render.py     (empty stub)
  src/compiler.py   (empty stub)
  src/transformer.py (transform typst → pdf/png)

Every string injected into .typ templates MUST pass through the `| te` filter
(Typst escape) defined here to prevent injection and encoding bugs.

Dependency rule: domain/ + application/ports + jinja2 + typst.
"""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..application.ports import RendererPort
from ..domain.exceptions import RenderError, TemplateNotFoundError
from ..domain.models import LayoutParams, ResolvedContent

logger = logging.getLogger(__name__)

# Characters that must be escaped inside Typst content strings.
_TYPST_ESCAPE: dict[str, str] = {
    "\\": "\\\\",
    '"': '\\"',
    "#": "\\#",
    "@": "\\@",
    "*": "\\*",
    "_": "\\_",
    "`": "\\`",
    "$": "\\$",
    "<": "\\<",
    ">": "\\>",
    "~": "\\~",
    "=": "\\=",
    "+": "\\+",
    "-": "\\-",
    "/": "\\/",
}


def _typst_escape(value: str) -> str:
    """Jinja2 `te` filter: escape a string for safe inclusion in Typst source."""
    for char, replacement in _TYPST_ESCAPE.items():
        value = value.replace(char, replacement)
    return value


class Renderer:
    """Renders ResolvedContent to PDF/PNG bytes via Jinja2 + Typst.

    All LayoutParams are passed as template variables, so Python fully controls
    the physical dimensions — no magic numbers live inside .typ files.

    Example::

        renderer = Renderer(templates_dir=Path("templates"))
        pdf_bytes, page_count = renderer.render(content, layout, tmp_dir)
    """

    def __init__(
        self,
        templates_dir: Path,
        template_name: str = "resume.typ.j2",
    ) -> None:
        self._template_name = template_name
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=StrictUndefined,
            autoescape=False,  # Typst is not HTML; we use `te` manually
        )
        self._env.filters["te"] = _typst_escape

    def render(
        self,
        content: ResolvedContent,
        layout: LayoutParams,
        tmp_dir: Path,
    ) -> tuple[bytes, int]:
        """Render content with layout. Returns (document_bytes, page_count).

        Raises:
            TemplateNotFoundError: template file cannot be found.
            RenderError: Jinja2 or Typst compilation fails.
        """
        raise NotImplementedError
