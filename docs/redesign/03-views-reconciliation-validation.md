# Redesign 3 — Views, reconciliation and validation (Phases 6, 7, 8)

*Draft for discussion, 2026-10-08. Addresses design review RC4 (the view contract cannot express what the expert asked for) and RC5 (no closed loop). Builds on [01](01-knowledge-model.md) (viewpoints, element and relation kinds, constraints) and [02](02-evidence-and-architecture-model.md) (the Architecture Evidence Model, AEM). Vocabulary: ISO/IEC/IEEE 42010:2011.*

## 1. What is wrong today

**The view format (`ViewModel`) is too thin:**
- groups are flat, and Phase 7 always empties them;
- `role` is a single string;
- no stereotypes, attributes or operations;
- `order` exists but is never set;
- one view per run.

**The renderer draws everything the same way:** every box is `[X]`, every relation is `-->`, `contains` is drawn as an arrow, and node, actor and use-case shapes are never used.

**Nothing closes the loop:**
- Phase 6 may only annotate.
- Phase 8 checks name strings and prose. Its verdict was `pass_with_corrections` for all 10 pilots, and its renaming step created duplicate boxes.

## 2. Principle

**A view is a projection of the AEM, governed by its viewpoint record.** Phase 7 does not invent, rename or merge anything. It *selects* from the AEM and *projects* what it selected:
- **Selection:** which elements, relations and scenarios serve this view's questions and subjects, at its detail level.
- **Projection:** kinds, grouping, stereotypes and notation, from the viewpoint record.

The LLM only words things: short responsibility phrases, message labels, the title. Every drawn mark carries an AEM id, so the checks in §6 are lookups, not string matching.

## 3. View format v2

### 3.1 One run produces a view set
```json
{"system_of_interest": "Progetto-IS",
 "stakeholder": "tester-and-integrator",
 "views": ["V1", "V2"],
 "correspondences": [
   {"rule": "same-element", "views": ["V1", "V2"], "elements": ["cmp:user-management"]},
   {"rule": "lifeline-realizes-component", "from": "V2:UserManager", "to": "V1:cmp:user-management"}],
 "declared_gaps": [{"need": "ownership", "reason": "no CODEOWNERS or git authors"}]}
```

### 3.2 One architecture view
```json
{"id": "V1", "viewpoint": "client-server", "combined_with": ["layered"],
 "model_kind": "uml-component", "title": "User registration — components",
 "purpose": "…", "detail_level": "detailed",
 "addresses": ["AQ1", "AQ2"], "scenario": null,

 "elements": [
   {"id": "layer:control", "kind": "layer", "name": "Control", "parent": null},
   {"id": "cmp:user-management", "kind": "component", "name": "UserManager",
    "stereotype": "control", "parent": "layer:control",
    "responsibilities": ["validates personal data and role", "enforces e-mail and identifier uniqueness"],
    "attributes": [], "realized_by": ["…controller.UserManager", "…factory.StudentFactory"],
    "support": "observed", "evidence": ["C12", "C17"]}],

 "relations": [
   {"id": "R3", "kind": "uses", "source": "cmp:library-facade", "target": "cmp:user-management",
    "label": "register(...)", "multiplicity": null, "protocol": null,
    "support": "observed", "evidence": ["C9"], "member_edges": ["LibraryFacade→UserManager"]}],

 "interactions": [],
 "fragments": [],
 "traceability": [{"element": "cmp:user-management", "files": ["…/UserManager.java"], "symbols": ["UserManager.register"]}],
 "limitations": ["registration via Swing and REST share the facade; only REST is shown"],
 "gaps": [],
 "confidence": 0.86}
```

**Rules of the format:**
- **Nesting** is `parent` on any element. Layers, packages, nodes, execution environments and the system boundary are all elements, so "layers around the components" and "node ⊃ environment ⊃ artifact" use the same mechanism. Fixes **Layers**.
- **`responsibilities[]` sits on the element**, never on an edge. Fixes **Placement**.
- **`attributes[]`** (name, type, key) on entities. Foreign-key fields are attributes. An association is drawn only for a real object reference, never for an `id_*` field. Fixes the expert's `id_cittadino` comment.
- **`stereotype`** comes from the layer, or from the C&C style (client/server, publisher, …). Fixes **Notation**.
- **`interactions[]`** carries the ordered messages for sequence and communication views: `{order, source, target, message, kind: call|return|create, fragment}`. **`fragments[]`** carries alt/opt/loop with guards. Fixes the missing order.
- **Kinds are closed per viewpoint** (01 §3), so a box's kind never comes from the grain unit, as it does today.

## 4. Phase 7 — Projection rules per viewpoint family

