# Redesign 1 — The knowledge model (Phases 1–3)

*Draft, 2026-10-08. Addresses design review RC1 (no architecture model in the KB) and the KB side of RC4 (single view; no behavioural, data, or use-case view).*

**Decisions taken (2026-10-08):**
- Viewpoint selection is deterministic covering, not an LLM choice.
- The catalog is the full Views and Beyond set.
- GR10-Q3 gets a second view for "which parts depend on the persisted data".
- The order stays as in ADR-005: the viewpoint is chosen before the questions are written.

## 1. What is wrong today

- `concerns` mixes **quality attributes** (maintainability, performance) with **information needs** (control-flow, connectivity). Viewpoints are selected by overlap on this mixed list.
- The catalog is CIAO's six documentation sections. 6 of 14 concerns are framed by no viewpoint, control-flow among them, so a sequence diagram can never be chosen.
- Nothing maps a need to a viewpoint. The research plan's chain (stakeholder → task → concern → question → view type → required evidence → granularity) exists only as prompt prose.
- Grain is one free-text sentence per viewpoint (`nodes`, `relations`, `forbid`). Nothing checks it.
- The role is overridden on purpose, and "database engineer" maps to the security-analyst row.

## 2. Principle

The knowledge base is the **type system** of the pipeline. It defines the element kinds and relation kinds that the viewpoints draw, the Architecture Evidence Model stores, and Phase 8 checks. One vocabulary everywhere.

Selection is driven by **information needs**: what the stakeholder must see. Quality attributes (ISO 25010) only set emphasis, for example failure paths for testability. They never choose the diagram.

## 3. The Views and Beyond catalog

Source: Clements et al., *Documenting Software Architectures: Views and Beyond*, 2nd ed., 2010. The table of contents and index were checked against the publisher's sample pages. Page numbers are from that edition.

V&B distinguishes **generic** viewpoints (apply to every system) from **style** viewpoints (apply only if the system is built in that style, §9.2 Step 1). The catalog keeps that distinction as an `applies_when` predicate, evaluated on the repository card from Phase 0.

### 3.1 Module views (Ch. 1–2)
| id | V&B | Applies | Shows | Generable from code? |
|---|---|---|---|---|
| `decomposition` | 2.1 Decomposition | generic | modules, submodules, responsibilities; *is-part-of* | yes |
| `uses` | 2.2 Uses | generic | modules; *uses* (depends-on-correct-presence) | yes |
| `generalization` | 2.3 Generalization | when inheritance/interfaces are architecturally significant | *is-a*, *implements* | yes |
| `layered` | 2.4 Layered | when the code is layered (packages/naming, e.g. BCED) | layers, *allowed-to-use* | yes |
| `aspects` | 2.5 Aspects | when crosscutting mechanisms exist (AOP, filters, interceptors) | aspects, *crosscuts* | yes, if present |
| `data-model` | 2.6 Data Model | when there is persisted or structured data | entities, attributes, keys, associations, multiplicity | yes (entities, JPA, SQL) |

### 3.2 Component-and-connector views (Ch. 3–4)
| id | V&B | Applies | Shows |
|---|---|---|---|
| `cnc-generic` | Ch. 3 C&C | generic | runtime components, ports, connectors, attachments |
| `pipe-and-filter` | 4.2.1 | data-flow systems | filters, pipes |
| `client-server` | 4.3.1 | requester/provider split (REST API, GUI→service) | clients, servers, request/reply connectors |
| `peer-to-peer` | 4.3.2 | peers that both request and provide | peers, call-return connectors |
| `soa` | 4.3.3 | services, ESB, registries | service providers/consumers, ESB |
| `publish-subscribe` | 4.4.1 | event bus/listeners | publishers, subscribers, event bus |
| `shared-data` | 4.5.1 | central datastore accessed by many components | repository, accessors, data readers/writers |
| `tiers` | 4.6.2 (crosscutting) | multi-tier runtime (UI / app / DB) | tiers, *allowed-to-communicate* |
| `communicating-processes` | 4.6.1 (crosscutting) | threads/processes/concurrency | processes, threads, synchronisation |

### 3.3 Allocation views (Ch. 5)
| id | V&B | Applies | Shows |
|---|---|---|---|
| `deployment` | 5.2 | generic when deploy/config evidence exists | software elements → nodes, environments, communication paths |
| `install` | 5.3 | build/packaging evidence (Maven, Docker) | artifacts → file structure, containment |
| `implementation` | 5.5 (p. 207) | generic | modules → source files/directories |
| `data-stores` | 5.5 (p. 207) | when persisted data exists | data entities → databases/schemas |
| `work-assignment` | 5.4 | only with ownership evidence (git authors, CODEOWNERS) | modules → teams/people |

