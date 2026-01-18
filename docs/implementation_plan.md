
# System Specification: Agentic CV Tailoring Engine (ACTE)

## 1. Project Overview

Build a Python-based system that generates highly configurable CVs using **Typst** and **Jinja2**. The system selects experiences from a "Master List," applies AI-driven tailoring based on a Job Description (JD), and enforces strict physical constraints (page count) via a heuristic feedback loop.

### Tech Stack

* **Core:** Python 3.10+
* **Typesetting:** Typst (via `typst-py`)
* **Templating:** Jinja2
* **Schema/Validation:** Pydantic v2
* **API:** FastAPI
* **AI:** LangChain or LiteLLM (for JD mapping and rephrasing)

---

## 2. Data Models (Pydantic)

Implement the following schemas to ensure data integrity:

* **`ExperienceItem`**: ID, Role, Company, Date, Bullets (List of strings), Keywords, Priority.
* **`MasterExperience`**: A collection of `ExperienceItem` objects.
* **`LayoutParams`**: Margin, Gutter, Font Size (pt), Item Spacing.
* **`TailoredConfig`**: `max_pages`, `min_font_size`, `allow_rephrasing`, `output_format` (PDF/PNG).
* **`GenerationState`**: Tracks current layout params and current page count during the heuristic loop.

---

## 3. The Heuristic Adjustment Loop

This is the core logic. The agent must implement a controller that follows this specific order to fit the CV into `max_pages`:

1. **Initial Render**: Compile `.typ` via Jinja2 with default `LayoutParams`.
2. **Page Check**: Use `typst-py` or `pypdf` to inspect the page count.
3. **Step A (Spacing)**: Reduce `margin` and `row-gutter` by  (up to 3 iterations).
4. **Step B (Typography)**: Reduce `font_size` by  increments (floor: `min_font_size`).
5. **Step C (Pruning)**: Remove the `ExperienceItem` with the lowest `match_score` (provided by AI) or `priority`.
6. **Loop**: Re-render and repeat until `actual_pages <= max_pages`.

---

## 4. AI Selection Engine (Optional/Configurable)

The agent should implement a `SelectionAgent` class:

* **Input**: `MasterExperience` + `JobDescription` (text/markdown).
* **Logic**:
1. Rank experiences by relevance to the JD ( to ).
2. If `allow_rephrasing` is True, rewrite bullet points to highlight JD keywords while maintaining grounding (no hallucinating new roles).


* **Output**: A filtered and ranked list of IDs and modified bullets.

---

## 5. Implementation Roadmap

### Phase 1: CLI & Templating (The Foundation)

* Setup Jinja2 to render `.typ` files.
* Implement `typst-py` wrapper to compile PDF/PNG.
* Create a CLI command: `generate --master master.yaml --config config.yaml`.

### Phase 2: The Constraint Engine (The Brain)

* Implement the `HeuristicLoop` controller.
* Add logic to parse PDF metadata to get page counts.
* Ensure layout parameters in the `.typ` file are variables passed from Python.

### Phase 3: AI Integration (The Intelligence)

* Integrate an LLM provider to handle the "Selection" and "Rephrasing" logic.
* Ensure the system remains "Grounded": the AI can only edit existing bullets, not invent new jobs.

### Phase 4: API & Persistence (The Scale)

* Create FastAPI endpoints for `/generate` and `/preview`.
* Implement a "History" layer: save every JD, Config, and Resulting PDF to a local `outputs/` folder or cloud storage.

---

## 6. Template Snippet (Typst + Jinja2)

Provide this to the agent as a starting point for `template.typ.j2`:

```typst
#set page(
  margin: {{ layout.margin }}pt,
  width: 210mm,
  height: 297mm,
)
#set text(size: {{ layout.font_size }}pt)

#let experience(role, company, bullets) = {
  block(below: {{ layout.gutter }}pt)[
    *#role* --- #company
    #for b in bullets [
      - #b
    ]
  ]
}

{% for exp in selected_experiences %}
experience("{{ exp.role }}", "{{ exp.company }}", {{ exp.bullets }})
{% endfor %}

```

---

## 7. Coding Agent Execution Instructions

1. **Scaffold** the Pydantic models first and the jinja template generation.
2. **Create** a "Dummy" Typst compiler that just produces a 2-page PDF following the template and populated from the config so you can test the **Heuristic Loop** logic without an LLM.
3. **Implement** the loop logic to successfully "shrink" that 2-page PDF into the desired constraints mentioned in the config by adjusting parameters.
4. **Once the loop works**, integrate the LLM for selection and rephrasing.
5. **Finally**, wrap it in FastAPI and implement the history layer.

i need this to be a step by step process where at the end of each phase there is a clear testable output i can build upon in the next phase