| Family | Selection | Projection |
|---|---|---|
| decomposition / layered / uses | Components realizing the view's subjects, plus their containing modules or layers; for **uses**, the dependents of the subject elements (GR10-Q3: who depends on the persisted entities) | Nest by layer or package; uses edges lifted from member edges; layers ordered top-down by *allowed-to-use* |
| C&C (generic or style) | Components on the subjects' collaboration paths, plus datastores and externals they touch | Style stereotypes; connectors labelled with the operation or protocol; layer overlay when combined |
| sequence / communication | One scenario per view. Lifelines are the components on the scenario path; alternatives come from the claim conditions | Ordered messages, alt fragments for the failure subjects (invalid data, duplicate account) |
| activity | Scenario steps and decisions | Actions, decisions, swimlanes per component |
| state-machine | An element with a lifecycle (e.g. report status enum plus its transitions in code) | States, transitions, guards |
| data-model | Persisted entities in scope, with fields from `@Entity`/SQL | Attributes with types and keys; associations with multiplicity; composition only for embedded or cascade-owned |
| use-case | Actors (user roles), use cases (entry operations: controllers, facade methods, tests), include/extend from call chains | System boundary, actor generalization |
| deployment / install | Nodes and environments from deploy/config, artifacts from build, datastores from persistence config | `node ⊃ env ⊃ artifact`; communication paths with protocol (e.g. JDBC/MySQL) |
| context | System, actors, external systems, datastores | One system box named after the product, never a package or GUI |

**Detail level** sets the caps from the viewpoint's `granularity` row (01 §5.1). When a selection exceeds its cap, Phase 6 decides what happens (§5); Phase 7 does not silently drop marks.

### Rendering
*Superseded in part by decision §9.2: every adapter renders every model kind. The bullets below describe the PlantUML and Mermaid targets.*

- **One renderer per (model kind, language).** PlantUML covers every UML model kind natively:
  - component with packages and stereotypes, responsibilities in the box body
  - sequence with `alt`/`opt`/`loop`
  - class with attributes and multiplicities
  - use case with a system rectangle
  - deployment with `node`/`artifact`/`database`
  - activity, state
- **Mermaid** for the kinds it renders well (sequence, class, state, flowchart).
- **The other adapters** (d2, C4, Structurizr, …) render every model kind too, natively where the language allows and by a documented approximation otherwise (§9.2).
- **Layout hints come from the model:** layer order becomes vertical position, scenario order becomes lifeline order, groups keep their members together. Fixes **Layout**.
- The diagram is compiled in Phase 7. A render failure is an input to Phase 8, not a silent `fail` in a side report as GR10-Q4 was.

## 5. Phase 6 — Reconciliation decides

Phase 6 runs per planned view, after the AEM exists and before projection.

1. **Coverage table.** For each assigned question and subject: `supported | partial | unsupported`, with the claim ids. This is computed: a subject is supported when the AEM has elements or relations of the kinds the question asks for, linked to that subject.
2. **Decision per view** (research plan Phase 6: confirm, simplify, change granularity, drop):

| Condition | Decision |
|---|---|
| All questions supported, within caps | `confirm` |
| Over the element cap | `simplify`: one detail level coarser, or `split` by layer or scenario if the view cap allows |
| A subject unsupported, but evidence plausibly exists (budget left, unsearched evidence classes) | `request_evidence(task)` → back to Phase 4/5, at most 2 rounds |
| Viewpoint's evidence absent (e.g. no deploy files) | keep the view, show what exists, add a **declared gap** (decision from 01 §8) |
| Nothing supported | `drop`, and report the need as a gap |

Decisions are **rule-based and logged**. The LLM writes only the limitation sentences. This makes the reconciliation step auditable and testable, unlike today's free-text annotations.

## 6. Phase 8 — Validation in five layers

| Layer | Checks | Kind |
|---|---|---|
| 1 Notation | The diagram compiles in its language; the model kind matches the viewpoint | hard |
| 2 Viewpoint constraints | The named predicates from 01 §5.1, e.g. `no_package_or_directory_element`, `lifeline_is_component_or_actor`, `messages_ordered`, `association_not_fk_field`, `component_has_responsibility`, `element_kind_allowed`, `max_elements` | hard |
| 3 Faithfulness | Every mark has an AEM id with support ≥ `inferred`; names are a member symbol or a marked phrase; no two marks share an AEM id; every lifted relation has a member edge; excerpts verified (from 02 §5.2) | hard |
| 4 Coverage and consistency | Every assigned question has its required kinds for each subject; the same AEM id has the same name in every view; correspondences resolve | hard for missing kinds, else gap |
| 5 Task fit (Track 2) | An LLM judge scores the rendered view against the profile and the questions on the expert's seven themes. It gives a score and a reason per theme, and does not decide pass/fail on its own until it is calibrated | soft |

