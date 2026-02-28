# CV Typist — Agentic CV Tailoring Engine (ACTE)

A Python-based system that generates highly configurable CVs using **Typst** and **Jinja2**. It selects experiences from a master list, applies AI-driven tailoring based on a job description, and enforces strict physical constraints (page count) via a heuristic feedback loop.

## Quick Start

```bash
# Install dependencies
uv sync

# Generate a PDF from example data
uv run python -m src.entrypoints.cli \
  --master data/master_example.yaml \
  --config data/config_example.yaml \
  --output output/resume.pdf
```

The generated PDF appears in `output/resume.pdf`.

## How It Works

1. **Load** a master experience list (YAML/JSON) and a tailoring config
2. **Sort** experiences by priority (highest first)
3. **Render** a Typst document via Jinja2 templating
4. **Compile** to PDF using `typst-py`

In later phases, the system will also:
- **Fit** content to page limits via a heuristic loop (spacing → font → pruning)
- **Score** experiences against a job description using an LLM
- **Rephrase** bullet points to highlight JD-relevant skills
- **Serve** generation requests via a FastAPI endpoint

## Project Structure

```
cv_typist/
├── src/
│   ├── domain/          # Pure models, state, exceptions (no I/O)
│   │   ├── models.py    # Pydantic schemas: ExperienceItem, LayoutParams, etc.
│   │   ├── actions.py   # Immutable action types for the heuristic loop
│   │   ├── state.py     # GenerationState (frozen dataclass)
│   │   ├── types.py     # Type aliases
│   │   └── exceptions.py
│   ├── application/     # Orchestration (imports domain/ only)
│   │   ├── loop.py      # HeuristicLoop controller
│   │   ├── pipeline.py  # Full pipeline coordinator
│   │   └── ports.py     # Abstract protocols (RendererPort, LLMClientPort, CachePort)
│   ├── infra/           # Concrete implementations (imports domain/ + application/ports)
│   │   ├── renderer.py  # Jinja2 + Typst compilation
│   │   ├── loader.py    # YAML/JSON file loading
│   │   ├── llm.py       # LiteLLM wrapper
│   │   ├── selection.py # SelectionAgent (AI scoring/rephrasing)
│   │   ├── grounding.py # GroundingGuard (hallucination detection)
│   │   └── cache.py     # File-based content cache
│   └── entrypoints/     # Thin wrappers (CLI, API)
│       ├── cli.py       # Typer CLI
│       └── api.py       # FastAPI routes
├── templates/
│   └── resume.typ.j2   # Jinja2 + Typst template
├── data/
│   ├── master_example.yaml  # 6 example experiences
│   └── config_example.yaml  # Example tailoring config
├── tests/
│   ├── domain/          # Pure unit tests (zero I/O)
│   ├── application/     # Loop tests (mocked renderer)
│   ├── infra/           # Renderer, cache, selection tests
│   └── e2e/             # Phase gate tests
├── output/              # Generated PDFs
├── docs/                # Design documents
└── pyproject.toml
```

## Architecture

The codebase follows a **layered architecture** with strict dependency rules:

```
domain/  ←  application/  ←  infra/  ←  entrypoints/
```

- **domain/** — Pure Python + Pydantic. No I/O, no external imports.
- **application/** — Orchestration logic. Imports `domain/` only. Depends on abstract `ports`, never concrete implementations.
- **infra/** — Implements the ports. Imports `domain/` + `application/ports` + external libraries.
- **entrypoints/** — Wires everything together. CLI and API live here.

The **HeuristicLoop** (application layer) has zero knowledge of LLMs or job descriptions. It consumes a `ResolvedContent` object and a `TailoredConfig`, nothing more.

## Data Files

### Master Experience (`data/master_example.yaml`)

```yaml
experiences:
  - id: "exp-001"
    role: "Senior Software Engineer"
    company: "Acme Corp"
    date: "2022-01 – 2024-03"
    bullets:
      - "Designed and shipped a Python/FastAPI microservice handling 50k req/day"
    keywords: ["Python", "FastAPI", "Kafka"]
    priority: 0.95    # 0.0–1.0; higher = keep under page pressure
```

### Tailoring Config (`data/config_example.yaml`)

```yaml
max_pages: 1               # Hard page limit
min_font_size_pt: 8.5      # Floor for font reduction
allow_rephrasing: false     # Enable AI bullet rewriting (Phase 3)
alpha: 0.5                  # Pruning weight: alpha*match_score + (1-alpha)*priority
```

## CLI Usage

```bash
# Basic generation
uv run python -m src.entrypoints.cli \
  --master data/master_example.yaml \
  --config data/config_example.yaml

# Custom output path
uv run python -m src.entrypoints.cli \
  --master data/master_example.yaml \
  --config data/config_example.yaml \
  --output output/my_cv.pdf

# Custom templates directory
uv run python -m src.entrypoints.cli \
  --master data/master_example.yaml \
  --config data/config_example.yaml \
  --templates-dir templates/
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run all tests
uv run pytest

# Run only fast domain tests (no Typst needed)
uv run pytest tests/domain/

# Run Phase 1 gate tests
uv run pytest tests/e2e/test_phase1.py -v

# Lint
uv run ruff check src/ tests/
```

## Tech Stack

| Component | Library |
|-----------|---------|
| Models & validation | Pydantic v2 |
| Templating | Jinja2 |
| Typesetting | Typst (via `typst-py`) |
| PDF inspection | pypdf |
| CLI | Typer |
| Data files | PyYAML |
| API (Phase 4) | FastAPI + Uvicorn |
| AI (Phase 3) | LiteLLM |

## Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| **1 — CLI & Templating** | ✅ Done | Load YAML → Jinja2 → Typst → PDF |
| **2 — Constraint Engine** | 🔲 Pending | Heuristic loop: spacing → font → pruning |
| **3 — AI Integration** | 🔲 Pending | LLM scoring, rephrasing, grounding guard |
| **4 — API & Persistence** | 🔲 Pending | FastAPI endpoints, caching, history |

See [docs/ACTE_implementation_artifact.md](docs/ACTE_implementation_artifact.md) for the full specification and [docs/STATUS.md](docs/STATUS.md) for detailed current state.
