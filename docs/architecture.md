# Current pipeline

![Current architecture](diagrams/architecture.svg)

Source: [`diagrams/architecture.dot`](diagrams/architecture.dot).

Two inputs: a code repository (`--code`) and a stakeholder goal (`--goal`). Output: one catalog viewpoint’s view (notation-neutral `ViewModel` + diagram).

Grounding: **ISO/IEC/IEEE 42010** (stakeholders, concerns, viewpoints, views) and **Views and Beyond** YAML under `code/src/task2view/knowledge/data/`.

The reusable contract is correspondence, not a diagram kind:

**stakeholder × concerns × task → catalog viewpoint → published grain → extract / gate / draw**

## Stages

| Stage | Code | LLM? | What it consumes |
|---|---|---|---|
| 0 clean | `phase0/clean.py` | no | Repo files; keeps source, drops binaries |
| 1 interpret | `agents/phase1_interpret.py` | yes | Goal + stakeholder catalog |
| correspondence | `knowledge/correspondence.py` | no | Role × concerns × task cues → viewpoint + `published_grain` |
| 2 questions | `agents/phase2_questions.py` | yes | Profile + grain of the **selected** viewpoint |
| 3 viewpoint | `agents/phase3_viewpoint.py` | yes | Ranked catalog candidates only; cannot invent a diagram kind |
| spec + RI | `knowledge/correspondence.py` | no | Instantiates `required_information.yaml` |
| graph | `phase3/graph.py` | no | uses / calls / parent directory among cleaned files |
| scoper | `phase3/` + `phase3/seeds.py` | no | Default `composite`. PageRank can force RI-matched files, then fill |
| extract | `phase4/extractors.py` | yes | `VIEWPOINT GRAIN` from the correspondence. Default `gemini`; `ciao` packs scoped files |
| project | `agents/structure.py` | no | Grounds evidence; unit from grain. Context: actors and the system |
| critic | `agents/phase6_critic.py` | yes | Notes only. Does not add class neighbours. `--skip-critic` |
| gate + render | `phase4/validate.py`, `render.py` | no | Drops unsupported boxes; keeps published names; emits notation |
| compile | `phase4/compile.py` | no | Kroki (or local fallback) → SVG/PNG/JPEG |

Default orchestrator: `agents/orchestrate.py` `run_agentic`. Gemini agents on that path: interpret, questions, viewpoint, extractor, critic. They call `complete_json` only — no repository tool loop. Correspondence itself is not an LLM.

`--legacy` skips agents 1–3 and uses regex intake, then the **same** correspondence kernel (`identify_view`).

## Correspondence and grain

`select_correspondence` ranks every catalog viewpoint the stakeholder may use (V&B Table 9.1 ∪ profile required/optional ∪ task-cue preferences). Cue **weights** let persistence, deployment, security, and context outrank a generic “modify”.

The winner binds one row of `published_grain` in `view_projection.yaml`. That row is what questions, purpose, extractors, `apply_facts`, and the gate must obey.

| If the goal looks like… | Viewpoint | Grain `unit` | What the view may be |
|---|---|---|---|
| who talks to this system? | `context` | context | actors + system + externals |
| where do I change X? | `module-decomposition` / `module-uses` | component | subsystems and uses — not every class |
| how is a request processed? | `scenario` / `control-flow` | component | a few participants and ordered calls |
| what is stored? | `data-model` | type | persistent entities |
| where does it run? | `allocation-deployment` | component | artifacts, nodes, datastores |
| attack surface / trust | `trust-boundary` | component | entry points and zone crossings |
| I’m new here | `onboarding-path` | component | entry + largest subsystems |

Quality attributes are concerns on the stakeholder profile, boosted by `task_cues.yaml`, then framed by `viewpoints.yaml` (`frames_concerns`). Security does not become a component dump; it prefers `trust-boundary`.

Adding a stakeholder or concern is catalog work: a row in stakeholders / cues / viewpoints plus a `published_grain` row. Extractor code does not get a new special case.

## Graph and projection

- Graph node = kept file (stem key; path aliases). Language-neutral (ADR-004 D1).
- Extractor, questions, and viewpoint purpose consume `VIEWPOINT GRAIN`. A tester scenario stays at component participants + ordered calls; a DBA data-model may name entities; a context view is actors + system.
- Gate keeps published names. Structure adds uses among owner files when unit is component; type-level edges only when unit is type. No folder-lift, no dumping the class graph unless the grain says type.

## Config

`code/pipeline.example.yaml` selects `scoper` / `extractor` / `diagram_language`. CLI flags override.

Typical evaluation command (PageRank scope + CIAO extract):

```bash
task2view run --code /path/to/repo --goal "…" --out runs/demo \
  --scope-strategy pagerank --extract-backend ciao
```

## Architecture decisions

| ADR | Status |
|---|---|
| [ADR-001](adr/ADR-001-agentic-realignment.md) | accepted (extract D5–D7 superseded) |
| [ADR-002](adr/ADR-002-sota-plugins.md) | accepted |
| [ADR-003](adr/ADR-003-structure-grounding.md) | superseded in part by ADR-004 |
| [ADR-004](adr/ADR-004-filesystem-graph-and-config.md) | accepted (D2 grouping superseded by ADR-005) |
| [ADR-005](adr/ADR-005-correspondence-and-published-grain.md) | accepted |
