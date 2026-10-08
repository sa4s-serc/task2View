# ADR-006 — Knowledge model, Architecture Evidence Model, and projected views

- **Status:** accepted (design). Implementation in progress.
- **Date:** 2026-10-08
- **Supersedes:**
  - ADR-002 D1–D3 (static scopers and a packed prompt *instead of* Phases 4–6 agents)
  - ADR-005 D1 (correspondence ranking overwritten by an LLM pick) and D4 (one view per run)
  - ADR-003 D2 (critic notes only)
- **Restores:** ADR-001 D6–D7 (the graph is a tool, not an inclusion filter; agents investigate with repository tools)
- **Keeps:**
  - ADR-005 phase order: viewpoint chosen before the questions are written.
  - ADR-004 D1 language neutrality (now via tree-sitter) and D5 (YAML-selectable plug-ins).
- **Design documents:** [01 knowledge model](../redesign/01-knowledge-model.md), [02 evidence and architecture model](../redesign/02-evidence-and-architecture-model.md), [03 views, reconciliation, validation](../redesign/03-views-reconciliation-validation.md)
- **Evidence for the decision:** [design review 2026-10](../design-review-2026-10.md), root causes RC0–RC5, and the pilot in `experiments/pilot-2026-09/`.

## Context

The pilot showed six root causes, five of them design-level:
- two incompatible evidence philosophies stacked (RC0);
- no architecture model in the knowledge base (RC1);
- lexical file selection (RC2);
- no consolidation of evidence (RC3);
- a view contract that cannot express layers, responsibilities, attributes, order or several views (RC4);
- no closed loop between Phases 6 and 8 (RC5).

Prompt tuning cannot fix contracts that cannot carry the information.

## Decisions

### D1. Knowledge model (01)
- The catalog is the full Views and Beyond 2nd-edition set: 30 entries, each with an `applies_when` predicate.
- Selection is deterministic covering over typed information needs, extracted in Phase 1. The cap is 3 views.
- Role priors (V&B Table 9.1) only break ties.
- Viewpoints without evidence are selected and reported as declared gaps.
- Vocabulary is ISO/IEC/IEEE 42010:2011.

### D2. Evidence and the Architecture Evidence Model (02)
- **Phase 0:** a deterministic repository card. Typed corpus, tree-sitter symbol table, directed dependency graph from code only.
- **Phases 4–5:** agents with repository tools. Investigation tasks per (view, subject), an open boundary, claims mechanically verified.
- **Phase 5b:** consolidation into the AEM. Symbol registry, class→component clustering named by the LLM, lifted relations, scenarios, correspondences.
- **Documentation:** counts as `documented` evidence. UML model files are evaluation references, never evidence.
- **Scopers:** kept as suggestions and ablation baselines only.

### D3. Views, reconciliation, validation (03)
- **Phase 7:** a deterministic projection of the AEM per viewpoint into View format v2: nesting, stereotypes, responsibilities, attributes, ordered interactions and fragments, traceability. The LLM only words things.
- **Notation:** every adapter renders every model kind, natively or by documented approximation.
- **Phase 6:** rule-based decisions per view: confirm, simplify, split, request_evidence (≤2 rounds), gap, drop.
- **Phase 8:** five validation layers. Notation, viewpoint constraints and faithfulness are hard checks; coverage and consistency come next. Task fit is judged by a different model and stays soft until calibrated (Track 2). At most 2 projection retries.

### D4. Pluggable LLM
- `LLMClient` adapters for Gemini, Anthropic, OpenAI and OpenAI-compatible servers, chosen from a `provider:model` spec.
- The project moves to a stronger model for runs.
- Already implemented: commit e0e8ebe.

## Consequences

- Every drawn mark traces to an AEM id, so Phase 8's checks are lookups. A pass now means the view is faithful, well-formed and covers its questions, not only that names resolve.
- **More model calls per run** (tool loops, several views). This is acceptable with a stronger model, and every call is attributable to a phase and a view.
- **The pilot's Task2View batch is not comparable** with runs under this ADR. The next evaluation re-runs all conditions on the same code and goals.
- **Implementation order:**
  1. knowledge model and selection (golden tests on the 10 pilot goals)
  2. Phase 0 card
  3. AEM with Phases 4–5
  4. View format v2, projection and renderers
  5. Phases 6 and 8
  6. re-run the pilot
