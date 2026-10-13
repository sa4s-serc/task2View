# Phases 6–8 — Decisions, views and validation

The pipeline does this in `phase6/decide.py`, `phase7/project.py`, `phase7/notations/` and `phase8/`.

## Abstraction (ADR-007)
For structural views at medium or coarse granularity:
1. **Scope:** the classes the verified claims are about; plus API, UI and job classes that call them and share the request's words (follow screen-to-screen navigation); plus the data access, domain and integration classes they reach (two hops).
2. **Role per class**, strongest evidence first: framework facts (entry point kind, annotations like `@RestController`/`@Service`/`@Repository`/`@Entity`, supertypes, persisted entity), then the class name (`…Controller` with routes = API, `…Service`/`…Manager`/`…Facade` = service, `…Repository`/`…Registry`/`Persistence…` = data access, `…DTO`/`…Factory`/`…Strategy` = helper), then the package (`swing`/`ui` = UI, `entity`/`domain` = domain). Start-up/configuration only when nothing else fits. Catalogue: `knowledge/element_roles.yaml`.
3. **Parts:** one per role (coarse: one per layer: presentation, application, domain, data access). Helpers join the one part that uses them; a data type used by several parts is listed, not drawn. Facts add the database (from the JDBC URL) and the web client (pages that call `/api`).
4. **Names:** name each part as an architect would (1–5 words, the system's own words, never a class name unless it has one class) with a one-line description; split a part into 2–3 only if its members do different jobs. Every member stays listed.
5. **Arrows:** one per pair of parts, only where their members have code dependencies; label with the intent for the pair of roles (e.g. "delegates requests", "reads and saves", "persists") and the protocol (HTTP/JSON, in-process, JPA / JDBC). Mark arrows the layering does not allow; list weak (< 3 dependencies) or implied ones instead of drawing them. Decomposition views draw no arrows.
6. **Draw** C4-PlantUML: `Component` per part inside a `System_Boundary`, `ComponentDb` for the database, `Rel` with label and protocol, a dashed red tag for arrows against the layering, `SHOW_LEGEND()`.

## Phase 7 projection
A view is drawn from the evidence model only:
- **Never invent, rename or merge an element.** Each mark keeps its evidence-model id and name.
- **Select** the elements most relevant to the view's questions: first those with claims answering them, then those whose names share words with the subjects or target.
- **Cap** at the view's `max_elements`; list the remaining ids in `overflow` and add a limitation.

| Viewpoint family | What to draw |
|---|---|
| decomposition, layered, client-server and other C&C, uses, generalization | Components (kind `component`, or `module` / `class` where the viewpoint uses those), with `stereotype` = layer and `responsibilities` inside. **Layered overlay:** add a group element per layer used (`id: group:layer:<layer>`, `kind: layer`, `group: true`) and set each component's `parent`. **Decomposition without layers:** group by the enclosing package (`group:module:<package>`): a class component in its package, a package component in its parent package. **uses:** the focus components plus what depends on them, then what they depend on. **generalization:** only components in an inheritance relation, with `is-a` relations. Relations: the model's `uses` relations between drawn elements (`allowed-to-use` in layered). C&C views also draw datastores when a persistence-layer component is drawn; datastores count toward the cap. An empty view reports the gap "no components evidenced". |
| context | One `system` element for the analysed system (named after the repository), with the actors, external systems and datastores around it; `uses` edges where a relation links one of them to a component inside the system. |
| data model | Entities with attributes, `{PK}` and `{FK}` marks; associations with multiplicity; composition; generalization between entities. Foreign-key fields stay attributes. |
| sequence, communication, activity | One scenario per view, the most relevant one; list the others as limitations. Lifelines are the participants in order of first appearance (actors as `actor`). Interactions keep their order. Fragments allowed by the detail level (sequence: overview none, feature `alt`, detailed `alt`/`opt`/`loop`). |
| state machine | One machine (states of the most relevant enum or state hierarchy) and transitions from claims; with no transitions, add the limitation "transitions were not evidenced". |
| use case | A system group named after the repository, actors outside it, use cases inside it, associations / include / extend. |
| deployment, install, data stores | Nodes, environments, artifacts and datastores, with artifacts nested in their node (that nesting replaces the deploys edge); communicates relations. |
| tables (interfaces, decisions, requirements, work assignment, implementation) | One row per element of the table's own kinds (interfaces, decision records, requirements, …); implementation lists components with their files. No such element: report the gap, do not fall back to components. |

Every view lists, in `traceability`, each element's files and symbols.

### Notation (PlantUML, the default)
| Mark | PlantUML |
|---|---|
| layer, module or system group | `package "Name" as <alias> <<layer>> { … }` (`rectangle` for the system) |
| component with responsibilities | `component "Name\n--\n- responsibility" as <alias> <<layer>>` |
| entity | `class "Name" as <alias> <<entity>> { id : Long {PK} … }` |
| datastore / artifact / node | `database` / `artifact` / `node` |
| actor / use case | `actor` / `usecase` |
| relations | `-->` uses; `..>` allowed-to-use and include/extend (`: <<include>>`); `--|>` is-a / generalization; `*--` composition; `A "*" --> "1" B : label` association |
| sequence | `participant` / `actor`; `A -> B : 1. message`; `alt guard` … `end` |
| activity | swimlanes `|Name|` declared before `start`, `:action;`, `if (guard) then (yes)` … `endif` |
| state | `state`, `[*] --> S`, `S1 --> S2 : label` |

Use one stable alias per element (the pipeline uses `e_` + the id with non-alphanumerics replaced by `_`, plus a short hash when characters were replaced). Responsibilities never go on edges.

## Phase 6 decisions
For each question of the view:
- `supported`: a claim answering it is drawn in the view.
- `partial`: claims exist but none is drawn, or the view is built from repository facts only.
- `unsupported`: no evidence.

Then decide, checking these rules in order:
1. The view draws nothing:
   - the viewpoint's evidence is absent from the repository (planned evidence gap) → `gap`;
   - else, if a round remains → `request_evidence` for all of the view's questions (at most 2 extra rounds of Phase 4–5);
   - else, if projection reported why it is empty → `gap`;
   - else → `drop`.
2. A component or package view overflows its cap, and either the goal has no target (a whole-system overview) or the selection is more than twice the cap → `simplify`: one element per layer, or per package when there are no layers, listing its components; relations between groups are labelled "<n> dependencies".
3. The view has an evidence gap → `gap` (keep the view, report the gap).
4. Otherwise → `confirm`.

## Phase 8 validation
1. **Notation:** the source is well formed in its language (compile it if you can), and the model kind matches the viewpoint.
2. **Constraints:** every constraint the viewpoint lists in `viewpoints.yaml`. Severities and rules are in catalogs.md; `error` fails the view, `warning` is reported.
3. **Faithfulness:**
   - every element is in the evidence model (or is a group or fold of evidence-model elements) and is not weakly supported; a **part** lists member classes or files that all exist, and no class belongs to two parts;
   - names are unchanged;
   - no element is drawn twice, and no symbol is drawn by two elements (states of one enum share its symbol and are exempt);
   - every interaction is a step of a recovered scenario.
4. **Coverage:** the Phase 6 table. A view with questions and at least two elements must draw at least one relation or interaction (except decomposition and use-case views, which show containment).
5. **Readability and spec** (structural views): no method names on arrows (error); at most max(1, 10% of the arrows) crossings when laid out top-down (warning); descriptions of at most 12 words (warning); a title and a legend (warning); coarse views at most 6 parts; no single class shown as a part at medium or coarse granularity; a feature view shows where requests enter; decomposition views have no arrows. No model judges the view.
6. **Correspondence:** list in `viewset.json` `correspondence_gaps` every component of a sequence, communication or activity view that no structural view of the set draws.

**Verdict:**
- `fail` on any error in layers 1–4;
- `pass_with_limitations` when there are gaps, limitations, warnings or non-supported questions;
- `pass` otherwise.

On `fail`, remove the offending marks (`repair_marks`) and redraw, at most 2 times.
