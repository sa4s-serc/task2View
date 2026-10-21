# Phases 6–8 — Decisions, views and validation

The pipeline does this in `phase6/decide.py`, `phase7/project.py`, `phase7/uml_arch.py`, `phase7/notations/plantuml.py` and `phase8/`.

**Every view is a UML 2.5.1 diagram (ADR-008).** The diagram types, the symbols and paths each allows, the Standard Profile stereotypes and the frame headings are in [`../knowledge/uml-2.5.1.yaml`](../knowledge/uml-2.5.1.yaml), with the clause of the UML specification for each rule. Use only those.

## Abstraction (ADR-007)
For structural views at medium or coarse granularity:
1. **Scope:** the classes the verified claims are about; plus API, UI and job classes that call them and share the request's words (follow screen-to-screen navigation); plus the data access, domain and integration classes they reach (two hops).
2. **Role per class**, strongest evidence first: framework facts (entry point kind, annotations like `@RestController`/`@Service`/`@Repository`/`@Entity`, supertypes, persisted entity), then the class name (`…Controller` with routes = API, `…Service`/`…Manager`/`…Facade` = service, `…Repository`/`…Registry`/`Persistence…` = data access, `…DTO`/`…Factory`/`…Strategy` = helper), then the package (`swing`/`ui` = UI, `entity`/`domain` = domain). Start-up/configuration only when nothing else fits. Catalogue: `knowledge/element_roles.yaml`.
3. **Parts:** one per role (coarse: one per layer: presentation, application, domain, data access). Helpers join the one part that uses them; a data type used by several parts is listed, not drawn. Facts add the database (from the JDBC URL) and the web client (pages that call `/api`).
4. **Names:** name each part as an architect would (1–5 words, the system's own words, never a class name unless it has one class) with a one-line description; split a part into 2–3 only if its members do different jobs. Every member stays listed.
5. **Arrows:** one per pair of parts, only where their members have code dependencies; label with the intent for the pair of roles (e.g. "delegates requests", "reads and saves", "persists") and the protocol (HTTP/JSON, in-process, JPA / JDBC). Mark arrows the layering does not allow; list weak (< 3 dependencies) or implied ones instead of drawing them. Decomposition views draw no arrows.
6. **Draw in UML** (PlantUML), with a frame whose heading names the diagram kind (`mainframe pkg …`, `mainframe cmp …`; UML Annex A):
   - **decomposition, layered:** a UML package diagram. Each layer is `package "Layer" <<layer>>`, each part a `package` inside it with its main classes as `class` symbols (`hide circle`, `hide empty members`); the other members as a comment (`note "and 9 more"`). No arrows in decomposition views; layered views add `..> : <<use>>` dependencies. A database is not a module: leave it out.
   - **uses:** a package diagram, parts as packages with their main classes, `..> : <<use>>` between parts (UML 7.7.4: a usage is a dependency with «use»); the part being changed gets a comment `note "the part being changed"`.
   - **client-server and other C&C:** a UML component diagram. Each part is a `component` (UML 11.6.4) whose body lists what it does and, under `..realizations..`, its main classes; the database is a `component <<database>>`; arrows are dependencies `..>` labelled with the intent and the protocol in braces, e.g. `: delegates requests {HTTP/JSON}` (UML 11.6.5, Fig. 11.39).
   - **against the layering:** add the constraint `{against the layering}` to the arrow (a red colour may be added).
   - stereotypes only from the Standard Profile (`<<Entity>>` on the domain-model part), the notation keywords (`<<use>>`, `<<include>>`, `<<deploy>>`, …) or the Task2View profile (`<<layer>>`, `<<tier>>`, `<<database>>`, `<<external>>`). No C4 macros, no `database`/`cloud`/`queue`/`rectangle` shapes outside a use-case subject.

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

Viewpoints documented only as tables (interfaces, decisions, requirements, work assignment, implementation) are not UML diagram types and are not selected (ADR-008).

Every view lists, in `traceability`, each element's files and symbols.

### UML in PlantUML (the only notation; ADR-008)
Start every diagram with `mainframe <kind> <title>`, the kind from UML Annex A: `pkg`, `cmp`, `class`, `dep`, `sd`, `act`, `stm`, `uc`.

| Mark | PlantUML (UML clause) |
|---|---|
| layer or module group | `package "Name" as <alias> <<layer>> { … }` (12.2.4); the system in a context view: `component "Name" <<Subsystem>>` |
| component with responsibilities | `component "Name\n--\n- responsibility" as <alias>` (11.6.4); stereotype only if UML allows it (see the knowledge file) |
| entity | `class "Name" as <alias> { id : Long {id} … }` (11.4.4, 9.5.4) |
| datastore | component view: `component "Name" <<database>>`; deployment view: `node "Name" <<executionEnvironment>>` (19.4.4). Never the `database` cylinder |
| artifact / node | `artifact` (19.3.4) / `node` (19.2.4) |
| actor / use case | `actor` / `usecase`, inside `rectangle "System" { … }` for the subject (18.1.4) |
| relations | `..>` dependency (7.7.4), `..> : <<use>>` usage, `<<include>>`/`<<extend>>`/`<<deploy>>` on dependencies; `--|>` generalization; `..|>` realization; `*--` composition; `A "*" --> "1" B : label` association; `--` communication path between nodes |
| sequence | `participant` / `actor` lifelines (17.3.4); `A -> B : 1. message` synchronous, `A --> B` reply (17.4.4); `alt guard` … `end` (17.6.4) |
| communication | `object` lifelines with `A -- B : 1: message >` on the link (17.9.1) |
| activity | swimlanes `|Name|` declared before `start`, `:action;`, `if (guard) then (yes)` … `endif` (15.2–15.6) |
| state | `state`, `[*] --> S`, `S1 --> S2 : label` (14.2.4) |

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
1. **Notation:** the source compiles (if you can), the model kind matches the viewpoint, and it is UML 2.5.1 for its diagram type: only the symbols and paths [`../knowledge/uml-2.5.1.yaml`](../knowledge/uml-2.5.1.yaml) lists for it (a non-UML shape such as the `database` cylinder or a C4 macro is an error; a UML symbol of another diagram type is a warning), stereotypes from the Standard Profile, keywords or the Task2View profile, and a frame heading naming the kind.
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
