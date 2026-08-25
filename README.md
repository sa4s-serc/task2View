# Task2View

Generate a **stakeholder- and task-guided architecture view** from a code repository.

Two inputs: a local repo (`--code`) and a free-text goal (`--goal`). One output: a viewpoint-selected view (JSON model + diagram). Catalogs follow **ISO/IEC/IEEE 42010** and **Views and Beyond**.

## Setup

Python 3.11+ and a [Google AI Studio](https://aistudio.google.com/apikey) key.

```bash
cd code
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # put GEMINI_API_KEY in .env — never commit it
pytest
```

Optional: `GEMINI_MODEL=gemini-2.5-flash` (default).

## Run

```bash
task2view run \
  --code /path/to/repo \
  --goal "I am a software developer. I need to modify the seat booking functionality and understand the main components involved." \
  --out runs/demo
```

Swap analysis plug-ins without changing the rest of the pipeline:

```bash
task2view run --code /path/to/repo --goal "..." --out runs/demo \
  --scope-strategy pagerank \
  --extract-backend ciao \
  --diagram-language plantuml
```

`--config pipeline.example.yaml` sets the same fields; CLI flags override.

```bash
task2view plugins          # list scopers, extractors, notations
task2view compile --run-dir runs/demo
```

Example goals for the two evaluation repos: [`input_example_task2view.txt`](input_example_task2view.txt). Batch runner:

```bash
cd code
.venv/bin/python scripts/run_input_examples.py \
  --out-dir demo-batch \
  --scope-strategy pagerank \
  --extract-backend ciao \
  --diagram-language plantuml
```

Generated artifacts go to `code/runs/` (gitignored).

## What the pipeline does

Default path is `run_agentic` in `code/src/task2view/agents/orchestrate.py`.

```
goal + code
    │
    ├─► 0 clean          keep source files, drop binaries / UML dumps
    ├─► 1 interpret      Gemini → stakeholder-task profile
    ├─► 2 questions      Gemini → architectural questions
    ├─► 3 viewpoint      Gemini → catalog viewpoint (never invents an id)
    ├─► instantiate RI   required_information.yaml for that viewpoint
    ├─► filesystem graph uses / calls / parent directory
    ├─► scoper           default composite; pagerank + RI-forced seeds is the usual experiment
    ├─► extractor        default gemini; ciao packs scoped files with the CIAO prompt
    ├─► project          directory groups, inter-package edges, view-type caps
    ├─► critic           optional Gemini completeness pass (cap 4 extra types)
    ├─► adapter + gate   PlantUML / Mermaid / … then drop invented types
    └─► compile          SVG / PNG / JPEG
```

`--legacy` skips agents 1–3 and uses regex intake. `--skip-critic` skips only the critic. `--skip-extract` stops after scoping.

## Plug-ins

| Kind | Default | Others |
|---|---|---|
| Scoper | `composite` | `pagerank`, `graph1`, `locagent`, `central`, `layer`, `grep`, `lexical`, `dataflow`, `full` |
| Extractor | `gemini` | `ciao`, `archagent` |
| Notation | viewpoint / goal / config | `plantuml`, `mermaid`, `d2`, `c4plantuml`, `structurizr`, `graphviz`, `nomnoml`, `excalidraw`, `bpmn` |

PageRank scoping can **force up to 8 files** from required-information cues (IDF-filtered so common tokens do not swallow the repo), then fills to 16 with PageRank.

## Knowledge and tools

Static knowledge is YAML under `code/src/task2view/knowledge/data/` (stakeholders, viewpoints, required information, task cues, view projection, CIAO prompt). It is loaded every run.

Live Gemini agents do **not** call repository tools. Each call is one JSON completion with evidence stuffed into the prompt (catalog text, scoped file bodies, graph summary). `RepoTools` (`list_tree`, `search`, `read`, `graph_query`, …) exists on `AgentRuntime.tool_loop` but is unused on the default path.

There is no vector store and no memory across runs. `code/runs/` is write-only output.

## Output of a run

| File | Contents |
|---|---|
| `stakeholder_task_profile.json` | Interpreted role, task, target |
| `architectural_questions.json` | Questions the view should answer |
| `viewpoint_plan.json` | Chosen catalog viewpoint |
| `view_specification.json` | Viewpoint + required information |
| `repository_scope.json` | Files the scoper kept |
| `view_model.json` | Elements, relations, groups |
| `architecture_view.puml` (or `.mmd`, …) | Diagram source |
| `architecture_view.svg` / `.png` | Compiled image |
| `structure_report.json` | Grounding / critic notes |
| `validation_report.json` | Semantic gate |

## Layout

```
code/src/task2view/   pipeline, agents, knowledge, CLI
code/tests/           pytest
code/scripts/         batch runner + compile helper
docs/architecture.md  stage-by-stage description
docs/adr/             design decisions ADR-001 … ADR-004
input_example_task2view.txt
```

## Tests

```bash
cd code && .venv/bin/pytest
```
