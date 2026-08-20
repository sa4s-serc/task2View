# Task2View code

Default path is in [ADR-002](../docs/architecture-decisions/ADR-002-sota-plugins.md): agents for stakeholder/task/viewpoint, then **plug-in** scoping, extraction, and notation.

Two inputs: a **code** repository and a **natural-language** stakeholder/task description.

| Stage | What it does | Model? |
|---|---|---|
| 0 | Keep source files; drop binaries/UML dumps | No |
| 1 | Interpretation agent → stakeholder-task profile | Gemini |
| 2 | Question agent → architectural questions | Gemini |
| 3 | Viewpoint-planning agent + YAML knowledge base | Gemini |
| 4 | **Scoper** plug-in (`--scope-strategy`, default `composite`) | No |
| 5 | **Extractor** plug-in (`--extract-backend`, default `gemini`) | Gemini |
| 7 | **NotationAdapter** (`--diagram-language`) | No |
| 8 | Semantic gate vs the Java graph + diagram syntax | No |

`--legacy` skips the three agents and uses regex Phase 1–2. Same scoper/extractor/adapter catalogs.

`task2view plugins` lists registered names.

## Setup

```bash
cd code
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Needs a free Google AI Studio key: https://aistudio.google.com/apikey

```bash
export GEMINI_API_KEY=your_key
# optional: GEMINI_MODEL=gemini-2.5-flash
```

## Run

```bash
task2view run \
  --code ../../data_points/Progetto-IS-main-English \
  --goal "I am a software developer. I need to modify the seat booking functionality and understand the main system components involved and how they interact." \
  --out runs/REQ-IS-002
```

Swap plug-ins without changing the rest of the pipeline:

```bash
task2view run --code ... --goal "..." --out runs/ablation \
  --scope-strategy locagent \
  --extract-backend archagent \
  --diagram-language mermaid
```

`--skip-extract` stops after scoping. `--legacy` uses regex intake.

Artifacts:

- `stakeholder_task_profile.json`
- `architectural_questions.json`
- `viewpoint_plan.json`
- `view_specification.json`
- `repository_scope.json`
- `view_model.json`
- `architecture_view.<ext>` (`.puml`, `.mmd`, `.d2`, `.dot`, `.dsl`, `.nomnoml`, `.excalidraw.json`, `.bpmn`)
- `architecture_view.svg` / `.png` / `.jpeg` (compiled via Kroki; override with `KROKI_URL` or `--kroki-url`)
- `render_report.json`
- `validation_report.json`

`--skip-render` writes source only. Re-compile an existing run:

```bash
task2view compile --run-dir runs/REQ-IS-001
task2view compile --run-dir runs/ablations-progetto-is/G3-detailed/composite-gemini --all-notations
task2view compile --source runs/REQ-IS-001/architecture_view.puml --formats svg,png,jpeg
```
