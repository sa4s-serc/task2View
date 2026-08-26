# ADR-005 — Correspondence kernel and viewpoint-keyed published grain

- **Status:** accepted
- **Date:** 2026-08-26
- **Supersedes:** [ADR-004](ADR-004-filesystem-graph-and-config.md) D2 (directory groups as the published architecture)
- **Extends:** [ADR-001](ADR-001-agentic-realignment.md) D2–D4 (interpret / questions / viewpoint stay agents)
- **Extends:** [ADR-002](ADR-002-sota-plugins.md) (scoper / extractor / notation remain plug-ins)

## Context

ISO/IEC/IEEE 42010 correspondence is:

**stakeholder × concerns × task → viewpoint → view**

The catalog already had stakeholders, concerns, V&B Table 9.1, task cues, and viewpoints. Extraction did not obey that. Three successive extractor contracts all assumed one diagram kind:

1. One box per class / every graph edge (hairball).
2. One box per parent directory (`Boundary` / `Control` / `Entity`, or `dto` / `Swing`).
3. Always 4–8 “responsibility component” boxes.

None of those is a viewpoint. A tester, a DBA, a DevOps engineer, and a business analyst do not share a component diagram. Forcing one made every quality attribute look like maintainability.

Questions were also asked **before** viewpoint selection, using every viewpoint the role might ever use. A developer’s required list includes `code-mapping` (type grain), so class/entity questions leaked into module views.

## Decision

### D1. Correspondence is a catalog function, not a prompt

`knowledge/correspondence.py` ranks viewpoints with no LLM and no repository:

- V&B Table 9.1 detail rank for the stakeholder row
- stakeholder required / optional viewpoints
- task-cue preferred viewpoints, **weighted** so specific cues (persistence, deploy, trust, context) outrank generic verbs such as “modify”
- overlap between the viewpoint’s `frames_concerns` and the task’s concerns

The winner binds `published_grain` for that `viewpoint_id`. Legacy `identify_view` and the agentic path both call this function so grain cannot drift.

Artifact: `correspondence.json` (ranked ids, grain unit / nodes / relations / forbid).

### D2. Grain is keyed by viewpoint, not by view_type special cases

`view_projection.yaml` `published_grain` is the reusable contract. Each catalog `viewpoint_id` declares:

| Field | Meaning |
|---|---|
| `unit` | `context` · `component` · `type` |
| `nodes` | what may appear as boxes / lifelines / entities |
| `relations` | what edges the view is for |
| `forbid` | class dumps, folder boxes, full call graphs, … |

Examples: `context` → actors + system; `scenario` → component-grain participants + ordered calls; `data-model` → persistent entities; `allocation-deployment` → artifacts and nodes; `module-decomposition` → subsystems and uses. Adding a stakeholder or quality concern is catalog work (a YAML row), not a new extractor special case.

### D3. Agents consume the selected grain; they do not invent a diagram kind

Pipeline order on the default path:

```
interpret → correspondence → questions at that grain → viewpoint confirm
         → extract (VIEWPOINT GRAIN) → apply_facts(unit) → critic notes → gate → render
```

- Questions are seeded from the **selected** viewpoint’s required-information templates. Type-level questions only if `unit` is `type`; call-chain questions only for scenario / control-flow.
- The viewpoint agent may only pick `viewpoint_id` from the ranked candidate list. Invalid picks snap back to the correspondence winner. Purpose is rewritten to the grain row. If task cues already prefer a behavioural viewpoint (`scenario` / `control-flow`), a later structural-token retarget does not override that.
- Gemini / ArchAgent / CIAO extract prompts all receive `grain_prompt(viewpoint_id, view_type)`.
- `apply_facts` uses `view_unit(view_type, viewpoint_id)`. Component/module names stay; type-level graph edges only when `unit` is `type`; context completes actors + system. Parent-directory names are not the model unless the grain is layers.
- The gate does not rename component boxes to class stems. The critic does not add class neighbours.

### D4. One view per run remains a cost cap, not a modelling claim

`preferences.max_views` still defaults to 1. Correspondence across several views of the same system is future work. Unanswered concerns (catalog ids the chosen viewpoint does not frame) stay declared gaps.

## Consequences

- A missing component diagram is not a failure: context, scenario, data-model, and deployment are first-class grains.
- Evaluation goals that used to collapse to the same component dump now select different viewpoints (developer → module-decomposition, tester → scenario, DevOps → allocation-deployment, DBA → data-model, analyst overview → context) without hardcoding repository type names.
- `apply_facts` no longer publishes folder groups as architecture. ADR-004 D1 (filesystem graph) and D3–D5 (42010 artefacts, notation, plug-in config) still hold.
- Cue weights live in `task_cues.yaml`. A DBA goal that contains both “modify” and “entities” prefers `data-model`, not `module-uses`.
