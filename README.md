# Task2View

Generate a **stakeholder- and task-guided architecture view** from a code repository.

Two inputs: a local repo (`--code`) and a free-text goal (`--goal`). One output: a viewpoint-selected view (JSON model + diagram). Catalogs follow **ISO/IEC/IEEE 42010** and **Views and Beyond**.

## Setup

Python 3.11+ and a key for at least one LLM provider.

```bash
cd code
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all-llms]"   # or .[dev,anthropic] / .[dev,openai]
cp .env.example .env               # put your keys in .env — never commit it
pytest
```

### Choosing the model

Every phase calls the model through one interface (`code/src/task2view/llm/`): one adapter per provider, picked from a `provider:model` spec.

| Provider | Spec example | Credentials |
|---|---|---|
| Gemini (default) | `gemini:gemini-2.5-flash` | `GEMINI_API_KEY` |
| Anthropic | `anthropic:claude-opus-5-5` | `ANTHROPIC_API_KEY` or `ant auth login` |
| OpenAI | `openai:<model>` | `OPENAI_API_KEY` |
| OpenRouter | `openrouter:<vendor>/<model>` | `OPENROUTER_API_KEY` |
| Ollama | `ollama:<model>` | `OLLAMA_BASE_URL` (default localhost:11434) |
| vLLM | `vllm:<served-model>` | `VLLM_BASE_URL` (default localhost:8000) |
| Any OpenAI-compatible server | `openai-compatible:<model>` | `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_API_KEY` |

Set it with `--llm`, with `llm:` in the run config, or with `TASK2VIEW_LLM`. Precedence is in that order. On Anthropic, `TASK2VIEW_LLM_EFFORT` sets the effort level (default `high`). Requests to Claude Opus 5.5 and the other current models opt into Anthropic's server-side refusal fallback.

Adding a provider means writing an `LLMClient` subclass with `complete_text` and registering it with `@register_provider`.

## Run

```bash
task2view run \
  --code /path/to/repo \
  --goal "I am a tester. I need to design integration tests for user registration and understand the components involved and how they interact." \
  --out runs/demo \
  --llm anthropic:claude-sonnet-4-5 \
  --judge-llm <another provider:model> \
  --notations plantuml,mermaid
```

The pipeline is ADR-006 (stages below). `--engine legacy` runs the pre-ADR-006 single-view pipeline with its scoper/extractor plug-ins.

Inspect individual stages without running the whole pipeline:

```bash
task2view card --code /path/to/repo                                   # Phase 0 repository card
task2view select-views --goal "..." --code /path/to/repo --llm ...    # Phase 1 + viewpoint selection
task2view plugins                                                     # notations, LLM providers, legacy plug-ins
```

Goal sets (any repositories; the pilot set is `code/tests/fixtures/pilot_goals.yaml`):

```bash
cd code
.venv/bin/python scripts/eval_view_selection.py --goals goals.yaml --llm ... --runs 3   # Phase 1 + selection only
.venv/bin/python scripts/run_goal_set.py --goals goals.yaml --out runs/eval --llm ... --judge-llm ...   # full runs
```

## What the pipeline does

Stage by stage: [`docs/architecture.md`](docs/architecture.md). Orchestrator: `code/src/task2view/agents/run_v2.py`.

```
goal ──► 1 needs, subjects, target (LLM, verified against the goal)
repo ──► 0 repository card: typed files, symbols, dependency graph, facts, signals (tree-sitter, no LLM)
         3 viewpoint selection: covering over 30 Views-and-Beyond viewpoints, cap 3 (no LLM)
         2 questions per selected view (no LLM)
         4 investigation tasks with suggested starting points (optional planning agent)
         5 evidence agents with repository tools ─► verified claims ─► Architecture Evidence Model
         6 per-view decision: confirm / simplify / request evidence / gap / drop (rules)
         7 deterministic projection to View format v2, rendered in 9 notations
         8 validation: notation, viewpoint constraints, faithfulness, coverage, task-fit judge (soft)
```

Every element in a view traces to code symbols and verified claims (`traceability.md`). Run-time limits: `code/src/task2view/knowledge/data/vb/pipeline.yaml`. Knowledge (needs, viewpoints, roles, corpus rules): `code/src/task2view/knowledge/data/vb/`.

## Output of a run

| File | Contents |
|---|---|
| `repository_card.json` / `.txt` | Phase 0 facts and signals |
| `stakeholder_profile.json` | Needs (primary/secondary), subjects, target, role, detail level |
| `view_plan.json` | Selected viewpoints with rationale, overlays, gaps |
| `architectural_questions.json` | Questions per view |
| `investigation_plan.json` | Tasks, starting points and their origin |
| `evidence_model.json` | Verified claims, rejected claims with reasons, elements, relations, scenarios |
| `reconciliation.json` | Coverage per question and the decision per view |
| `viewset.json`, `V*/view.json` | The views (format v2) and correspondences |
| `V*/view.puml` (+ other notations) | Diagram sources; images when `--skip-render` is not set |
| `validation_report.json` | Five-layer validation per view |
| `traceability.md`, `README.md`, `run.log` | Element → files/symbols; run summary; models used |

## Layout

```
code/src/task2view/phase1 … phase8   one package per diagram phase
code/src/task2view/phase0            corpus clean, before the eight phases
code/src/task2view/inputs            repository path and request id
code/src/task2view/agents            runtime, schemas, orchestrator
code/src/task2view/knowledge         catalogs and correspondence
code/tests/                          pytest
docs/architecture.md                 stage-by-stage description
docs/design-review-2026-10.md        root causes of the pilot failures, redesign proposal
docs/adr/                            decision log
skill/                               Task2View skill (single-agent baseline)
experiments/pilot-2026-09/           pilot: all three conditions' outputs, review, provenance
tools/                               GR10 UML-vs-code analysis scripts
data/                                English subject repositories (gitignored, local only)
```

## Tests

```bash
cd code && .venv/bin/pytest
```
