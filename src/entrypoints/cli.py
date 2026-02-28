"""CLI entrypoint — thin wrapper over Pipeline. No business logic here.

All orchestration lives in application/pipeline.py.
This file only: parses CLI args, constructs concrete infra objects, calls Pipeline.

Usage:
    uv run python -m src.entrypoints.cli generate --master data/master_example.yaml \\
        --config data/config_example.yaml --jd "Python engineer role..."
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import typer

from ..application.pipeline import Pipeline
from ..infra.cache import ContentCache
from ..infra.llm import LiteLLMClient
from ..infra.loader import load_config, load_master
from ..infra.renderer import Renderer

app = typer.Typer(name="cv-typist", help="Agentic CV tailoring engine (ACTE)")


def _build_pipeline(cache_dir: Path, templates_dir: Path) -> Pipeline:
    """Wire concrete infra objects into Pipeline."""
    llm = LiteLLMClient()
    renderer = Renderer(templates_dir=templates_dir)
    cache = ContentCache(cache_dir=cache_dir)
    return Pipeline(llm=llm, renderer=renderer, cache=cache)


@app.command()
def generate(
    master: Path = typer.Option(..., exists=True, help="Master experience YAML/JSON"),
    config: Path = typer.Option(..., exists=True, help="TailoredConfig YAML/JSON"),
    output: Path = typer.Option(Path("output/resume.pdf"), help="Output PDF path"),
    jd: str = typer.Option("", help="Job description text (or leave blank)"),
    jd_file: Path = typer.Option(None, exists=True, help="Job description file"),
    templates_dir: Path = typer.Option(Path("templates"), help="Templates directory"),
    cache_dir: Path = typer.Option(Path("output/cache"), help="Cache directory"),
) -> None:
    """Generate a tailored CV from a master experience list."""
    job_description = jd
    if jd_file is not None:
        job_description = jd_file.read_text(encoding="utf-8")

    master_data = load_master(master)
    tailored_config = load_config(config)
    pipeline = _build_pipeline(cache_dir=cache_dir, templates_dir=templates_dir)

    with tempfile.TemporaryDirectory() as tmp:
        pdf_bytes = pipeline.run(
            master=master_data,
            job_description=job_description,
            config=tailored_config,
            tmp_dir=Path(tmp),
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pdf_bytes)
    typer.echo(f"✓ Written to {output}")


if __name__ == "__main__":
    app()
