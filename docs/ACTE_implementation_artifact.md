# ACTE: Agentic CV Tailoring Engine — Coding Agent Implementation Artifact

> **Purpose:** This document is the single source of truth for a coding agent implementing the ACTE system. Every architectural decision has been pre-resolved. Do not deviate from the patterns, interfaces, or constraints described here without explicit instruction. Each phase ends with a clear, runnable test that must pass before the next phase begins.

---

## 0. Project Scaffold & Directory Structure

Create the following structure before writing any code:

```
cv_typist/
├── src/
│   └── acte/
│       ├── __init__.py
│       ├── models.py          # All Pydantic models
│       ├── renderer.py        # Renderer class (Jinja2 + Typst)
│       ├── loop.py            # HeuristicLoop controller
│       ├── actions.py         # Immutable Action types
│       ├── state.py           # GenerationState immutable dataclass
│       ├── selection.py       # SelectionAgent (Phase 3)
│       ├── grounding.py       # GroundingGuard (Phase 3)
│       ├── api.py             # FastAPI app (Phase 4)
│       ├── cache.py           # File-based cache (Phase 4)
│       └── cli.py             # CLI entrypoint
├── templates/
│   └── resume.typ.j2          # Jinja2 + Typst template
├── data/
│   ├── master_example.yaml    # Example master experience list
│   └── config_example.yaml   # Example TailoredConfig
├── output/                    # Generated PDFs land here
├── tests/
│   ├── test_phase1.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   └── test_phase4.py
├── pyproject.toml
└── README.md
```

### `pyproject.toml` dependencies

```toml
[project]
name = "acte"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "jinja2>=3.1",
    "typst>=0.1",        # typst-py binding
    "pypdf>=4.0",
    "typer>=0.12",
    "pyyaml>=6.0",
    "fastapi>=0.111",
    "uvicorn>=0.30",
    "litellm>=1.40",
    "spacy>=3.7",        # fallback NER; Phase 3 may swap for LLM call
]

[project.scripts]
acte = "acte.cli:app"
```

### 0.1 Package Initialisation Files

Every directory containing Python source is a proper package. `__init__.py` files serve two purposes: establishing the **public interface** of each module and enforcing the **import topology** that prevents circular dependencies.

**Dependency order — strictly acyclic.**

**`src/acte/__init__.py`** — re-exports Phase 1 & 2 symbols only. Phase 3/4 components are intentionally **not** re-exported here to avoid pulling LiteLLM/FastAPI into contexts that only need the core engine:

```python
from .models import (
    ExperienceItem,
    MasterExperience,
    LayoutParams,
    TailoredConfig,
    ResolvedContent,
    GenerationArtifact,
)
from .renderer import Renderer, TypstCompilationError, TypstMonotoneViolation
from .loop import HeuristicLoop
from .actions import SpacingAction, FontAction, PruneAction, NoOpAction, Action
from .state import GenerationState

__all__ = [
    "ExperienceItem", "MasterExperience", "LayoutParams", "TailoredConfig",
    "ResolvedContent", "GenerationArtifact",
    "Renderer", "TypstCompilationError", "TypstMonotoneViolation",
    "HeuristicLoop",
    "SpacingAction", "FontAction", "PruneAction", "NoOpAction", "Action",
    "GenerationState",
]
```

**Import rules enforced by the topology above:**
- `models.py` — no intra-package imports (leaf node).
- `actions.py` / `state.py` — may import from `models` only.
- `renderer.py` — may import from `models`; no loop or AI imports.
- `loop.py` — may import from `models`, `actions`, `state`, `renderer`. **Must not import `selection`, `grounding`, `cache`, or any LLM library.**
- `selection.py` — may import from `models`, `loop` (for type hints only via `TYPE_CHECKING`). Imports `grounding`.
- `grounding.py` — may import from `models` only.
- `cache.py` — may import from `models`, `selection` (for `ResolvedContent` type).
- `api.py` — may import from all of the above.
- `cli.py` — may import from all of the above.

**Rule:** Never use `from .module import *`. All imports must be explicit. Circular imports that violate this topology are a hard failure.

---

## Phase 1: CLI & Templating (The Foundation)

**Goal:** `acte generate --master data/master_example.yaml --config data/config_example.yaml` produces a valid, readable PDF in `output/`.

### 1.1 Pydantic Models — `src/acte/models.py`

Implement exactly these models. Field constraints are requirements, not suggestions.

