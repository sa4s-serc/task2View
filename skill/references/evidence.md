# Phase 5 — Claims, verification and the evidence model

The pipeline does this in `code/src/task2view/phase5/` (`agent.py`, `verify.py`, `consolidate.py`). Follow the same rules so your `evidence_model.json` is comparable.

## 1. Claims
A claim states **one** fact and has at least one **citation**:
`{"file": "path relative to --code", "symbol": "symbol id (optional)", "lines": [start, end], "excerpt": "text copied exactly from those lines"}`

| kind | fields |
|---|---|
| `element` | `element_kind` (a kind the view allows; `actor` / `use_case` for people and use cases), `name` (the code's name), `symbol` (fully qualified id for code elements), `responsibilities` (short phrases), `attributes` (entities: `{name, type, key}`) |
| `relation` | `source`, `target` (symbol ids), `relation` (a relation kind of the view), `label` (operation) |
| `interaction` | `scenario` (short name, the same for all its steps), `order` (1, 2, …), `source`, `target`, `label` (`method(args)`), `condition` (guard of an alternative or failure path, else null) |
| `state` / `transition` | `name`; or `source`, `target`, `label` |

Also record `id` (`C1`, `C2`, …), `task` (the investigation task id), `question_ids`, and `confidence` (0–1).

Rules:
- Copy each excerpt exactly from lines you have read, and give those lines.
- Names are the code's names. A responsibility goes in its own field, never inside a name.
- One fact per claim. If the code does not show something, do not claim it.

## 2. Verification (do this for every claim)
Reject the claim, with the reason, unless **at least one** citation passes all of these checks:
1. The file exists in the repository and is not a UML model or binary.
2. The first cited line exists.
3. The excerpt contains at least one word of 3 or more characters (`}` alone locates nothing).
4. The excerpt occurs, ignoring whitespace differences, within the cited lines (3 lines of slack either side).
5. If the citation names a symbol, that symbol exists.

Then check the claim itself:
- An **element** claim must name a real symbol, except `actor`, `use_case`, `node`, `execution_env`, `artifact`, `datastore`, `external_system`, `system`, `state` and the other non-code kinds.
- **Relation** and **interaction** endpoints must be real symbols (an interaction's source may be an actor).

**Support** is decided by these checks, not by your opinion:
- `documented`: every passing citation is in documentation files.
- For a relation or interaction:
  - `observed`: the source code depends on the target **in that direction** (a call, field, parameter, instantiation or inheritance), or the excerpt contains the target's name or the called method as a whole word.
  - `inferred`: otherwise. Cap its confidence at 0.7.
- For an element: `observed` when a passing citation is in the file that declares its symbol, else `inferred`.
- `observed` means the cited code exists where the claim says. It does not prove the wording: responsibilities are your reading of that code.
- A `Type.member` reference counts only if the type has that method, field or constant. A simple name that matches several symbols counts only if exactly one of them is in a cited file.

Keep rejected claims in `rejected_claims` as `{"task", "claim", "reason"}`.

## 3. Evidence model (consolidation)
Build it from the verified claims and the repository card only.

**Components.** The grain follows the goal's scope and detail level:
- **whole-system overview** (detail level overview and no target): one component per package (Python/JS: module) that holds a candidate: id `cmp:<package>`, name = the package's last segment, `realized_by` = its candidates. Skip the anchor rules below.
- **a request about a specific feature (a target is set), or feature / detailed level:** the anchor rules below.

- Every non-test code symbol that a claim is about (as `symbol`, `source` or `target`) is a candidate.
- **Merge** an interface with exactly one implementation among the candidates into that implementation.
- **Helpers** are enums, records, and names ending in `Exception`, `Error`, `DTO`, `Dto`, `Request` or `Response`. They do not become components: attach each helper to the one candidate it has code links with. A helper linked to several candidates, or to none, stays its own component.
- Every other candidate is a component:
  - id `cmp:<symbol id>`;
  - **name = the class or module's simple name**;
  - `realized_by`: its symbol and the merged and attached symbols;
  - `layer`: from the layer aliases;
  - `responsibilities`: from its element claims, without duplicates.

**Relations between components**
- For every code dependency between members of two different components, add one relation per pair:
  - `uses` for calls, fields, parameters, return types and instantiation;
  - `generalization` for extends and implements.
- Label: the most frequent called method names (at most 2).
- Keep the member dependencies as `member_edges`, written `src -kind-> tgt (file:line)`.
- A relation claim between two elements adds its claim id to the matching relation, or creates one.
- **Reflexion:** list every relation between two components under `reflexion` as `convergence` (it has member edges and claims), `divergence` (member edges, no claim: a possible omission) or `absence` (claims, no member edge).

**Non-code elements from claims:** actors, use cases and similar get the id `<kind>:<slug of name>`.

**Entities** (from persistence facts)
- id `ent:<symbol id or table name>`.
- `attributes`: the persisted fields, with `key` and `foreign_key`. Static and transient fields are excluded. A field that references another entity is **not** an attribute (it becomes an association), unless it is embedded.
- **Associations:** many-to-one, one-to-one, one-to-many and many-to-many fields. Draw a bidirectional pair once. `multiplicity` is written as `source..target`, e.g. `*..1`.
- **Composition:** embedded fields.

**Deployment** (from deployment and build files)
- **artifacts:** one per build unit, named `<artifact id>.<packaging>`.
- **nodes:** application services in compose files.
- **datastores:** database images in compose, or the database of a JDBC URL. A URL whose host is a compose service is that same datastore.
- **execution environments:** Dockerfile base images.
- **relations:** `deploys` from an artifact to its node; `communicates` from an artifact to each datastore, labelled with the technology.

**States**
- the constants of enums whose name ends in `Status` or `State`;
- the classes implementing a `*State` or `*Status` type;
- `state` and `transition` claims.

**Scenarios**
- Group interaction claims by scenario name and sort them by `order`.
- Merge identical steps (same order, endpoints and message) and keep all their claim ids.
- Each distinct `condition` becomes an `alt` fragment, and its steps refer to it.
