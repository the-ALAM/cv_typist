# ACTE Copilot Instructions

## Architecture: Hexagonal Layers

```
domain/      → stdlib + pydantic only. ZERO imports from acte.*
application/ → domain/ + stdlib only. NEVER imports infra/
infra/       → domain/ + application/ports + external libs
entrypoints/ → application/ + infra/ + domain/ (wiring only)
```

### The Dependency Rule — enforce this mechanically

| Layer | May import from | FORBIDDEN |
|---|---|---|
| `domain/` | stdlib, pydantic | anything in `src.*` |
| `application/` | `domain/`, stdlib | `infra/`, litellm, jinja2, typst |
| `infra/` | `domain/`, `application/ports`, external libs | — |
| `entrypoints/` | all layers | business logic (belongs in `application/`) |

**Corollary rules:**
- `loop.py` MUST NOT import from `selection.py`, `grounding.py`, `llm.py`, or `litellm`
- `selection.py` and `grounding.py` MUST import LLM via `infra/llm.py`, never `litellm` directly
- All custom exceptions live in `domain/exceptions.py` — import from nowhere else
- Every string rendered into `.typ` files MUST use the `| te` Jinja2 filter (defined in `infra/renderer.py`)

## Key Interface

`ResolvedContent` is the hard boundary between the AI layer and the layout layer:

```python
# SelectionAgent (infra) produces it
resolved: ResolvedContent = agent.select(master, jd, config)

# HeuristicLoop (application) consumes it — knows nothing about how it was made
pdf_bytes, state = loop.run(resolved, config, tmp_dir)
```

## Where Things Belong

| Concept | File |
|---|---|
| Pydantic models | `src/domain/models.py` |
| Type aliases | `src/domain/types.py` |
| Immutable loop state | `src/domain/state.py` |
| ALL custom exceptions | `src/domain/exceptions.py` |
| Port Protocols | `src/application/ports.py` |
| Heuristic loop controller | `src/application/loop.py` |
| Pipeline orchestrator | `src/application/pipeline.py` |
| Jinja2 + Typst renderer | `src/infra/renderer.py` |
| LiteLLM wrapper | `src/infra/llm.py` |
| AI selection agent | `src/infra/selection.py` |
| Grounding guard | `src/infra/grounding.py` |
| File-based cache | `src/infra/cache.py` |
| YAML/JSON loader | `src/infra/loader.py` |
| CLI (Typer) | `src/entrypoints/cli.py` |
| API (FastAPI) | `src/entrypoints/api.py` |

## Phase Gate

- Current phase: **Phase 1** — CLI & Templating Foundation
- Do not implement Phase N+1 code until all Phase N tests pass

## Test Commands

```bash
# Domain unit tests (zero I/O, always fast)
uv run pytest tests/domain/ -v

# Application tests (mocked ports, no external deps)
uv run pytest tests/application/ -v

# Infra tests (needs Typst/LLM — skip in CI with -m "not integration")
uv run pytest tests/infra/ -v -m "not integration"

# Phase gate
uv run pytest tests/e2e/test_phase1.py -v
```
