# ADR-006 — Knowledge model, Architecture Evidence Model, and projected views

- **Status:** accepted. Implemented (steps 1–5 and the v2 orchestrator, 2026-10-08); revised after a literature check (addendum, 2026-10-09); not yet evaluated with a live model.
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
- **Phase 5b:** consolidation into the AEM. Symbol registry, deterministic class→component grouping named after code (package or anchor class; see addendum A2), lifted relations, scenarios, correspondences.
- **Documentation:** counts as `documented` evidence. UML model files are evaluation references, never evidence.
- **Scopers:** kept as suggestions and ablation baselines only.

### D3. Views, reconciliation, validation (03)
- **Phase 7:** a deterministic projection of the AEM per viewpoint into View format v2: nesting, stereotypes, responsibilities, attributes, ordered interactions and fragments, traceability. The LLM only words things.
- **Notation:** every adapter renders every model kind, natively or by documented approximation.
- **Phase 6:** rule-based decisions per view: confirm, simplify, split, request_evidence (≤2 rounds), gap, drop.
- **Phase 8:** five validation layers. Notation, viewpoint constraints and faithfulness are hard checks; coverage and consistency come next. Task fit is judged by a model from a different family and stays soft until validated against ratings by at least two people (Track 2; addendum A6). At most 2 projection retries.

### D4. Pluggable LLM
- `LLMClient` adapters for Gemini, Anthropic, OpenAI and OpenAI-compatible servers, chosen from a `provider:model` spec.
- The project moves to a stronger model for runs.
- Already implemented: commit e0e8ebe.

## Consequences

- Every drawn mark traces to an AEM id, so Phase 8's checks are lookups. A pass now means the view is faithful, well-formed and covers its questions, not only that names resolve.
- **More model calls per run** (tool loops, several views). This is acceptable with a stronger model, and every call is attributable to a phase and a view.
- **The pilot's Task2View batch is not comparable** with runs under this ADR.
- **Generality is a design requirement.** Rules, priors and thresholds come from general sources (V&B, ISO 42010, the catalog definitions) or from config with stated provenance, never from fitting the pilot. The pilot goals are a regression set; evaluation uses goal sets and repositories beyond it.
- **Implementation order:**
  1. knowledge model and selection (golden tests on the 10 pilot goals)
  2. Phase 0 card
  3. AEM with Phases 4–5
  4. View format v2, projection and renderers
  5. Phases 6 and 8
  6. evaluate on goal sets across repositories, roles and models (the pilot is one regression set)

## Addendum A — after the literature check (2026-10-09)

Source: `reports/Task2View design literature check.md` (notes in `research_notes/`), at the root of the research folder. It found the overall shape supported: a deterministic static summary before agents, small tool sets with step budgets, verification outside the model, deterministic projection, and rule gates with a soft judge. It found the following under-specified, and they were changed:

- **A1. Phase order, reworded, not reordered.** Views & Beyond §8.2.1, ATAM and Kruchten put questions before viewpoints. Phase 1's typed needs are those concern-level questions (42010 concerns); Phase 3 picks viewpoints that frame them; Phase 2 then refines each need into questions at the chosen viewpoint's grain. The selection rationale (which needs each viewpoint covers, uncovered needs) is logged in every run.
- **A2. Component grain.** One component per class the claims mention is finer than any recovery ground truth (11–216 components) and ignores package structure, the strongest single grouping signal. Overview goals now get one component per package; feature and detailed goals keep class anchors. A helper used by several anchors stays its own component instead of being forced into one. Names always come from code.
- **A3. What "observed" means.** Verification proves the cited code exists where the claim says: an element is cited in the file that declares it; a relation has a graph edge in its direction or names its target. It is not an entailment check; responsibilities remain the agent's reading. `Type.member` resolves only for real members; ambiguous names resolve only through the cited file.
- **A4. Reflexion output.** Following reflexion models, every component relation is a convergence (claim and code edge agree), divergence (code edge no claim mentions: a possible omission) or absence (claimed without a code edge). Behavioural participants are checked against the set's structural views (42010 correspondence).
- **A5. Agent context and a baseline.** Older tool results are elided (observation masking), the stable prompt prefix carries a cache breakpoint, repeated calls are caught, and tool use is logged. A fixed-retrieval mode (`--evidence retrieval`: one call over the seeds' code, no tools) is the baseline that shows what agentic exploration adds.
- **A6. Judge.** One theme per call, with anchored levels and the reason before the score; the judge reads the diagram source and the view's facts. Notation, names and grain are checked by rules, not judged. The rubric (v1: answers-questions, second-view, layers, placement, layout) is frozen before experiment outputs are seen. The 18 expert comments are used descriptively only: the themes came from them, so agreement on them cannot validate the judge. No external diagram dataset is used. Validation needs pilot outputs rated blind by at least two people (`scripts/make_rating_sheet.py`, `scripts/judge_agreement.py`); a theme may gate only when judge–human agreement approaches human–human agreement.
- **A7. Study design.** The pilot is exploratory: 2 repositories × 10 goals, 3 runs each, the same generator model in every condition, a judge from another model family, and expected facts written per goal before generation (`experiments/pilot-2026-09/goals.yaml`). See `experiments/PROTOCOL.md`.
