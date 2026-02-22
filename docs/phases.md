# Agentic CV Tailoring Engine (ACTE): Implementation Phases

To implement the **Agentic CV Tailoring Engine (ACTE)**, we will follow a modular "Inside-Out" approach. This ensures the core layout and constraint logic is stable before we introduce the non-deterministic nature of AI.

---

### Phase 1: CLI & Templating (The Foundation)

**Goal:** Establish a reliable pipeline to turn Python data into a PDF via Typst and provide a functional CLI.

1.  **Environment Setup:**
    *   Install `typst` (CLI) and `typst-py`.
    *   Create a directory structure: `/templates`, `/data`, `/output`, `/src`.

2.  **Define Pydantic Models:**
    *   Create `models.py` containing `ExperienceItem`, `MasterExperience`, `LayoutParams`, and `TailoredConfig`.
    *   Implement `GenerationState` to track current layout params and page counts during the loop.

3.  **Jinja2 Template Creation:**
    *   Build `template.typ.j2`. Use variables for all dimensions: `margin`, `font_size`, `gutter`, and `item_spacing`.
    *   Use Typst's `block(breakable: false)` to ensure logical units (like an entire experience) stay together.

4.  **The Compiler Wrapper & CLI:**
    *   Write a `Renderer` class that handles `typst-py` compilation logic.
    *   Implement a CLI: `generate --master master.yaml --config config.yaml` to produce a fixed-format PDF.
    *   Add a **Diff-Check** on major entities (dates, titles, tech stack) to ensure rendering integrity.

5.  **Validation:**
    *   **Test:** Run the CLI with a `master.json` to produce a `resume.pdf`.
    *   **Success Metric:** A readable PDF appears in `/output` that accurately reflects the input data.

---

### Phase 2: The Constraint Engine (The Brain)

**Goal:** Automate the "shrink to fit" logic using a heuristic feedback loop.

1.  **The Page Inspector:**
    *   Implement a helper that parses PDF metadata (via `pypdf` or `typst-py`) to get accurate page counts.

2.  **The Heuristic Adjustment Loop:**
    *   Create a controller that iterates in this specific order to fit into `max_pages`:
        *   **Step A (Spacing):** Reduce `margin` and `row-gutter` (up to 3 iterations).
        *   **Step B (Typography):** Reduce `font_size` using a **Binary Search** approach ($10pt \to 9pt \to 9.5pt$) down to `min_font_size`.
        *   **Step C (Pruning):** Remove the `ExperienceItem` with the lowest `priority` or `match_score`.
    *   Enforce a **Minimum Readability** threshold to prevent the font from getting too small.

3.  **Validation:**
    *   **Test:** Input a large `MasterExperience` with a `max_pages: 1` limit.
    *   **Success Metric:** The engine successfully "shrinks" the output by adjusting spacing/font and finally pruning items until `actual_pages <= max_pages`.

---

### Phase 3: AI Integration (The Intelligence)

**Goal:** Use an LLM to select and rephrase content based on a Job Description (JD).

1.  **The Selection Agent:**
    *   Implement a `SelectionAgent` that ranks `ExperienceItem`s by relevance to the JD (0.0 to 1.0).
    *   **Content vs. Layout Separation:** Ensure that tweaking a margin does *not* re-trigger the LLM.

2.  **Tailoring & Rephrasing:**
    *   If `allow_rephrasing` is True, rewrite bullet points to highlight JD keywords.
    *   **Grounding Guardrail:** Ensure the AI only edits existing bullets; if it invents new roles or companies, the change is rejected.

3.  **Validation:**
    *   **Test:** Pass a specific JD and check if the most relevant experiences are selected and rewritten with JD keywords.
    *   **Success Metric:** The output CV is qualitatively better matched to the JD while remaining strictly grounded in the original facts.

---

### Phase 4: API & Persistence (The Scale)

**Goal:** Package the engine as a scalable service with historical tracking.

1.  **FastAPI Implementation:**
    *   Implement endpoints:
        *   `POST /generate`: Full tailoring flow.
        *   `POST /tailor`: Long-running tailoring task.
        *   `GET /status/{id}`: Check status of a tailoring job.
        *   `GET /preview`: Quick render of current state.

2.  **Persistence & Caching:**
    *   **History Layer:** Save every JD, Config, and Resulting PDF to an `outputs/` folder.
    *   **File-Based Cache:** Hash the JD and Master List; if they haven't changed, skip Phase 3 and go straight to Phase 2 (Layout Optimization).

3.  **Debug Features:**
    *   Add a **Debug PDF** mode that highlights AI-rewritten text in a different color.

4.  **Validation:**
    *   **Test:** Perform an end-to-end request via the API and verify the cache hits on repeated identical requests.
    *   **Success Metric:** A production-ready API that handles the full CV generation lifecycle efficiently.

---

### Summary Checklist for Implementation

| Phase | Core Component | Test Case |
| --- | --- | --- |
| **1** | CLI & Typst | Does `generate --master ...` create a valid PDF? |
| **2** | Heuristic Loop | Does it prune items to fit Exactly 1 page? |
| **3** | AI Selection | Are bullets rewritten to match JD keywords? |
| **4** | API & Cache | Does the cache skip LLM calls for identical JDs? |

