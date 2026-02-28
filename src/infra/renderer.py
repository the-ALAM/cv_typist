"""Renderer — implements RendererPort using Jinja2 + Typst.

Every string injected into .typ templates MUST pass through the `| te` filter
(Typst escape) defined here to prevent injection and encoding bugs.

Dependency rule: domain/ + application/ports + jinja2 + typst + pypdf.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import typst
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound
from pypdf import PdfReader

from ..application.ports import RendererPort
from ..domain.exceptions import RenderError, TemplateNotFoundError
from ..domain.models import LayoutParams, ResolvedContent

logger = logging.getLogger(__name__)

_TYPST_ESCAPE: dict[str, str] = {
    "\\": "\\\\",
    '"': '\\"',
    "#": "\\#",
}


def _typst_escape(value: str) -> str:
    """Jinja2 `te` filter: escape a string for safe inclusion in a Typst double-quoted string literal."""
    for char, replacement in _TYPST_ESCAPE.items():
        value = value.replace(char, replacement)
    return value


class TypstCompilationError(RenderError):
    """Wraps typst stderr output on compilation failure."""


class TypstMonotoneViolation(RenderError):
    """Raised when binary search detects non-monotone page-count behavior."""


class Renderer:
    """Renders ResolvedContent to PDF bytes via Jinja2 + Typst.

    All LayoutParams are passed as template variables, so Python fully controls
    the physical dimensions — no magic numbers live inside .typ files.
    """

    def __init__(
        self,
        templates_dir: Path,
        template_name: str = "resume.typ.j2",
    ) -> None:
        self._template_name = template_name
        self._templates_dir = templates_dir
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=StrictUndefined,
            autoescape=False,
        )
        self._env.filters["te"] = _typst_escape

    def render(
        self,
        content: ResolvedContent,
        layout: LayoutParams,
        tmp_dir: Path,
    ) -> tuple[bytes, int]:
        """Render content with layout. Returns (pdf_bytes, page_count).

        Raises:
            TemplateNotFoundError: template file cannot be found.
            RenderError: Jinja2 or Typst compilation fails.
        """
        typ_source = self._render_template(content, layout)
        pdf_bytes = self._compile_typst(typ_source, tmp_dir)
        page_count = self._count_pages(pdf_bytes)
        return pdf_bytes, page_count

    def _render_template(self, content: ResolvedContent, layout: LayoutParams) -> str:
        """Returns the rendered .typ string. Independently testable without Typst."""
        try:
            template = self._env.get_template(self._template_name)
        except TemplateNotFound as exc:
            raise TemplateNotFoundError(
                f"Template {self._template_name!r} not found in {self._templates_dir}"
            ) from exc
        try:
            return template.render(
                layout=layout,
                experiences=content.experiences,
            )
        except Exception as exc:
            raise RenderError(f"Jinja2 rendering failed: {exc}") from exc

    def _compile_typst(self, typ_source: str, tmp_dir: Path) -> bytes:
        """Writes .typ to disk, calls typst.compile(), returns PDF bytes."""
        typ_path = tmp_dir / "resume.typ"
        typ_path.write_text(typ_source, encoding="utf-8")
        try:
            pdf_bytes = typst.compile(str(typ_path))
        except Exception as exc:
            raise TypstCompilationError(f"Typst compilation failed: {exc}") from exc
        return pdf_bytes

    def _count_pages(self, pdf_bytes: bytes) -> int:
        """Uses pypdf to count pages from PDF bytes."""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