### 3.4 Behaviour (Ch. 8)
| id | V&B | Applies | Shows |
|---|---|---|---|
| `use-case` | 8.3.1 traces (p. 458) | generic | actors, use cases, include/extend |
| `sequence` | 8.3.1 traces (p. 298, alt/loop frames) | generic | lifelines, ordered messages, fragments |
| `communication` | 8.3.1 traces (p. 299) | generic | objects/components, numbered links |
| `activity` | 8.3.1 traces (p. 301) | generic | actions, decisions, forks, swimlanes |
| `state-machine` | 8.3.2 comprehensive (p. 303) | when an element has a lifecycle (e.g. report status) | states, transitions, guards |

### 3.5 Beyond the basics and beyond views (Ch. 6, 7, 10)
| id | V&B | Applies | Output |
|---|---|---|---|
| `context` | 6.3 Context diagrams | generic | system, actors, external systems, datastores at the boundary |
| `interfaces` | Ch. 7 | generic | interface specs: resources provided, syntax, semantics, errors |
| `variation-points` | 6.4 | when variability exists (profiles, flags, plugins) | variation points and mechanisms |
| `decisions` | 6.5 | only with recorded decisions (ADRs, docs) | decision records; otherwise a declared gap |
| `requirements-mapping` | 10.3 | only with requirement docs | requirement → element table |
| *mechanism* `combined` | 6.6 Combining views | — | not a viewpoint: rules for overlaying, e.g. layered + decomposition, or C&C + deployment |

**Total: 30 entries** (6 module, 9 C&C, 5 allocation, 5 behaviour, 5 beyond). Combined views (§6.6) are how we keep the expert's "layers around the components" without inventing a new viewpoint: `decomposition`/`cnc-generic` combined with `layered` for grouping.

### 3.6 What the catalog does *not* cover
Quality-specific views (security, performance) appear in V&B only through the Rozanski & Woods comparison in the Epilogue (p. 404, "security views"). They are not V&B styles, so they are left out. They can be added later as R&W perspectives.

## 4. Information needs (selection vocabulary)

Every catalog entry frames one or more needs. A goal may raise several.

| need | Framed by |
|---|---|
| `actors-goals` | use-case |
| `boundary` | context |
| `decomposition` | decomposition |
| `layering` | layered, tiers |
| `dependencies` / `change-impact` | uses |
| `inheritance-extension` | generalization, variation-points |
| `crosscutting` | aspects |
| `collaboration` (which parts work together, via which interfaces) | cnc-generic or the applicable C&C style |
| `interaction-order` (incl. failure paths) | sequence, communication |
| `process-flow` | activity |
| `lifecycle` | state-machine |
| `data-structure` | data-model |
| `data-storage` | data-stores, shared-data |
| `concurrency` | communicating-processes |
| `deployment` | deployment |
| `build-packaging` | install |
| `code-location` | implementation (and attached to every view as the traceability appendix) |
| `ownership` | work-assignment |
| `interface-contract` | interfaces |
| `rationale` | decisions |
| `requirement-traceability` | requirements-mapping |

**Implemented (step 1):** 22 needs. Dependencies and change-impact are separate ids, both framed by `uses`. Each need has a category (structure / behavior / allocation / beyond), and behaviour viewpoints never cover structural needs. This encodes the expert's "second view" finding.

**C&C style resolution.** `collaboration` is framed by `cnc-generic`. If the repository card shows a style (for example client-server from a REST controller plus a GUI client, or publish-subscribe from listeners), the most specific applicable style replaces `cnc-generic`. The style is decided from repository evidence, not from goal wording.

## 5. Records

### 5.1 Viewpoint record
```yaml
- id: sequence
  vb_ref: "8.3.1 Notations for capturing traces"
  family: behavior
  applies_when: generic
  frames: [interaction-order]
  element_kinds: [actor, lifeline]
  relation_kinds: [message, return]
  fragments: [alt, opt, loop]
  scope: one scenario per view
  granularity:                       # picked by Phase 1 detail_level
    overview: {max_elements: 5, fragments: []}
    feature:  {max_elements: 8, fragments: [alt]}
    detailed: {max_elements: 12, fragments: [alt, opt, loop]}
  evidence: [code, web, test]        # Phase 0 corpus classes Phase 4 must search
  constraints:                       # named predicates, implemented once in Phase 8
    - lifeline_is_component_or_actor
    - messages_ordered
    - message_backed_by_call_evidence
    - no_package_or_directory_element
  combine_with: [layered]            # stereotypes <<boundary>>/<<control>>/<<entity>> when layers are known
  notation: {plantuml: sequence, mermaid: sequenceDiagram}
```

