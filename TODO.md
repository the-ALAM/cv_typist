
# context
i need to apply for a wide range of jobs and i have a wide range of experiences which i want to tailor to each application
i wanna split it into two phases
first phase is to define the cv template and the config file which will be used to generate the cv under the defined constraints
second phase is to use genai to tailor the cv to the job description and create a tailored version as well as the first

# inputs
  - typst-defined cv template
  - yaml config file with the required experiences and constraints
  - a big list of all the experience i have as the source of experiences
  - upload linkdin job description
  - scan its requirements
  - pick and choose from previous experience and adjust accordingly

# outputs
  - image preview of the cv
  - cv pdf export

# constraints
  - should define constraints on the configs
  - like max number of pages, max length and width of the page
  - it has to be grounded on my experiences so i can't just add random experiences

# phases
  - cli based operation
    define the cv template and the config file which will be used to generate the cv under the defined constraints
  - ai integration
    genai to tailor the cv to the job description and create a tailored version as well as the first
  - api based operation
    hostable, api, just send a json with the config and get the cv back or be saved on my gdrive

# notes
for the The "Grounding" Strategy: the "Master Experience List" is a json/yaml file as is the config
for Typst Integration: i have a typist template that should be populated
The "Selection" Logic: rephrasing is configurable, i can set it to take bullet points as is or to rephrase based on a flag in the configs
for the Constraint Enforcement: we can start by changing the paddings to make it fit, if it wont, change the font size, and so on, so its a heuristics based approach
The Heuristic Adjustment Loop: To handle constraints without losing content, the agent should follow a specific priority order. This prevents the CV from looking "empty" or "cramped" unnecessarily.
  Step 1: Spacing. Reduce margin, row-gutter, and item-spacing.
  Step 2: Typography. Scale font-size down (e.g., from 11pt to a floor of 9pt).
  Step 3: Conditional Selection. If Step 1 & 2 fail, the agent can drop the lowest-ranked "Optional" (defined by the AI relevance score or a priority key in the YAML).
for State Management: In the "Heuristic Adjustment Loop," i want the system to run multiple Typst compilations and "check" the page count (feedback loop)
for The "Rephrase" Flag: If a flag is set to rephrase, the AI is tasked with shortening the text to help meet the constraints while maintaining the meaning
for the Templating approach: i wanna try a Python templating engine (like Jinja2) to write the .typ file before compilation for robustness
Data Ingestion: Load a Master Experience JSON/YAML and a Job Description (JD).
Data Layer: Pydantic models for MasterExperience, TailoredConfig, and ConstraintSettings.
AI Selection Engine: Map JD requirements to Master Experience entries.
Constraint Engine: Enforce a "Page Max" using a multi-step heuristic loop.
Compilation: Use typst-py to render the final PDF and a PNG preview.
Backend: FastAPI to handle the generation requests.
Processing: A "Selection Agent" (LLM) that outputs a filtered YAML based on the JD.
Rendering: typst-py to interface with the .typ template.
Validation: A post-render check on the PDF metadata to verify page count and pydantic for schema validation
Ranking: the AI assigns a numerical match_score to each experience during the selection phase to guide the pruning logic

each entry of a generation request is saved and tracked for later improvements including the JD, the passed configs, and the generated CV
Intelligence Layer: 
Filter experiences based on Job Description.
Rephrase bullets (if allow_rephrasing is true).
Assign priority/relevance scores.

Orchestration Layer: A heuristic loop that:
Compiles CV.
Inspects PDF page count via typst-py (or pypdf).
Adjusts layout_params (margins, font size, or content removal) until constraints are met.
Output Layer: FastAPI endpoints and CLI commands.

The Heuristic Loop Algorithm: Initial Render: Compile with default settings ($11pt$ font, standard margins).Constraint Check: Is actual_pages <= max_pages?Step A (Spacing): Reduce margin and gutter by $10\%$. Repeat up to 3 times.Step B (Typography): Decrement font_size by $0.5pt$ until min_font_size.Step C (Selection): Remove the experience with the lowest match_score.Loop: Re-run Step 1 until check passes.

i will need to create a jinja template that matches the .typ template

use of LLMs and AI is optional and should be configurable
use of API is optional and should be configurable
output location should be configurable (local, cloud)

# stack
python, typst-py, fastAPI, YAML/JSON (Source Data, Config), .typ (Template)

# examples

Master Experience (Source)
```yaml
experiences:
  - id: "exp_001"
    role: "Senior Dev"
    company: "Tech Corp"
    priority: 1 # Default importance
    bullets:
      - text: "Built a microservice..."
        keywords: ["python", "aws"]
```

Application Config (constraints)
```yaml
constraints:
  max_pages: 1
  min_font_size: 9pt
  allow_rephrasing: true
  heuristic_steps: ["spacing", "typography", "selection"]
```

# Implementation order:
Phase 1 (CLI): Implement the Pydantic models and a basic Jinja2 to Typst pipeline. Ensure the user can generate a CV from the CLI using only the master_experience and a manual config.yaml.
Phase 2 (Heuristics): Implement the HeuristicLoop. Use a while loop that checks the PDF page count and updates a LayoutParams object until the PDF length is $\le$ max_pages.
Phase 3 (AI): Add the SelectionAgent. It should take a string (Job Description) and the master_experience, returning a filtered list of Experience IDs with match_score and optionally rephrased text.
Phase 4 (API): Wrap the logic in FastAPI with an endpoint /generate that returns a FileResponse or uploads to a storage provider.

# TODO

- [ ] - theres a big misalignment here there should be a config, a master experience list, a job description list and the optional chosen experience items list. the master experience list has all i have done and the job description has the requirements of the job, and the config has the constraints and the flags, and the chosen experience items list is the output of the selection phase which is based on the master experience list.

- [ ] - add to phase 3 an agentic component that reviews the generated template and decide on the best heuristic adjustment to make based on the constraints and the content of the CV, instead of following a fixed order of adjustments. 
For example, if the CV is just slightly over the page limit, it might choose to rephrase a few bullets instead of reducing font size or margins, which could make the CV look cramped.
and also make it directly edit the template to remove or rephrase content instead of just outputting a filtered list of experience IDs. This way, the AI can make more nuanced adjustments to the CV content while ensuring it meets the constraints.