```python
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ExperienceItem(BaseModel):
    id: str                          # Unique slug, e.g. "acme-backend-2022"
    role: str
    company: str
    date: str                        # Human-readable, e.g. "Jan 2022 – Mar 2024"
    bullets: list[str]               # Original bullet points, never mutated after load
    keywords: list[str] = Field(default_factory=list)
    priority: float = Field(ge=0.0, le=1.0)   # User-assigned, 0.0 = lowest
    match_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    # Set by SelectionAgent in Phase 3. None in Phases 1 & 2.


class MasterExperience(BaseModel):
    experiences: list[ExperienceItem]

    @model_validator(mode="after")
    def unique_ids(self) -> MasterExperience:
        ids = [e.id for e in self.experiences]
        assert len(ids) == len(set(ids)), "ExperienceItem IDs must be unique"
        return self


class LayoutParams(BaseModel):
    margin_pt: float = Field(default=56.0, ge=20.0, le=80.0)   # ~20mm default
    gutter_pt: float = Field(default=6.0,  ge=2.0,  le=16.0)
    font_size_pt: float = Field(default=10.5, ge=7.0, le=14.0)
    item_spacing_pt: float = Field(default=4.0, ge=1.0, le=10.0)


class TailoredConfig(BaseModel):
    max_pages: int = Field(default=1, ge=1, le=4)
    min_font_size_pt: float = Field(default=8.5, ge=7.0, le=10.0)
    allow_rephrasing: bool = False
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    # alpha controls pruning score: score = alpha*match_score + (1-alpha)*priority
    # When match_score is None, alpha is forced to 0.0 automatically.


class ResolvedContent(BaseModel):
    """
    The output of Stage 1 (Content Resolution).
    This is the hard interface boundary between the AI layer and the layout layer.
    The HeuristicLoop must NEVER call any LLM. It consumes only ResolvedContent.
    """
    experiences: list[ExperienceItem]   # Ordered: highest relevance first
    # bullets on each item may be rephrased versions (Phase 3) or originals (Phase 1/2)
    # The loop prunes from the END of this list (lowest relevance last)
    job_description: Optional[str] = None
    # Populated by SelectionAgent for audit/history. NEVER read by HeuristicLoop.
    # Stored verbatim in output/history/{run}/job_description.txt.


class GenerationArtifact(BaseModel):
    pdf_bytes: bytes
    final_page_count: int
    final_layout: LayoutParams
    action_log: list[dict]       # Serialized list of actions applied
    warnings: list[str] = Field(default_factory=list)
```

### 1.2 Jinja2 + Typst Template — `templates/resume.typ.j2`

This is the canonical template. The Typst escape filter (Section 1.3) MUST be applied to all user-supplied string values via the `| te` filter.

```typst
// ---- ACTE Generated Resume ----
// All dimension variables are injected by Python. Do not hardcode values.

#set page(
  margin: {{ layout.margin_pt }}pt,
  width: 210mm,
  height: 297mm,
)

#set text(
  size: {{ layout.font_size_pt }}pt,
  font: ("Times New Roman", "Liberation Serif", "Georgia"),
  // Fallback order: Liberation Serif (Linux), Times New Roman (Windows/macOS), Georgia (all).
  // All three are pre-installed on most devices. Typst will use the first match found.
)

#set par(leading: {{ layout.item_spacing_pt }}pt)

// ---- Helper function ----
#let experience_block(role, company, date, bullets) = {
  block(breakable: false, below: {{ layout.gutter_pt }}pt)[
    #grid(
      columns: (1fr, auto),
      [*#role* #h(4pt) #text(style: "italic")[#company]],
      [#text(style: "italic")[#date]]
    )
    #for b in bullets [
      - #b
    ]
  ]
}

// ---- Content ----
{% block experiences %}
{% for exp in experiences %}
#experience_block(
  "{{ exp.role | te }}",
  "{{ exp.company | te }}",
  "{{ exp.date | te }}",
  (
    {% for bullet in exp.bullets %}
    "{{ bullet | te }}",
    {% endfor %}
  )
)
{% endfor %}
{% endblock %}
```

### 1.3 Typst Escape Filter

This filter MUST be registered in Jinja2 before any template is rendered. Failure to do so will cause silent corruption or Typst compilation errors on real resume data.

Characters that require escaping in Typst string literals: `\`, `"`, `#`

