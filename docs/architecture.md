# Pipeline and research-plan phases

![Task2View eight research-plan phases](diagrams/architecture.svg)

Source: [`diagrams/architecture.dot`](diagrams/architecture.dot) · raster: [`diagrams/architecture.png`](diagrams/architecture.png).

This is the **same pipeline** as the research plan *From Stakeholder Tasks to Architecture Views* (Figure 1). The boxes keep the plan’s eight phase names. The second line in each box is what `run_agentic` actually runs today.

Two inputs: `--goal` (free-text stakeholder/task) and `--code` (repository). One output: a viewpoint-selected view (`view_model.json` + diagram).

## Plan phase → current implementation

| Plan | What the plan specified | What runs today | Artifact |
|---|---|---|---|
| **1** Stakeholder-Task Interpretation | Interpretation Agent | Gemini interpret agent; role checked against `aliases.yaml` | `stakeholder_task_profile.json` |
| **2** Concern and Architectural Questions | Question Agent | Gemini questions agent, seeded from the **selected** viewpoint’s required-information templates | `architectural_questions.json` |
| **3** Knowledge-Grounded Viewpoint Planning | Viewpoint agent + knowledge base | Catalog ranks viewpoints from role × concerns × task cues (no LLM), then the viewpoint agent may only confirm a ranked id | `viewpoint_plan.json`, `view_specification.json` |
| **4** Repository Analysis | Analysis plan: where to look | Drop binaries; file graph (uses/calls); scoper plug-in (`composite`, `pagerank`, …) | `repository_scope.json` |
| **5** Evidence Extraction and Grounding | Extraction agents → evidence model | Extractor plug-in (`gemini`, `ciao`, `archagent`) over scoped files; claims grounded to paths | `view_model.json` |
| **6** Need–Evidence Reconciliation | Rewrite the plan if evidence is missing | Critic writes notes only; it does not change the viewpoint | `structure_report.json` |
| **7** Specialized View Generation | Per-view generators | Notation adapter (`plantuml`, `mermaid`, …) | `architecture_view.puml` |
| **8** Validation and Consistency | Validation agent | Semantic gate (names need evidence) + compile | `validation_report.json`, SVG/PNG/JPEG |

Default orchestrator: `agents/orchestrate.py`. `--legacy` skips the Phase 1–3 agents and uses regex intake, then the same catalog rank. `--skip-extract` stops after Phase 4. `--skip-critic` skips only Phase 6.

Phase 4 and Phase 5 stay separate on purpose: the scoper is the analysis plan (candidate files); the extractor is the only stage that claims what the architecture contains.

Typical evaluation command:

```bash
task2view run --code /path/to/repo --goal "…" --out runs/demo \
  --scope-strategy pagerank --extract-backend ciao
```

## What the current runs get right — and what they get wrong

On `pagerank` + `ciao` against the two evaluation repos, **viewpoint choice is often right** and **the drawn boxes are often wrong**.

| Goal | Viewpoint chosen | What was drawn | Problem |
|---|---|---|---|
| Tester L1 (registration) | scenario | LibraryFacade, UserManager, UserRegistry, … | This is the one that looks like a view |
| Tester L2 / L3 | module-decomposition / module-uses | L2: `boundary`, `controller`, `dto`, `entity`. L3: 17 boxes / 50 edges | “main components involved” in the goal text beats “integration test”; L3 dumps classes |
| Developer seat L1–L3 | module-decomposition | `Boundary` / `Controller` / `DTO` / `Entity` (packages) | Goal asked for booking, availability, rules, reservations, notification — those types exist (`ReservationManager`, `LibraryFacade`) and were not used as names |
| Architect GR10-Q1 | module-decomposition | Boundary / Control / Database / Entity subsystems | Same package-lift, one lonely edge |
| DevOps GR10-Q2 | allocation-deployment | app container + database | Right kind of view; too thin |
| DBA GR10-Q3 | data-model | Citizen, Report, Location, … | Right kind of view |
| Analyst GR10-Q4 | context | Citizen, Municipal Operator, **Boundary**, Database | System named after a package |

The critic on seat L3 then **endorsed** the package boxes as fully answering “top-level modules and their responsibilities”. Phase 6 is not catching the failure.

So the pipeline shape is the research plan. The remaining defect is not “we picked the wrong diagram kind for DBA/DevOps”. It is: **when the viewpoint is a module view, Phase 5 still publishes folder names, and Phase 6 believes them.**

## What to do next

Items 1–4 below are now in the code (catalog rank, allowed names, folder rebuild, uses arrows, cap, context rename). Remaining:

- **Phase 4** still keeps 16 PageRank files. Force files matching the goal nouns (booking, reservation, registration, notification) before centrality fill.
- **Phase 6** can still praise a weak view. Fail leftover package-shaped names and re-extract once.
- **Deployment views** are still thin (app + database). Seed from Docker/compose/SQL as well as Java.

## Which view for which task

The knowledge base maps stakeholder, task, and concerns to a viewpoint (Phase 3). Examples:

| If the goal looks like… | Viewpoint | What the view should show |
|---|---|---|
| who talks to this system? | context | actors, the system, externals |
| where do I change X? | module decomposition / uses | subsystems named by **responsibility**, and uses |
| how is a request processed? | scenario / control flow | participants and ordered interactions |
| what is stored? | data model | persistent entities |
| where does it run? | allocation / deployment | artifacts, nodes, datastores |
| attack surface / trust | trust boundary | entry points and zone crossings |
| I’m new here | onboarding path | entry and main subsystems |

Adding a stakeholder or concern is catalog work under `code/src/task2view/knowledge/data/`.

## Architecture decisions

| ADR | Status |
|---|---|
| [ADR-001](adr/ADR-001-agentic-realignment.md) | accepted (extract D5–D7 superseded) |
| [ADR-002](adr/ADR-002-sota-plugins.md) | accepted |
| [ADR-003](adr/ADR-003-structure-grounding.md) | superseded in part by ADR-004 |
| [ADR-004](adr/ADR-004-filesystem-graph-and-config.md) | accepted (D2 grouping superseded by ADR-005) |
| [ADR-005](adr/ADR-005-correspondence-and-published-grain.md) | accepted |
