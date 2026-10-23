---
name: task2view
description: Produce stakeholder- and task-specific architecture views (ISO/IEC/IEEE 42010, Views and Beyond) from a local repository and a free-text stakeholder goal, following the Task2View method step by step and writing the same artifacts as the Task2View pipeline. Use when asked for an architecture view, viewpoint, or Task2View single-agent run for a stakeholder goal. Not for code review, refactoring, or implementing features.
---

# Task2View (single-agent method)

You are **one agent** carrying out the Task2View method by hand: the same phases, rules and output files as the Task2View pipeline (ADR-006). In experiments this is the "agent + skill" condition, compared file by file with the pipeline and with a plain agent.

**Inputs:** `--code` (repository path), `--goal` (the stakeholder's request, verbatim), `--out` (output folder), optional `--run-id`. Every view is drawn in UML 2.5.1 with PlantUML (ADR-008); there is no other notation. If `--code`, `--goal` or `--out` is missing, ask once, then proceed.

## Hard rules
- **Do not run the pipeline.** Do not run `task2view`, `python -m task2view`, or anything under a `Task2View/` folder. Do not read Task2View run folders.
- **No UML models or images as evidence.** Never open UML models or exported diagrams (`.vpp`, `.puml`, `.drawio`, `.png`, `.svg`, `.pdf`, …). They are what the views are evaluated against.
- **Use only the catalogs.** Every need, viewpoint, role, element kind and relation kind comes from [references/catalogs.md](references/catalogs.md) (generated from the pipeline's own catalog files in [knowledge/](knowledge/)).
- **Cite real code.** Every element and relation you draw has a citation: file, line range, and an excerpt copied exactly from those lines.
- **Use the code's names.** Never invent names.
- **Write every file** listed in [references/output-schema.md](references/output-schema.md), with exactly those names and fields.

## Workflow

Work in this order (it is the order of the pipeline). Write each file when its phase is done. Do not change an earlier decision because of what you see later, except where a phase below says so.

### Phase 0 — Repository card
Survey the repository without interpreting it architecturally yet.
1. List the tree. Skip `.git`, `node_modules`, `target`, `build`, `dist`, `venv`, caches.
2. Classify the files: code, test, build, deploy, config, schema, web, docs, model, binary (rules: `knowledge/corpus.yaml`).
3. Note the facts:
   - languages;
   - layers: package or directory names matching the layer aliases in `corpus.yaml`;
   - entry points: `main`, HTTP routes, GUI frames, scheduled jobs, event listeners;
   - persisted entities with their fields (ORM annotations, models, SQL `CREATE TABLE`);
   - deployment and build files.
4. Decide the **repository signals** (table in catalogs.md). Record one piece of evidence per signal (file and what it shows). Raise a signal only when the evidence is in the code or configuration, not because the domain suggests it.

Write `repository_card.txt` and `repository_card.json`.

### Phase 1 — Stakeholder profile
Read only the goal. Record:
- **role_label / role:** the person's own words, and a role id from the catalog (or null).
- **target:** the feature or subsystem the goal is about, copied exactly (or "" for the whole system).
- **needs:** for each kind of information the goal asks to *see*, give the need id, **evidence** (the exact words of the goal) and **salience**:
  - `primary`: the goal says the person needs to understand, identify or see it.
  - `secondary`: mentioned in passing, context, or implied.
- **subjects:** items the goal enumerates as things to understand, copied exactly, each with its need ids.
- **quality_attributes:** ISO 25010 ids the goal stresses (they never choose diagrams).
- **detail_level:** computed, not judged (see the end of catalogs.md).
- **spec** (ADR-007): `scope` ("feature" if there is a target, else "system"); `granularity` ("coarse" for a whole-system overview, else "medium"; "fine" only if the person asks for classes); `behaviour` ("structure", "interaction" or "both", from the primary needs).
- **clarifications:** at most 3 questions, only where the goal leaves scope, granularity or behaviour open, each with a default. If you can ask the person, ask; otherwise use the defaults and record them.

How to type needs:
- Words that only name the person's work ("I will change the persistence layer") are not a need.
- **Structural** needs ask which parts exist and how they relate. **Behavioural** needs (interaction-order, process-flow, lifecycle, actors-goals) ask what happens over time; list one only when the goal asks about that dynamic aspect.
- People who use the system belong to actors-goals. Software parts that work together belong to collaboration.

Check: every evidence string, subject and target appears word for word in the goal. Drop anything that does not, and record it under `dropped`.

Write `stakeholder_profile.json`.

### Phase 3 — Viewpoint selection (deterministic)
Follow [references/selection.md](references/selection.md) exactly: choose the **one** applicable viewpoint that best covers the **primary** need. Then:
- specialise a C&C view to the repository's style;
- add the layered overlay when the repository is layered;
- record evidence gaps;
- assign the subjects.

Secondary needs never add a view.

Write `view_plan.json`. Number the views `V1-<viewpoint id>`, `V2-…` in plan order.

### Phase 2 — Questions per view
For each view, write one question per (need, subject) it covers, or one per need when it has no subjects. Use the form `For <subject or target>: <need definition>?`. Ids are `AQ1`, `AQ2`, … across all views.

Write `architectural_questions.json`.

### Phase 4 — Investigation plan
Make one task per (view, subject), or per (view, need) without subjects, with at most 6 tasks per view. For each task, record:
- **starting symbols:** classes or modules whose names or method names share words with the subject or target, plus entry points and their direct dependencies;
- **starting paths:** configuration, deployment and schema files for allocation and data views;
- **why each was suggested.**

Starting points are not a boundary.

Write `investigation_plan.json`.

### Phase 5 — Evidence
Carry out each task by reading code. Record **claims** as described in [references/evidence.md](references/evidence.md): one fact per claim, each with a citation copied exactly from lines you have read. Then verify every claim yourself against the file, using the same checks the pipeline applies, and drop the ones that fail (keep them under `rejected_claims` with the reason). Set the support class as described there.

Then build the **evidence model** (also in evidence.md):
- components anchored on the classes your claims are about, with helpers merged in;
- relations derived from real code dependencies between members;
- entities from persistence facts (foreign keys stay attributes);
- deployment elements from deploy and build files;
- states;
- ordered scenarios with alternative paths.

Write `evidence_model.json`.

### Phase 7 — Views
**Structural views** (decomposition, uses, layered, C&C, client-server, multi-tier, shared data, SOA) are drawn as **parts**, not classes: follow "Abstraction" in [references/views.md](references/views.md#abstraction-adr-007). Other views use the projection rules for their viewpoint family in the same file:
- **Never invent an element.** Parts get architectural names, but every part lists its member classes.
- **Put content in the right place:** responsibilities inside elements, attributes inside entities, layers or packages as containers.
- **Behaviour views:** ordered messages with `alt` blocks.
- **Cap the elements** at the view's `max_elements`; list the rest under `overflow`.

Then write the diagram in UML (PlantUML), following "UML in PlantUML" in [references/views.md](references/views.md#uml-in-plantuml-the-only-notation-adr-008) and the diagram types in [knowledge/uml-2.5.1.yaml](knowledge/uml-2.5.1.yaml).

Write `V*/view.json`, `V*/view.puml` (a UML diagram for every view), `V*/architecture.json` (parts with members, arrows with their code evidence) and `viewset.json`.

### Phase 8 — Checks
Check the view by the two rules in [references/views.md](references/views.md#phase-8-checks): the diagram compiles, and every mark is backed by verified code. No model judges the view; whether it is the right view is for the person.

Write `validation_report.json`, `traceability.md` (element → files and symbols), and `README.md` (goal, role, needs, the view with its verdict, rationale, limitations and needs not covered, evidence counts).

## When you finish
Print an 8-line summary:
- role and primary needs;
- the views (viewpoint ids);
- for each view, its decision and verdict;
- the number of claims, verified and rejected;
- the uncovered needs and declared gaps;
- the output folder.
