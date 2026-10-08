# Redesign 2 — Evidence acquisition and the Architecture Evidence Model (Phases 0, 4, 5)

*Draft for discussion, 2026-10-08. Addresses design review RC0 (two philosophies stacked), RC2 (lexical evidence acquisition) and RC3 (no consolidation). Builds on [01-knowledge-model.md](01-knowledge-model.md): element and relation kinds come from the catalog there. Vocabulary: ISO/IEC/IEEE 42010:2011.*

## 1. The problem in the pilot, end to end

```
Phase 0 keeps only source code        → persistence.xml, pom.xml, registration.html gone
Phase 4 picks files by path substring → 8 files, alphabetical tie-break, PageRank discarded
Phase 5 reads only those files        → cannot follow a call to UserManager or ReservationManager
claims → boxes 1:1                    → SeatDTO as a component; InternalNoteGUI three times
```

Every later phase can only filter what Phase 4 picked. That is why the views contain the wrong things, not just too few things.

## 2. Principle

Go back to the research plan's split (§1.5, Phases 4–5). **Agents decide what is relevant and how to abstract it. Deterministic analysis supplies facts and checks claims.** The published scopers (PageRank, LocAgent hops, …) become *suggestions and tools* offered to the agent, plus ablation baselines. They are never the inclusion filter again.

Everything recovered goes into **one Architecture Evidence Model (AEM)**: the 42010 *architecture model* that every view is projected from. Because views share it, they share element identities. Cross-view consistency (a research-plan Phase 8 criterion) then comes for free.

## 3. Phase 0 — Repository card (deterministic, no LLM)

### 3.1 Typed corpus
Every file gets a class instead of a keep/drop decision:

| class | examples | used by |
|---|---|---|
| `code` | `.java`, `.py`, `.ts` | all |
| `test` | `src/test/**`, `*Test.java` | sequence, use-case (scenarios), interfaces |
| `build` | `pom.xml`, `build.gradle`, `package.json` | install, deployment |
| `deploy` | `Dockerfile`, `docker-compose.yml`, k8s yaml | deployment |
| `config` | `application.properties`, `persistence.xml`, `.env.example` | deployment, data-stores, C&C style |
| `schema` | `*.sql`, migrations | data-model, data-stores |
| `web` | `static/*.html`, `*.js` routes | client-server, use-case |
| `docs` | README, `*.md`, design docs | context, decisions, requirements-mapping (support = *documented*) |
| `model` | `.vpp`, `.puml`, exported diagrams | **never evidence** for generation (they are the reference for evaluation) |
| `binary` | images, jars, pdf | skipped |

Each viewpoint's `evidence:` list (01 §5.1) names the classes Phase 4 must search for it.

