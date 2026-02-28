"""CLI entrypoint — thin wrapper over Pipeline. No business logic here.

All orchestration lives in application/pipeline.py.
This file only: parses CLI args, constructs concrete infra objects, calls Pipeline.

Usage:
    uv run python -m src.entrypoints.cli generate --master data/master_example.yaml \
        --config data/config_example.yaml
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import typer

from ..domain.models import LayoutParams, ResolvedContent
from ..infra.loader import load_config, load_master
from ..infra.renderer import Renderer

app = typer.Typer(name="cv-typist", help="Agentic CV tailoring engine (ACTE)")


@app.command()
def generate(
    master: Path = typer.Option(..., exists=True, help="Master experience YAML/JSON"),
    config: Path = typer.Option(..., exists=True, help="TailoredConfig YAML/JSON"),
    output: Path = typer.Option(Path("output/resume.pdf"), help="Output PDF path"),
    templates_dir: Path = typer.Option(Path("templates"), help="Templates directory"),
) -> None:
    """Generate a PDF from a master experience list and config.

    Phase 1: No AI, no heuristic loop. Renders all experiences sorted by priority.
    """
    master_data = load_master(master)
    load_config(config)  # validate config; layout uses defaults for Phase 1

    sorted_experiences = sorted(
        master_data.experiences, key=lambda e: e.priority, reverse=True
    )
    content = ResolvedContent(experiences=sorted_experiences)

    renderer = Renderer(templates_dir=templates_dir)
    layout = LayoutParams()
    with tempfile.TemporaryDirectory() as tmp:
        pdf_bytes, page_count = renderer.render(content, layout, Path(tmp))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pdf_bytes)
    typer.echo(f"✓ Written {page_count}-page PDF to {output}")


if __name__ == "__main__":
    app()
