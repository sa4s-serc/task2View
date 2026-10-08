---
name: task2view
description: Generate one ISO 42010 / Views-and-Beyond architecture view from a local repository and a free-text stakeholder goal. Use when the user says Task2View, architecture view, viewpoint, stakeholder goal, or asks for a single-agent baseline comparable to the Task2View multi-agent pipeline. Do not use for general code review, refactoring, or implementing features.
---

# Task2View (single-agent baseline)

You are **one agent** that produces the same artifacts as the Task2View multi-agent pipeline. This run is the single-agent baseline for comparison.

## Hard rules

- Do **not** run `task2view`, `python -m task2view`, or any multi-agent orchestrator.
- Do **not** invent types, actors, nodes, or services that are not in the repository.
- Use only catalog `viewpoint_id` values from [knowledge/viewpoints.yaml](knowledge/viewpoints.yaml).
- Write every artifact under `--out` before stopping. If the user gives no `--out`, use `./runs/single-agent/<run-id>`.
- Read [references/output-schema.md](references/output-schema.md) before writing JSON.
- Read [references/quality-rules.md](references/quality-rules.md) before publishing `view_model.json`.
- Read [knowledge/viewpoints.yaml](knowledge/viewpoints.yaml) and [knowledge/view_projection.yaml](knowledge/view_projection.yaml) when choosing a view, then again when extracting. Id list: [references/catalogs.md](references/catalogs.md).

## Inputs

The user provides:

| Field | Meaning |
|---|---|
| `--code` / repository | Local path of the system under analysis |
| `--goal` | Free-text stakeholder + task (ISO 42010 request) |
| `--out` | Output directory |
| `--run-id` | Optional id for `request_id` (e.g. `IS-seat-L1`) |

If a field is missing, ask once, then proceed.

Evaluation goals: [references/examples.md](references/examples.md).

## Workflow

Work the eight research-plan phases **in this order**. It matches `run_agentic`: interpret, choose a viewpoint from the concerns, bind that viewpoint's grain, then write questions at that grain. You do all of them yourself. Do not open the repository until phase 4.

### 1. Stakeholder-Task Interpretation

Map the goal onto a catalog role using [knowledge/aliases.yaml](knowledge/aliases.yaml) and [knowledge/stakeholders.yaml](knowledge/stakeholders.yaml).

Write `stakeholder_task_profile.json`:

- `stakeholder`: the canonical role id when one resolves, otherwise the words the user used
- `original_label`: the words the user used for themselves
- `canonical_role`: one catalog id (`developer` → `member-of-development-team`, `integration tester` → `tester-and-integrator`, `software architect` → `current-and-future-architect`, `devops engineer` → `infrastructure-support-personnel`, `database engineer` → `analyst`, `business analyst` → `customer`). Use null only when the statement names no role and the work fits none. If the label is unmapped but a role is required to continue, use `member-of-development-team`.
- `task`: the work they will do, not a copy of the whole statement
- `target`: a short noun phrase from their words (the feature or subsystem)
- `goal`: one sentence, what the diagram must make visible
- `scope`: a bound they actually stated, else `""`
- `constraints`: limits they actually stated, else `[]`
- `concerns`: catalog concern ids **this statement raises**, and no others. Do not copy every concern on the role. Include a concern no viewpoint frames when the statement really raises it. Drop ids that are not in the catalog. If none remain, keep only the role's highest-priority concern.
- `source_goal`: the original goal text verbatim

### 2. Viewpoint choice

Do **not** open the repository yet. Do **not** write the architectural questions yet.

Build the allowed list from [knowledge/viewpoints.yaml](knowledge/viewpoints.yaml):

- Keep viewpoints whose `frames_concerns` overlap the concerns from phase 1. Sort by how many of those concerns they frame.
- If none overlap, the allowed list is the full catalog. Say that in `viewpoint_plan.json` notes.

Choose **one** `viewpoint_id` from that allowed list. Read `nodes`, `relations`, and `forbid` in [knowledge/view_projection.yaml](knowledge/view_projection.yaml). Pick the id whose nodes are what this stakeholder must look at. Do not pick an id because it is first, and do not pick a component diagram for every stakeholder.

The choice wins. Do not retarget it afterward from keywords, questions, or task-cue scores. `decided_by` is `model`.

Write `correspondence.json` and `viewpoint_plan.json`.

`correspondence.json`: winner, `task_focus`, `decided_by` = `model`, `grain` copied from the published grain of that id, `unanswered_concerns` = chosen concerns that id does not frame. `purpose` is the catalog sentence: `{viewpoint name} for {task focus}: {nodes}. Relations: {relations}. Do not: {forbid}.`

`viewpoint_plan.json`:

- Exactly **one** view, `"deferred": false`. Do not add deferred runner-ups.
- `addresses` is `[]`. Questions are written in the next phase.
- `purpose` is one sentence using the winner's nodes. It must not ask for what its `forbid` line denies. A module view must not talk about classes. A C&C runtime view talks about runtime components and connectors. If the purpose mentions classes and the grain unit is not `type`, replace it with the catalog sentence above.
- `notes` start with the allowed ids. If no viewpoint framed the concerns, the first note says the full catalog was offered.