### 3.2 Facts (static analysis as a tool, not a filter)
- **Symbol table:** types, methods, fields, annotations, file and line span.
- **Directed dependency graph** from imports, type references, instantiation, inheritance and calls resolved through declared types. Edges come from code only; strings and comments are ignored. Test files are flagged. This replaces the co-mention graph (design review RC2: 18% of today's edges come from strings).
- **Package tree** with sizes and a layer guess (`architectural_styles.yaml` aliases: boundary/control/entity/database, controller/service/repository, …).
- **Entry points:** `main`, `@SpringBootApplication`, `@RestController` routes, Swing frames, CLI.
- **Persistence facts:** `@Entity` classes with fields, `persistence.xml` units, SQL tables.
- **Style evidence** for the `applies_when` predicates in 01: REST controller + client → client-server; listeners/event bus → publish-subscribe; threads/executors → communicating processes; layered packages → layered; interceptors/aspects → aspects; ADR files → decisions; git authors → work assignment.

The card is a compact text summary of these facts (≈1–2k tokens). It is the "repository summary" every later agent sees.

## 4. Phase 4 — Investigation plan (agent, card + tools)

Input: the card, the selected views, each view's assigned subjects and questions, and the viewpoint records.

Output: one **investigation task per (view, subject)**:

```json
{"id": "IT3", "view": "V2-sequence", "subject": "duplicate account",
 "need": "interaction-order",
 "seeds": {"symbols": ["AuthenticationController.register", "UserManager"],
           "dirs": ["controller/", "entity/"], "classes": ["code", "test", "web"]},
 "expect": {"elements": ["lifeline"], "relations": ["message"], "fragments": ["alt"]},
 "suggested_by": ["entry-point", "pagerank", "search:register"],
 "budget_steps": 10}
```

- Seeds come from the card (entry points, symbols, packages) and from tool calls (`search`, `list_tree`). Scoper outputs (PageRank, 1-hop) are offered as *suggestions* with their origin, so a run's label matches what was really used.
- **The budget scales with the goal:** steps per task are set by the detail level and the number of subjects. There is no fixed 8-file cap.
- The plan is grounded: every seed must exist in the card's symbol table or corpus. It is not closed: Phase 5 may go beyond it.

## 5. Phase 5 — Evidence extraction (agents, bounded tool loop)

One agent per investigation task, running the existing `AgentRuntime.tool_loop` with `RepoTools` (`list_tree`, `search`, `read`, `graph_query`, `traverse_graph`, `edges_among`). Both exist today and are unused. **The boundary is open:** the agent may read any file of the task's evidence classes.

### 5.1 Claim schema
```json
{"id": "C17", "task": "IT3",
 "kind": "relation", "relation": "message",
 "source": "UserManager", "target": "UserRegistry",
 "label": "institutionalEmailExists(email)", "order": 3, "scenario": "register user",
 "condition": "email already registered → IllegalArgumentException",
 "evidence": [{"file": "JavaProject/src/main/java/it/unina/reservations/controller/UserManager.java",
               "symbol": "UserManager.register", "lines": [77, 78],
               "excerpt": "if (userRegistry.institutionalEmailExists(email)) {"}],
 "support": "observed", "confidence": 0.9}
```
Element claims carry `element_kind`, `responsibilities[]` (each with evidence) and `attributes[]` (for entities).

### 5.2 Mechanical verification (no LLM)
- The excerpt must occur in the file within the stated lines; the symbol must exist in the card's symbol table. Otherwise the claim is dropped.
- `uses`/`message` claims are checked against the dependency graph. A graph edge confirms them as `observed`. No edge means the claim is downgraded to `inferred` or `weak`, unless the excerpt itself shows the call.
- **Support classes** (research plan §5): `observed` · `inferred` (from several artifacts) · `weak` · `documented` (from `docs` only). Confidence comes from the agent; verification can cap it.

## 6. Phase 5b — Consolidation into the AEM

This step does not exist today. Deterministic, except one bounded LLM step for naming components.

### 6.1 Code registry
One entry per real symbol, keyed by fully qualified name. Aliases (`InternalNoteGUI`, `Boundary.InternalNoteGUI`, `boundary.InternalNoteGUI`) resolve to the same entry. This fixes the GR10-Q3 duplicates at the source.

### 6.2 Architectural elements
```json
{"id": "cmp:user-management", "kind": "component", "name": "UserManager",
 "realized_by": ["it.unina.reservations.controller.UserManager",
                 "it.unina.reservations.controller.factory.StudentFactory", "…"],
 "layer": "control",
 "responsibilities": [{"text": "validates registration data", "claims": ["C12"]},
                      {"text": "enforces account uniqueness", "claims": ["C17"]}],
 "support": "observed"}
```
- **Class → component abstraction.** Component candidates are proposed deterministically: clusters of the dependency graph within a package, plus helper classes (factories, DTOs, exceptions) attached to the type that uses them. The LLM then merges, splits and names them, under one constraint: every member must be in the registry, and names must be a member symbol or a responsibility phrase marked as such. The detail level decides granularity: `overview` gives coarse clusters, `detailed` gives one component per significant type.
- Entities, attributes, nodes, artifacts, actors and use cases come from typed claims plus card facts (`@Entity` fields, `persistence.xml`, Docker, controllers and tests).

### 6.3 Relations and scenarios
- **Lifted relations:** component A *uses* B if a member of A uses a member of B in the graph. Each lifted relation keeps the member edges and claims behind it, so Phase 8 can check it.
- **Scenarios:** ordered message lists per subject, with alternative branches and their conditions, for sequence, communication and activity views.

### 6.4 Correspondences (42010)
- Each architectural element has one id across all views.
- Each correspondence records how elements relate across views, for example `component realizes data-model entity` or `component deployed-in artifact`.
- The research plan's "names must be consistent across views" becomes a check on ids, not on strings.

## 7. Does it fix the pilot's failures?

| Pilot failure | Cause today | Under this design |
|---|---|---|
| GR10-Q3 drew GUIs for a DB goal | "boundaries" matched `Boundary/`; `Database/` cut alphabetically | Data-model view searches `schema`/`config` classes and `@Entity` facts. No path-substring seeding. |
| IS-reg-L3 drew seat-booking managers | "manage" matched 3 managers before `UserManager` (9th, cut) | Seeds from entry point `register` route → call chain → `UserManager`; agent follows calls |
| IS-seat-L3 had 3 boxes | "reservations" dropped by IDF; 2 files kept | Budget scales with 5 subjects; `ReservationManager` reachable from the booking entry point |
| GR10-Q2 had classes as nodes | `pom.xml`, `persistence.xml` dropped in Phase 0 | `build`/`config` classes are evidence for deployment |
| `InternalNoteGUI` ×3 | name variants + Phase 8 rename | Registry resolves aliases before any view exists |
| "User Dashboard Boundary Component" | invented label, borrowed symbol | Names must be a member symbol or a marked responsibility phrase |
| PageRank label was false | plan filtered PageRank candidates out | Suggestions carry their origin; the run records what was used |

## 8. Decisions (2026-10-08)

1. **Parser: tree-sitter**, Java first. Keeps ADR-004's language-neutral goal.
2. **Documentation counts as evidence**, with support class `documented`. It can back context, decisions and requirements-mapping. `model` files (VPP, exported UML) stay excluded, because they are the reference for evaluating the views.
3. **The model is pluggable, and the project moves to a stronger model.** Implemented in `code/src/task2view/llm/`:
   - **Adapters:** one `LLMClient` adapter per provider: Gemini (REST), Anthropic (`anthropic` SDK), OpenAI, and OpenAI-compatible presets (OpenRouter, Ollama, vLLM, any base URL; `openai` SDK).
   - **Strategy:** the adapter is chosen at run time from a `provider:model` spec, set by `--llm`, config `llm:`, or `TASK2VIEW_LLM`.
   - **Interface today:** `complete_json` only. Native tool calling for the Phase 5 loop gets added to this same interface when Phase 5 is rebuilt.
4. **Component abstraction: deterministic clustering, then LLM naming.** Every member of a component must be a real symbol.