### 5.2 Phase 1 profile additions
- `needs: [{need, evidence_span}]`: closed vocabulary from §4. Each need cites the words of the goal that raise it.
- `subjects: [..]`: the enumerated items of the goal, e.g. "checking seat availability", "notification service". One per item.
- `detail_level: overview | feature | detailed`.
- `quality_attributes: [..]`: ISO 25010, for emphasis only.

### 5.3 Stakeholder roles as priors
Roles carry V&B Table 9.1 weights per viewpoint family (`d`, `s`, `o`). A role prior is used only when the goal states no need, and to break ties. Alias fix: "database engineer" becomes a `data-engineer` role whose prior favours `data-model` and `data-stores`.

## 6. Pipeline order (ADR-005 kept)

```
Phase 0  repository card (corpus classes, packages, style evidence)  ← deterministic, cheap
Phase 1  profile: needs, subjects, detail level, quality attributes   ← LLM
Phase 3  covering selection over applicable viewpoints               ← deterministic
Phase 2  questions per selected view, at its grain, one per subject  ← LLM
```

1. Keep only viewpoints whose `applies_when` holds on the repository card.
2. Choose the smallest set of viewpoints that frames every need (cap 3). Break ties by role prior, then by catalog order.
3. Resolve C&C styles and apply `combine_with` overlays (layers).
4. Assign each subject to the view that frames it. Phase 2 writes the questions for each view from its subjects and its grain, so questions cannot leak another view's grain. This was the reason for ADR-005's order; it still holds.

## 7. Check against the pilot

| Goal | Needs | Views selected | Expert expected |
|---|---|---|---|
| IS-seat-L1 | collaboration | client-server C&C (+ layered overlay) | components + layers ✓ |
| IS-seat-L2 | collaboration, interaction-order, change-impact | C&C + sequence (+ uses for "which parts are affected", cap 3) | component + sequence ✓ |
| IS-seat-L3 | same, 5 subjects (request handling, availability, rules, storage, notification) | C&C (detailed) + sequence (alt) + uses | component + sequence ✓ |
| IS-reg-L1 | collaboration | C&C | plain agent's L1 accepted ✓ |
| IS-reg-L2 | collaboration, interaction-order, interface-contract | client-server C&C + sequence | component + sequence ✓ |
| IS-reg-L3 | same, 5 subjects incl. invalid/duplicate paths | C&C + sequence (alt fragments) | component + sequence ✓ |
| GR10-Q1 | decomposition, layering, dependencies, collaboration | decomposition + C&C, both with the layered overlay (C&C also covers dependencies) | macro-components / layers ✓ |
| GR10-Q2 | deployment, build-packaging | deployment (also covers build-packaging) | deployment ✓ |
| GR10-Q3 | data-structure, change-impact | **data-model + uses** (dependents of the persisted entities) | entities with attributes ✓; second view per decision |
| GR10-Q4 | actors-goals | use-case | use-case ✓ |

Notes:
- The second view for GR10-Q3 is V&B's **uses** style. "Which parts depend on X" is exactly what the uses relation answers, and it is drawn at component grain. The expert criticised extra *layers* in the plain agent's diagram, not a separate dependency view.
- Change-impact on IS-seat-L2/L3 brings in `uses` as a third view. If three views is too many, the cap or the role prior can drop it, and its content moves to the traceability appendix.

These ten rows are the golden tests in `code/tests/fixtures/pilot_goals.yaml` / `test_selection.py`, which run without an LLM by fixing the Phase 1 output. The table reflects the implemented selection.

## 8. Settled points (2026-10-08)

1. **Non-code evidence.** Work-assignment, decisions and requirements-mapping (and any viewpoint whose evidence is missing) are **selected and reported as a declared gap**. The need stays visible to the stakeholder, as the research plan requires ("unanswered questions and limitations must remain visible"). They are not silently dropped.
2. **View cap: 3** per goal.
3. **ISO/IEC/IEEE 42010:2011 vocabulary**: system of interest, stakeholder, concern, architecture viewpoint, architecture view, model kind, architecture model, correspondence, correspondence rule, architecture rationale. A move to 2022 terms (entity of interest, view component, aspects) is deferred.
