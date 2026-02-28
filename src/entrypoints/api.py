"""FastAPI entrypoint — thin wrapper over Pipeline. No business logic here.

All orchestration lives in application/pipeline.py.
This file only: defines route shapes, constructs concrete infra objects,
calls Pipeline, and returns HTTP responses.

Endpoints (Phase 4):
    POST /generate              Synchronous generation; returns PDF bytes
    POST /tailor                Long-running AI tailoring; returns {job_id}
    GET  /status/{job_id}       Poll status of a tailor job
    GET  /preview/{job_id}      Return preview PDF for a completed job
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ..application.pipeline import Pipeline
from ..infra.cache import ContentCache
from ..infra.llm import LiteLLMClient
from ..infra.renderer import Renderer

app = FastAPI(title="ACTE API", version="0.1.0")

# ── Dependency wiring (replace with DI framework if needed) ──────────────────

_PIPELINE: Pipeline | None = None


def _get_pipeline() -> Pipeline:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = Pipeline(
            llm=LiteLLMClient(),
            renderer=Renderer(templates_dir=Path("templates")),
            cache=ContentCache(cache_dir=Path("output/cache")),
        )
    return _PIPELINE


# ── Request / response schemas ────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    master: dict          # raw MasterExperience JSON
    config: dict          # raw TailoredConfig JSON
    job_description: str = ""


class TailorRequest(GenerateRequest):
    pass


class JobStatusResponse(BaseModel):
    job_id: str
    status: str           # "pending" | "running" | "done" | "failed"
    result_url: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/generate", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
async def generate(request: GenerateRequest) -> Response:
    """Synchronous CV generation. Returns PDF bytes."""
    raise NotImplementedError


@app.post("/tailor", response_model=JobStatusResponse)
async def tailor(request: TailorRequest) -> JobStatusResponse:
    """Long-running AI tailoring. Returns a job_id to poll with /status."""
    raise NotImplementedError


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def status(job_id: str) -> JobStatusResponse:
    """Poll status of a long-running tailor job."""
    raise NotImplementedError


@app.get("/preview/{job_id}", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
async def preview(job_id: str) -> Response:
    """Return preview PDF for a completed job."""
    raise NotImplementedError