```python
# In renderer.py, register this filter on the Jinja2 Environment:

def typst_escape(value: str) -> str:
    """Escape a string for safe inclusion inside a Typst double-quoted string literal."""
    value = value.replace("\\", "\\\\")  # Must be first
    value = value.replace('"', '\\"')
    value = value.replace("#", "\\#")
    return value

# env.filters["te"] = typst_escape
```

### 1.4 Renderer Class — `src/acte/renderer.py`

The `Renderer` class has one public method. It knows nothing about the heuristic loop, AI, or page constraints.

```python
class Renderer:
    """
    Responsible for: Jinja2 rendering → .typ string → Typst compilation → (pdf_bytes, page_count).

    This class has NO knowledge of the HeuristicLoop, TailoredConfig, or the AI layer.
    It is a pure function: same inputs always produce same outputs.
    """

    def __init__(self, template_dir: Path):
        # Set up Jinja2 Environment with typst_escape filter registered as "te"
        ...

    def render(
        self,
        content: ResolvedContent,
        layout: LayoutParams,
        tmp_dir: Path,
    ) -> tuple[bytes, int]:
        """
        Returns (pdf_bytes, page_count).
        Writes .typ and .pdf to tmp_dir, reads page count via pypdf, cleans up.
        Raises TypstCompilationError on non-zero exit from typst compiler.
        Raises TypstMonotoneViolation if used in monotone-check mode (Phase 2).
        """
        ...

    def _render_template(self, content: ResolvedContent, layout: LayoutParams) -> str:
        """Returns the rendered .typ string. Independently testable."""
        ...

    def _compile_typst(self, typ_source: str, tmp_dir: Path) -> bytes:
        """Writes .typ to disk, calls typst-py or subprocess, returns pdf bytes. Independently testable."""
        ...

    def _count_pages(self, pdf_bytes: bytes) -> int:
        """Uses pypdf to count pages. Writes to tmp file if needed, cleans up."""
        ...
```

**Error types to define in `renderer.py`:**
- `TypstCompilationError(Exception)` — wraps typst stderr output
- `TypstMonotoneViolation(Exception)` — raised when binary search detects non-monotone behavior

### 1.5 CLI — `src/acte/cli.py`

```python
import typer
app = typer.Typer()

@app.command()
def generate(
    master: Path = typer.Option(..., help="Path to master YAML experience list"),
    config: Path = typer.Option(..., help="Path to TailoredConfig YAML"),
    output: Path = typer.Option(Path("output/resume.pdf")),
):
    """
    Phase 1: Generate a PDF with fixed formatting. No AI, no loop.
    Loads master YAML → builds ResolvedContent (all items, original bullets, ordered by priority desc)
    → Renderer.render() → writes PDF.
    """
    ...
```

### 1.6 Example Data Files