- **Verdict:** `fail` on any hard check; `pass_with_limitations` when gaps or limitations are declared; else `pass`.
- **Repair:** a failed layer 1–3 check re-runs the projection with the offending marks fixed or removed, at most 2 times. A failure that needs evidence goes back to Phase 6 as `request_evidence`.
- **Independence:** the task-fit judge uses a different model from the generator by default. The pluggable LLM layer makes this a setting.
- **Calibration of layer 5:**
  - the 18 expert comments on the pilot;
  - the CodeToDiagram ground-truth diagrams (340+);
  - the GR10 Visual Paradigm model, via `tools/compare_gr10.py`.

  This is Track 2.

## 7. The expert's themes, mapped to mechanisms

| Theme | Mechanism |
|---|---|
| Second view | 01 covering selection (behaviour viewpoints exist; cap 3) + view set with correspondences |
| Grain | Detail level → granularity row and caps; components from 02 abstraction; `max_elements`, no mixed kinds (layer 2) |
| Layers | `parent` nesting + `combined_with: layered` + layer order in layout |
| Names | AEM registry (02) + name fidelity (layer 3) + `no_package_or_directory_element` |
| Notation | Closed kinds per viewpoint + stereotypes + one renderer per model kind |
| Placement | `responsibilities[]` on elements; FK fields as attributes (`association_not_fk_field`) |
| Layout | Layout hints from layers and scenario order; render checked in layer 1 |

## 8. Output package (research plan §7)

Per run directory:
- `viewset.json`
- one `V*/view.json` plus diagram source and image per view
- `evidence_model.json` (the AEM)
- `reconciliation.json` (coverage tables and decisions)
- `validation_report.json` (per view, per layer)
- `traceability.md` (element → files/symbols, per view)
- `README.md` per run: rationale, addressed questions, limitations, declared gaps, confidence

## 9. Decisions (2026-10-08)

1. **Phase 7: deterministic projection.** The LLM only writes the wording (responsibilities, labels, titles).
2. **Notation: all adapters are equal.** Every registered language must render every model kind. Where a language has no native construct, the adapter approximates it with a documented, consistent convention and records `approximated: true` in the validation report, rather than refusing. This replaces the "PlantUML first" proposal in §4.

   Support matrix (N = native construct, A = approximation convention). Expected from each language's documentation; to be verified per adapter while implementing:

   | language | component / C&C | layered / decomposition | sequence | communication | activity | state | data model | use case | deployment | context |
   |---|---|---|---|---|---|---|---|---|---|---|
   | plantuml | N | N | N | A | N | N | N | N | N | N |
   | c4plantuml | N | N | N (dynamic, or plain PlantUML) | N (dynamic) | N* | N* | N* | N* | N | N |
   | mermaid | A (flowchart + subgraphs) | A | N | A | N (flowchart) | N | N (class / ER) | A | A | N (C4) |
   | d2 | N (containers) | N | N | A | A | A | N (sql_table / class) | A | N (containers) | N |
   | structurizr | N | N | A (dynamic) | N (dynamic) | A | A | A | A | N | N |
   | graphviz | A | A (clusters) | A | A | A | A | A (record shapes) | A | A | A |
   | nomnoml | A | N (packages) | A | A | A | A | N (class boxes) | N | A | A |
   | excalidraw | A | A | A | A | A | A | A | A | A | A |
   | bpmn | A | A | A | A | N | A | A | A | A | A |

   \* c4plantuml includes PlantUML, so the non-C4 kinds use the plain PlantUML constructs.
3. **Task-fit judge:** uses a different model from the generator by default. It is soft, reported but not gating, until calibrated on the expert reviews, CodeToDiagram and the GR10 UML model.
4. **Repair budget:** 2 projection retries and 2 evidence rounds per view.

## 10. Implementation status (2026-10-08)

Implemented in `code/src/task2view/` (ADR-006 steps 4–5), with tests on synthetic repositories:
- View format v2: `contracts/views.py`. Projection: `phase7/project.py`, including `fold` (Phase 6 simplify) and `exclude` (Phase 8 repair).
- Renderers: `phase7/notations/`, 9 languages x 10 model kinds; the approximated flag comes from the §9 matrix.
  - Compile-checked locally: PlantUML, C4-PlantUML, Graphviz, Mermaid.
  - Checked for structure: D2, nomnoml, Structurizr, Excalidraw, BPMN.
- Phase 6: `phase6/decide.py`. Phase 8: `phase8/constraints.py`, `validate_view.py`, `judge.py`.

Differences from the text above:
- **`split` is not automatic yet.** An overflowing structural view is simplified (folded to layers or packages) instead, and the limitation says so.
- **No LLM wording step in Phase 7.** Responsibility phrases are the ones written in verified claims, and titles and labels are deterministic, so every word in a view traces to a claim or a code symbol. An LLM wording pass can be added later behind the same projection.
- **The judge does not run without a judge model.** It is skipped unless `--judge-llm` is given. Independence is reported as unknown when either model has no spec.
