# ACTE — Current System Status

> Last updated after Phase 1 completion.

## What's Working

### Phase 1: CLI & Templating ✅

The foundational pipeline is fully operational:

```
YAML files → Pydantic validation → Jinja2 template → Typst compilation → PDF
```

**Running it:**

```bash
uv run python -m src.entrypoints.cli \
  --master data/master_example.yaml \
  --config data/config_example.yaml \
  --output output/resume.pdf
```

This loads 6 experiences, sorts them by priority (highest first), renders them through the Jinja2+Typst template, and writes a PDF to disk.

### Implemented Components

| Component | File | Status |
|-----------|------|--------|
| `ExperienceItem` | `src/domain/models.py` | ✅ With `priority`, `match_score`, field constraints |
| `MasterExperience` | `src/domain/models.py` | ✅ With `unique_ids` validator |
| `LayoutParams` | `src/domain/models.py` | ✅ Fields: `margin_pt`, `gutter_pt`, `font_size_pt`, `item_spacing_pt` |
| `TailoredConfig` | `src/domain/models.py` | ✅ Fields: `max_pages`, `min_font_size_pt`, `alpha`, `allow_rephrasing` |
| `ResolvedContent` | `src/domain/models.py` | ✅ Boundary object between AI and layout layers |
| `GenerationArtifact` | `src/domain/models.py` | ✅ Output container for PDF + audit log |
| `GenerationState` | `src/domain/state.py` | ✅ Immutable, with `apply_action`, `add_warning`, `pruning_score` |
| Action types | `src/domain/actions.py` | ✅ `SpacingAction`, `FontAction`, `PruneAction`, `NoOpAction` |
| Exception hierarchy | `src/domain/exceptions.py` | ✅ All exceptions inherit `ACTEError` |
| Port protocols | `src/application/ports.py` | ✅ `RendererPort`, `LLMClientPort`, `CachePort` |
| Typst escape filter | `src/infra/renderer.py` | ✅ Escapes `\`, `"`, `#` in Typst string literals |
| Renderer | `src/infra/renderer.py` | ✅ `render()`, `_render_template()`, `_compile_typst()`, `_count_pages()` |
| YAML/JSON loader | `src/infra/loader.py` | ✅ `load_master()`, `load_config()` |
| CLI generate | `src/entrypoints/cli.py` | ✅ Loads, sorts, renders, writes PDF |
| Jinja2+Typst template | `templates/resume.typ.j2` | ✅ `experience_block` helper, `| te` filter |

### Test Suite

```
69 passed, 8 skipped
```

The 8 skipped tests belong to Phases 2–4 (gated behind `pytest.skip` or `NotImplementedError`).

**Phase 1 gate tests (all 5 pass):**

| # | Test | What it verifies |
|---|------|-----------------|
| 1 | `test_typst_escape_special_chars` | `#`, `\`, `"` are escaped in rendered `.typ` |
| 2 | `test_renderer_returns_pdf_bytes` | `Renderer.render()` returns non-empty bytes, page_count ≥ 1 |
| 3 | `test_renderer_template_isolation` | `_render_template()` works without Typst (pure string test) |
| 4 | `test_cli_produces_output_file` | CLI writes a valid PDF to disk |
| 5 | `test_pdf_contains_all_experiences` | All experience roles/companies appear in PDF text |

## What's Stubbed (NotImplementedError)

These components have their interfaces defined, imports wired, and tests scaffolded, but the implementation raises `NotImplementedError`:

| Component | File | Phase |
|-----------|------|-------|
| `HeuristicLoop.run()` | `src/application/loop.py` | Phase 2 |
| `Pipeline.run()` | `src/application/pipeline.py` | Phase 2+ |
| `LiteLLMClient.complete()` | `src/infra/llm.py` | Phase 3 |
| `SelectionAgent.select()` | `src/infra/selection.py` | Phase 3 |
| `GroundingGuard.verify()` | `src/infra/grounding.py` | Phase 3 |
| `ContentCache.get()` / `.set()` | `src/infra/cache.py` | Phase 4 |
| API endpoints | `src/entrypoints/api.py` | Phase 4 |

## Data Files

**`data/master_example.yaml`** — 6 experiences with:
- Priorities ranging from 0.20 to 0.95
- Special characters in bullets: `#`, `\`, `"` (to test the escape filter)
- Varied keyword sets for future AI scoring

**`data/config_example.yaml`** — Default configuration:
- `max_pages: 1`
- `min_font_size_pt: 8.5`
- `allow_rephrasing: false`
- `alpha: 0.5`

## Architecture Invariants

These rules are enforced and must not be violated in future phases:

1. **HeuristicLoop imports nothing from `infra/`** — it consumes `ResolvedContent` via the `RendererPort` protocol, never concrete classes.
2. **Typst escape filter is mandatory** — every user string in `.typ` templates passes through `| te`.
3. **GenerationState is immutable** — `apply_action()` and `add_warning()` return new instances.
4. **`match_score` is always `None` in Phases 1 & 2** — `pruning_score()` forces `alpha=0.0` when `match_score is None`, falling back to priority-only ranking.
5. **No circular imports** — the dependency graph is strictly acyclic: `domain/ ← application/ ← infra/ ← entrypoints/`.

## Next Up: Phase 2

The heuristic loop implementation. The goal: given a large master experience list and `max_pages: 1`, produce a PDF that fits by systematically adjusting spacing, font size, and pruning items. All intermediate states are recorded in an action log.

Key tests to pass (from spec):
1. Loop fits 8 experiences into 1 page
2. Spacing actions precede font actions in the log
3. Font actions precede prune actions
4. Lowest-priority items are pruned first
5. Stall detection fast-forwards to the next step
6. Oversized PDF emits a warning (doesn't crash)
7. Action log is a complete reproducible audit trail
8. Non-monotone page counts trigger fallback (no crash)