**`data/master_example.yaml`** — populate with at least 6 experience items with varied priorities (0.2 through 1.0) and bullets that contain special characters (`#`, `\`, `"`) to validate the escape filter.

**`data/config_example.yaml`:**
```yaml
max_pages: 1
min_font_size_pt: 8.5
allow_rephrasing: false
alpha: 0.5
```

### Phase 1 — Success Gate

Run: `acte generate --master data/master_example.yaml --config data/config_example.yaml`

**`tests/test_phase1.py` must pass all of:**
1. `test_typst_escape_special_chars` — verifies `#`, `\`, `"` are escaped correctly in rendered `.typ` string.
2. `test_renderer_returns_pdf_bytes` — `Renderer.render()` returns non-empty bytes and `page_count >= 1`.
3. `test_renderer_template_isolation` — `_render_template()` can be called without a Typst installation (pure string test).
4. `test_cli_produces_output_file` — the CLI writes a valid PDF to disk.
5. `test_pdf_contains_all_experiences` — open the PDF with pypdf, verify all experience IDs appear in extracted text.

**Do not proceed to Phase 2 until all 5 tests pass.**

---

## Phase 2: The Constraint Engine (The Brain)

**Goal:** Given a large `MasterExperience` and `max_pages: 1`, the engine produces a PDF that fits within 1 page by systematically adjusting spacing, font, and pruning items. All intermediate states are recorded in an action log.

### 2.1 Immutable Action Types — `src/acte/actions.py`

```python
from dataclasses import dataclass
from typing import Literal, Union

@dataclass(frozen=True)
class SpacingAction:
    kind: Literal["spacing"] = "spacing"
    delta_margin_pt: float = 0.0
    delta_gutter_pt: float = 0.0

@dataclass(frozen=True)
class FontAction:
    kind: Literal["font"] = "font"
    new_font_size_pt: float = 0.0

@dataclass(frozen=True)
class PruneAction:
    kind: Literal["prune"] = "prune"
    pruned_experience_id: str = ""
    pruning_score: float = 0.0

@dataclass(frozen=True)
class NoOpAction:
    """Emitted when a step has no further moves available."""
    kind: Literal["noop"] = "noop"
    reason: str = ""

Action = Union[SpacingAction, FontAction, PruneAction, NoOpAction]
```

### 2.2 Immutable GenerationState — `src/acte/state.py`

```python
from dataclasses import dataclass, replace
from typing import Sequence
from .models import LayoutParams, ResolvedContent
from .actions import Action

@dataclass(frozen=True)
class GenerationState:
    layout: LayoutParams
    content: ResolvedContent
    page_count: int
    actions: tuple[Action, ...]  # Immutable audit log
    warnings: tuple[str, ...]

    def apply_action(self, action: Action, new_page_count: int, new_content: ResolvedContent | None = None) -> "GenerationState":
        """Returns a NEW GenerationState. Never mutates self."""
        return replace(
            self,
            layout=self._apply_layout(action),
            content=new_content if new_content is not None else self.content,
            page_count=new_page_count,
            actions=self.actions + (action,),
        )

    def add_warning(self, msg: str) -> "GenerationState":
        return replace(self, warnings=self.warnings + (msg,))

    def _apply_layout(self, action: Action) -> LayoutParams:
        # Returns updated LayoutParams based on action type.
        # SpacingAction → adjust margin/gutter
        # FontAction → adjust font_size_pt
        # PruneAction / NoOpAction → no layout change
        ...

    def pruning_score(self, exp_id: str, alpha: float) -> float:
        """
        pruning_score = alpha * match_score + (1 - alpha) * priority
        If match_score is None, alpha is forced to 0.0.
        Lower score = pruned first.
        """
        ...
```

### 2.3 HeuristicLoop Controller — `src/acte/loop.py`

Implement the controller exactly as specified below. The order of steps is a hard requirement.

```python
class HeuristicLoop:
    """
    Consumes ResolvedContent + TailoredConfig. Produces GenerationArtifact.
    Has NO knowledge of LLMs, job descriptions, or the SelectionAgent.
    """

    # --- Tunable constants (not user-configurable, internal to the loop) ---
    SPACING_MAX_ITERATIONS = 3
    SPACING_MARGIN_DELTA_PT = -4.0    # Reduce margin by this per step
    SPACING_GUTTER_DELTA_PT = -1.0    # Reduce gutter by this per step
    FONT_BINARY_SEARCH_MAX_ITER = 8
    STALL_DETECTION_WINDOW = 2       # If page_count hasn't changed in N steps, fast-forward to next step

    def run(
        self,
        content: ResolvedContent,
        config: TailoredConfig,
        tmp_dir: Path,
    ) -> GenerationArtifact:
        ...
```

**Loop execution order (implement exactly this):**

```
1. INITIAL RENDER
   - state = GenerationState(default LayoutParams, content, page_count=render(), actions=())
   - If state.page_count <= config.max_pages: return immediately (already fits)

2. STEP A — SPACING REDUCTION (up to SPACING_MAX_ITERATIONS)
   - Each iteration: apply SpacingAction(delta_margin, delta_gutter), re-render, update state
   - Stop early if page_count <= max_pages (success) or stall detected (no improvement in STALL_DETECTION_WINDOW iterations → fast-forward to Step B)
   - Guard: never reduce margin_pt below LayoutParams field minimum (20.0)

3. STEP B — FONT SIZE BINARY SEARCH
   - low = config.min_font_size_pt, high = current font_size_pt
   - Each iteration: mid = (low + high) / 2, apply FontAction(mid), re-render
   - MONOTONE GUARD: Before trusting direction, assert render(mid - 0.1) page_count >= render(mid) page_count.
     If violated: emit warning, do NOT raise, fall back to linear descent instead.
   - Max FONT_BINARY_SEARCH_MAX_ITER iterations
   - Stop early if page_count <= max_pages (success) or font_size reaches min_font_size_pt floor

4. STEP C — PRUNING
   - While page_count > max_pages AND len(content.experiences) > 1:
       - Compute pruning_score for each remaining experience
       - Remove experience with LOWEST score → emit PruneAction
       - Re-render → update state
   - If len(content.experiences) == 1 AND page_count > max_pages:
       STEP D: emit warning "Cannot fit within max_pages; emitting oversized PDF"
       add_warning to state, break loop

5. RETURN GenerationArtifact(
       pdf_bytes=last_render,
       final_page_count=state.page_count,
       final_layout=state.layout,
       action_log=[serialize(a) for a in state.actions],
       warnings=list(state.warnings)
   )
```

### Phase 2 — Success Gate

**`tests/test_phase2.py` must pass all of:**
1. `test_loop_fits_large_input_to_one_page` — Load 8 experience items, `max_pages=1`, verify output PDF is 1 page and action log is non-empty.
2. `test_spacing_step_fires_before_font_step` — Inspect action log; confirm all `SpacingAction`s precede any `FontAction`.
3. `test_font_step_fires_before_prune_step` — Confirm all `FontAction`s precede any `PruneAction`.
4. `test_pruning_removes_lowest_priority_first` — With `alpha=0.0` and no match scores, verify pruned items had the lowest `priority` values.
5. `test_stall_detection_fast_forwards` — Construct a scenario where spacing adjustments cannot reduce page count; verify stall detection skips to Step B within STALL_DETECTION_WINDOW iterations.
6. `test_step_d_warning_emitted` — Force an impossible constraint (1 item, still >1 page); verify `GenerationArtifact.warnings` is non-empty.
7. `test_action_log_is_complete_audit` — Verify `reduce(apply_action, initial_state, log)` reproduces `final_layout` exactly.
8. `test_monotone_guard_fallback` — Mock `Renderer.render` to return non-monotone page counts; verify warning is emitted and loop continues (does not raise).

**Do not proceed to Phase 3 until all 8 tests pass.**

---

## Phase 3: AI Integration (The Intelligence)

**Goal:** A `SelectionAgent` ranks and optionally rephrases experiences based on a Job Description. A `GroundingGuard` rejects any rewrite that introduces semantic drift. The output is a `ResolvedContent` object that the unchanged Phase 2 loop consumes.

### 3.1 SelectionAgent — `src/acte/selection.py`

```python
class SelectionAgent:
    """
    Input:  MasterExperience + job_description (str)
    Output: ResolvedContent (ordered by match_score desc, bullets optionally rephrased)

    This class is the ONLY component that calls the LLM.
    The HeuristicLoop must never be modified to accommodate this class.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        allow_rephrasing: bool = False,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        """
        timeout:     seconds before an individual LLM call is abandoned and retried.
        max_retries: retry attempts on transient errors (e.g. HTTP 429 rate-limit).
                     Retries use exponential back-off: wait = 2 ** attempt seconds.
                     After all retries are exhausted, assign score 0.0 and emit a warning.
        """
        ...

    def resolve(self, master: MasterExperience, job_description: str) -> ResolvedContent:
        """
        Step 1: Score each ExperienceItem (0.0–1.0) via LLM call.
        Step 2: If allow_rephrasing=True, rephrase bullets via LLM.
        Step 3: Run GroundingGuard on every rephrased item.
                If guard fails for a bullet → keep original bullet, emit warning.
        Step 4: Sort by match_score descending.
        Step 5: Return ResolvedContent.
        """
        ...

    def _score_experiences(self, experiences: list[ExperienceItem], jd: str) -> dict[str, float]:
        """
        LLM prompt contract:
        - System: "You are a CV relevance scorer. Return ONLY valid JSON."
        - User: JD text + list of experience IDs + summaries
        - Expected response: {"experience_id": 0.87, ...}
        - Parse with json.loads(); on failure retry once, then assign 0.0 and warn.
        """
        ...

    def _rephrase_bullets(self, item: ExperienceItem, jd: str) -> list[str]:
        """
        LLM prompt contract:
        - System: "Rewrite ONLY the provided bullet points to highlight relevance to the JD.
                   Do NOT invent new roles, companies, dates, or metrics.
                   Return ONLY a JSON array of strings with the same length as input."
        - User: original bullets + JD keywords
        - Validate: len(output) == len(input); on mismatch reject entire rewrite.
        """
        ...
```

### 3.2 GroundingGuard — `src/acte/grounding.py`

This is a hard requirement. No rewrite that introduces semantic drift may pass through.

```python
class GroundingGuard:
    """
    Validates that a rephrased bullet does not introduce or remove protected entities.

    Entity extraction uses a two-tier strategy to minimise LLM call volume:
    - Fast-path: spaCy NER (en_core_web_sm) handles COMPANY, DATE, and METRIC reliably
      and requires zero LLM calls.
    - LLM fallback: invoked only when TECHNOLOGY or ROLE entities may be present
      (spaCy does not reliably detect these categories).

    Cost profile for a resolve() call over N items with rephrasing enabled:
    - Naive (LLM-only):  1 scoring call + N rephrasing calls + 2N grounding calls = 3N+1
    - With spaCy path:   1 scoring call + N rephrasing calls + 0–2 LLM calls per bullet
      For plain-language bullets with no technology terms: grounding LLM calls ≈ 0.
    """

    # Entity categories that are protected (must be preserved exactly):
    PROTECTED_CATEGORIES = {
        "COMPANY",      # Organization names
        "DATE",         # Any temporal expression
        "ROLE",         # Job title / position
        "TECHNOLOGY",   # Specific tech names, languages, frameworks
        "METRIC",       # Any numeric value with a unit or % sign
    }

    def validate(self, original_bullet: str, rephrased_bullet: str) -> tuple[bool, str]:
        """
        Returns (is_valid, reason).
        is_valid=False means the rephrased_bullet must be DISCARDED and original kept.

        Logic:
        1. Extract entities from original_bullet → set A
        2. Extract entities from rephrased_bullet → set B
        3. If (A - B) is non-empty: a protected entity was REMOVED → fail
        4. If (B - A) is non-empty and category is in PROTECTED_CATEGORIES: entity was INVENTED → fail
        5. Otherwise: pass
        """
        ...

    def _extract_entities(self, text: str) -> set[tuple[str, str]]:
        """
        Returns set of (entity_text, category) tuples.

        Two-tier extraction strategy:

        1. spaCy fast-path (always runs first):
           - Load en_core_web_sm model (cached as a module-level singleton on first use).
           - Map spaCy labels → PROTECTED_CATEGORIES:
               ORG              → COMPANY
               DATE / TIME      → DATE
               PERCENT / CARDINAL / QUANTITY → METRIC (only when token text contains
                                                        a digit or '%')
           - ROLE and TECHNOLOGY are not reliably produced by en_core_web_sm and are
             excluded from the spaCy result set.

        2. LLM fallback (conditional):
           - Triggered when the text contains any proper-noun token not already captured
             by spaCy (heuristic for potential TECHNOLOGY or ROLE terms), OR when spaCy
             returns an empty result for a non-trivial text (>3 tokens).
           - Uses the canonical Entity Extraction Prompt from the Appendix.
           - On JSON parse failure: retry once; if still failing, return spaCy-only
             result and emit a warning. Never silently pass a bullet that could not
             be validated.

        3. Merge: union(spaCy_entities, llm_entities). LLM result takes precedence
           on any text-level conflict.
        """
        ...
```

### 3.3 Content/Layout Separation — Enforcement Pattern

The following pattern must be used in any code path that calls both the `SelectionAgent` and `HeuristicLoop`:

```python
# CORRECT — content resolution is separate from layout optimization
resolved = selection_agent.resolve(master, job_description)   # LLM calls happen here
artifact = heuristic_loop.run(resolved, config, tmp_dir)      # Zero LLM calls here

# WRONG — never pass job_description into HeuristicLoop
# heuristic_loop.run(master, job_description, config, ...)    # This must not exist
```

### Phase 3 — Success Gate

**`tests/test_phase3.py` must pass all of:**
1. `test_selection_agent_scores_all_items` — All items receive a `match_score` in `[0.0, 1.0]`.
2. `test_selection_agent_orders_by_score` — `resolved.experiences[0].match_score >= resolved.experiences[-1].match_score`.
3. `test_rephrasing_contains_jd_keywords` — At least one JD keyword appears in a rephrased bullet.
4. `test_grounding_guard_rejects_invented_metric` — Pass original: "Reduced latency by 30ms", rephrased: "Reduced latency by 80ms"; verify `is_valid=False`.
5. `test_grounding_guard_rejects_removed_company` — Remove a company name in rephrasing; verify rejection.
6. `test_grounding_guard_passes_valid_rephrase` — Synonym substitution with no entity changes; verify `is_valid=True`.
7. `test_grounding_fallback_keeps_original` — Mock guard to fail; verify `ResolvedContent` bullet equals original.
8. `test_layout_change_does_not_retrigger_llm` — Call `HeuristicLoop.run()` directly with pre-built `ResolvedContent`; verify zero LLM calls (mock LLM client and assert call count = 0).

**Do not proceed to Phase 4 until all 8 tests pass.**

---

## Phase 4: API & Persistence (The Scale)

**Goal:** A FastAPI service exposing the full pipeline, with file-based caching that skips Phase 3 for identical inputs, and a history layer that persists every run.

### 4.1 FastAPI Endpoints — `src/acte/api.py`

```python
# POST /generate
# Body: { master: MasterExperience, config: TailoredConfig, job_description: str | null }
# Behavior: Synchronous. Runs full pipeline. Returns PDF as application/pdf response.
# Use BackgroundTask only for cleanup; the main generation is synchronous here.

# POST /tailor
# Body: Same as /generate
# Behavior: Async. Enqueues job, returns { job_id: str, status: "queued" } immediately.
# Use FastAPI BackgroundTasks. Document the limitation: job state is in-process memory only.
# (A production upgrade to ARQ/Celery is noted as future work, not implemented here.)
# Error handling: wrap the ENTIRE background task body in try/except Exception.
#   On exception → set job state to "failed", store str(exc) in the job record's
#   error field. This guarantees GET /status/{job_id} never returns "queued"
#   indefinitely after an unhandled crash inside the background task.

# GET /status/{job_id}
# Returns: { job_id, status: "queued|running|complete|failed",
#            artifact_path: str | null, warnings: list[str], error: str | null }
# error is non-null only when status="failed". artifact_path is null when failed.

# GET /history
# Query params: limit (int, default 20, max 100), offset (int, default 0)
# Behavior: Scans output/history/ for completed run directories sorted by
#   timestamp descending (most recent first). Returns a paginated summary list.
# Response: { items: [{ job_id, timestamp, status, artifact_path, warnings }], total: int }
# Reads metadata from output/history/{timestamp}_{job_id}/action_log.json and
#   warnings.json. Returns { items: [], total: 0 } (not 404) when the directory
#   is empty or does not yet exist.

# GET /preview
# Query params: master_path, config_path (paths to files in output/)
# Behavior: Renders with default LayoutParams, no loop, returns first-page PNG.
# DEFERRED: PNG output is out of scope. Return a 501 Not Implemented with message
# "PNG preview not yet implemented" until explicitly re-scoped.
```

### 4.2 File-Based Cache — `src/acte/cache.py`

```python
class ContentCache:
    """
    Caches the output of SelectionAgent.resolve() keyed on a canonical hash.
    Cache hit → skip Phase 3 entirely, go directly to Phase 2.
    Cache stored as JSON files in output/cache/.

    Cache key = sha256(
        canonical_json(master)
        + canonical_json(job_description)
        + json.dumps(allow_rephrasing)    # MUST be included — see note below
    )

    IMPORTANT: allow_rephrasing MUST be part of the key. A cache entry produced
    with allow_rephrasing=False contains original (unrephrased) bullets. Serving
    that entry for an allow_rephrasing=True request would silently skip rephrasing
    and return stale content. The caller (api.py) must pass config.allow_rephrasing
    into every get() / set() call.

    canonical_json rules:
    - Sort all dict keys alphabetically (recursive)
    - Strip leading/trailing whitespace from all string values
    - Serialize with separators=(',', ':') (no extra whitespace)
    """

    def get(self, master: MasterExperience, jd: str, allow_rephrasing: bool) -> ResolvedContent | None:
        ...

    def set(self, master: MasterExperience, jd: str, allow_rephrasing: bool, resolved: ResolvedContent) -> None:
        ...

    def _cache_key(self, master: MasterExperience, jd: str, allow_rephrasing: bool) -> str:
        ...
```

### 4.3 History Layer

Every call to `POST /generate` or `POST /tailor` (on completion) must write to `output/history/{timestamp}_{job_id}/`:
- `master.json` — the input master experience list
- `config.json` — the input TailoredConfig
- `job_description.txt` — raw JD text
- `resume.pdf` — the output PDF
- `action_log.json` — the `GenerationArtifact.action_log`
- `warnings.json` — list of warnings emitted during generation

### Phase 4 — Success Gate

**`tests/test_phase4.py` must pass all of:**
1. `test_generate_endpoint_returns_pdf` — POST to `/generate` with valid payload; response content-type is `application/pdf`.
2. `test_tailor_endpoint_returns_job_id` — POST to `/tailor`; response contains `job_id`.
3. `test_status_endpoint_tracks_completion` — Poll `/status/{job_id}` until `status=complete`; verify `artifact_path` is set.
4. `test_preview_returns_501` — GET `/preview` returns HTTP 501.
5. `test_cache_hit_skips_llm` — Submit identical `/generate` twice; mock LLM client; assert LLM call count after second request equals count after first (cache served).
6. `test_cache_key_is_canonical` — Verify two `MasterExperience` objects with keys in different order produce the same cache key.
7. `test_history_files_written` — After `/generate`, verify all 6 history files exist in `output/history/`.
8. `test_cache_miss_on_different_jd` — Submit with JD "A", then JD "B"; verify LLM is called twice.
9. `test_status_transitions_to_failed_on_error` — Mock the pipeline to raise `RuntimeError` inside the `/tailor` background task; poll `/status/{job_id}` and assert `status="failed"` and `error` field is a non-empty string.
10. `test_history_endpoint_returns_list` — After two `/generate` calls, GET `/history`; verify response body contains `total=2` and items are sorted by timestamp descending.
11. `test_cache_key_includes_allow_rephrasing` — Call `_cache_key()` with `allow_rephrasing=False` and `allow_rephrasing=True` for an identical master + JD; assert the two keys differ.

---

## Cross-Cutting Constraints (Apply to All Phases)

These are non-negotiable invariants the coding agent must enforce across the entire codebase:

**1. The Interface Boundary is Sacred**
`HeuristicLoop.run()` signature must remain `(content: ResolvedContent, config: TailoredConfig, tmp_dir: Path) -> GenerationArtifact`. It must import nothing from `selection.py`, `grounding.py`, or any LLM library.

**2. Typst Escape Filter is Mandatory**
Every string value rendered into a `.typ` file must pass through `typst_escape()`. No exceptions. Use the `| te` Jinja2 filter. Add a test that deliberately passes `#`, `\`, and `"` through the full render pipeline.

**3. Temp Directory Lifecycle**
Every call to `Renderer.render()` must use a `tempfile.TemporaryDirectory()` context manager. No `.typ` or intermediate `.pdf` files may persist after `render()` returns, regardless of success or failure.

**4. `match_score` is Always Optional in Phase 1 & 2**
Any code path in the loop that reads `match_score` must handle `None`. The pruning score formula enforces this: if `match_score is None`, set `alpha_effective = 0.0`.

**5. No Silent Failures**
`TypstCompilationError` must always include the full stderr output from the Typst compiler. The loop must log (not swallow) every `NoOpAction` with its `reason` field populated.

**6. Action Log is Always Reproducible**
The invariant `reduce(apply_action, initial_state, action_log) == final_state` must hold. A test enforcing this must exist in `test_phase2.py` (test #7 above).

**7. PNG Output is Deferred**
Do not implement PNG rendering. Return HTTP 501 from the `/preview` endpoint. Do not add PNG-related code paths to `Renderer`.

---

## Appendix: Prompt Templates for Phase 3

These are the canonical LLM prompt templates. Do not alter them without updating the grounding tests.

**Scoring Prompt (system):**
```
You are a CV relevance scorer. You will receive a job description and a list of work experiences.
Score each experience on a scale from 0.0 to 1.0 based on how relevant it is to the job description.
1.0 = highly relevant, 0.0 = irrelevant.
Return ONLY a valid JSON object mapping experience ID to score. No explanation, no markdown.
```

**Rephrasing Prompt (system):**
```
You are a CV editor. You will receive a set of bullet points from a work experience and a job description.
Rewrite each bullet point to better highlight its relevance to the job description.
Rules you must follow:
1. Do NOT invent new metrics, percentages, or numbers that are not in the original.
2. Do NOT change the company name, job title, or employment dates.
3. Do NOT add new technologies or skills that are not mentioned in the original bullet.
4. Keep the same number of bullets as the input.
5. Return ONLY a valid JSON array of strings. No explanation, no markdown, no extra fields.
```

**Entity Extraction Prompt (system):**
```
Extract all named entities from the provided text.
Categories: COMPANY (organization names), DATE (any time expression), ROLE (job titles),
TECHNOLOGY (programming languages, frameworks, tools), METRIC (any number with unit or %).
Return ONLY a valid JSON array: [{"text": "...", "category": "..."}].
No explanation, no markdown.
```