### 3. Architectural questions at that grain

Now write the questions. A viewpoint is already selected. Every question stays at its grain.

Write 3–6 `AQ*` questions. Fewer is better when the task is narrow. Each question is one fact the diagram must show. It names the target. It asks for something the grain allows as a box or a relation. It is not a restatement of the whole goal.

- Seed from the winner's required-information templates in [knowledge/required_information.yaml](knowledge/required_information.yaml), rewritten to this target. Do not copy one template per viewpoint.
- Tag each question with a concern that viewpoint frames. Drop concerns it does not frame.
- Do not ask for classes, call chains, hosts, or actors when the grain forbids them.

Write `architectural_questions.json`, then `view_specification.json` from the winner plus instantiated required information. Concerns the winner does not frame go in `unanswered_concerns` / `declared_gaps`.

### 4. Repository Analysis

Now open `--code`.

- List the tree. Skip binaries, build outputs, `.git`, `node_modules`, `target`, `venv`.
- Search for task-focus tokens (booking, reservation, registration, notification, deploy, entity, …). Keep domain nouns; drop the stopword list in `view_projection.yaml` → `forced_seeds.extra_stopwords`.
- Keep **at most 16** source files: up to 8 forced by task cues, then fill with files that define the owning types / configs (Docker, compose, SQL, application properties).
- Prefer implementation types that own the task (`ReservationManager`, `LibraryFacade`, `UserManager`) over GUI widgets and DTOs.

Write `repository_scope.json` with the kept relative paths and a one-line reason each.

### 5. Evidence Extraction and Grounding

Read the scoped files. Build `view_model.json` for the **winner only**.

Follow the grain for that `viewpoint_id`:

- **module-decomposition**: 5–12 modules named by **responsibility** (file-stem type names). Relations: `contains` or `uses`.
- **cnc-runtime**: runtime components and connectors at component grain.
- **code-mapping**: architecture elements mapped to implementing types. No UI/controllers as entities unless they own the mapping.
- **allocation-deployment**: artifacts, nodes, datastores. Seed from Docker/compose/SQL, not Java packages.
- **context**: actors + **one** system box with a product name (not a package or GUI file) + externals/datastores.
- **decision-record**: components affected by recorded decisions (do not invent ADRs).

Every non-actor element needs `evidence.file` that exists in the scope, plus a short `excerpt`. `support` is `observed` if the excerpt shows it, else `inferred`.

Forbidden box names for component/module/sequence views: `Boundary`, `Entity`, `DTO`, `Controller`, `Control`, `Database`, Java package segments (`it.unina…`), folder names (`boundary`, `entity`, `dto`).

If a required-information need cannot be grounded, put its id in `unanswered`. Do not fake it.

### 6. Need–Evidence Reconciliation

Check the view against the questions and the required information. Notes only. Do not add boxes, and do not change the viewpoint.

Write `structure_report.json`:

- which AQ / RI ids are answered, and what is missing when one is not
- leftover package-shaped names (must be empty; if any, rename that element from a scoped file and rewrite the diagram once)
- gaps (missing evidence)

A missing class, or a box for a declared gap, is not a reason to add an element. Missing means a responsibility, connector, actor, or host that this grain allows and a question asks for.

### 7. Specialized View Generation

Write `architecture_view.puml` (or `.mmd` if the viewpoint default is mermaid: `context`, `decision-record`).

PlantUML rules:

- Wrap with `@startuml` / `@enduml`.
- Component/module: `component "Name" as E1`.
- Sequence: `participant` / `actor`, arrows `E1 -> E2: label` in `order`.
- Deployment: `node` / `database` / `artifact`.
- Context: actors around one `system` box.
- Use element ids (`E1`) as aliases. Do not invent extra boxes.

### 8. Validation and Consistency

Write `validation_report.json`:

- `syntax.status`: `pass` if the diagram has matching start/end markers
- `semantic.elements_resolved`: `k/n` elements whose `evidence.file` is in the scope
- `semantic.relations_resolved`: both ends exist
- `unsupported`: elements/relations with no evidence
- `granularity_violations`: class inventory on a component view, package-shaped names, GUI-as-system
- `unanswered_information` / `unanswered_concerns`
- `verdict`: `pass` | `pass_with_corrections` | `fail`

Fix `fail` once (rename or drop unsupported boxes), then rewrite the diagram and reports.

## Output files (all required)

```
<out>/
  stakeholder_task_profile.json
  architectural_questions.json
  correspondence.json
  viewpoint_plan.json
  view_specification.json
  repository_scope.json
  view_model.json
  structure_report.json
  architecture_view.puml   # or .mmd
  validation_report.json
```

JSON must be valid. Schemas: [references/output-schema.md](references/output-schema.md).

## Comparison notes (do not skip)

This baseline is comparable only if you:

1. Use the same `--goal` text and the same `--code` checkout.
2. Produce the same filenames as Task2View.
3. Stay inside the catalog (no homemade viewpoint names).
4. Ground names in the repository.

After writing files, print a 8-line summary: role, winner viewpoint, file count, element count, relation count, unanswered RI ids, verdict, output path.
