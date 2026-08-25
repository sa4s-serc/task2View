# ADR-003 — Graph-grounded structure and a completeness critic

- **Status:** superseded in part by [ADR-004](ADR-004-filesystem-graph-and-config.md)
- **Date:** 2026-08-24
- **Supersedes:** none (extends [ADR-002](ADR-002-sota-plugins.md); does not revive ADR-001 D5–D7)
- **Decided in:** review of PageRank + CIAO runs (misplaced packages, sparse relations) plus recent recovery / agent literature

## Context

ADR-002 kept Phases 1–3 as knowledge-grounded agents and made scoping / extraction / notation **plug-ins**. That split is still right: reviewers rejected LLM-only grounding, and homemade ReAct extractors were weaker than a typed graph plus a published scoper.

The PageRank + CIAO runs then showed two failure modes the plug-ins do not catch:

1. **Wrong organisation.** Types are placed in the wrong package or layer (Entity types in a “Presentation” group, Boundary GUIs in “Persistence”). The Java graph already has the path and a layer tag; the extractor is allowed to ignore both. Sample merge can also remap element ids and leave group `contains` pointing at the wrong ids.
2. **Incomplete structure.** The overall shape is plausible, but uses/calls/inherits edges that exist among the selected types are omitted. Completeness of *relations among selected elements* is a graph lookup, not a generation task.

Meeting notes already asked for tools and knowledge, not more ungrounded agents. Recent work points at the same split:

| Source | What we take | What we do not take |
|---|---|---|
| ArchAgent (2026) | Static analysis + LLM synthesis; missing relations and architectural drift are the stated failure modes | Their full multi-repo analysis loop |
| SemRef (2026) | LLM refinement of a recovered architecture must be constrained by structural dependencies; mixed-package clusters are a known SAR error | Training a separate recovery tool |
| LocAgent (ACL 2025) | Graph tools (search / traverse / retrieve) so the agent navigates a typed graph instead of grepping files | Vendoring their SWE-bench harness |
| AgenticAKM (2026) | Extract → retrieve → generate → **validate** as separate roles | A fourth documentation-only agent |
| MAAD (2026) | Evaluator with external knowledge, not self-critique | Per-view-type agent swarm (meeting notes: overkill) |
| Reflexion / tool-grounded reflection | Critique needs **external** evidence; internal “think again” repeats the same hallucination | An unconstrained retry loop |

So: keep ADR-002 plug-ins as the first extract. Add **deterministic structure grounding** (graph is source of truth for package membership and edges among selected types). Add **one** completeness critic that may propose extra neighbours, and accept a proposal only if the graph contains that type.

## Decision

### D1. After extraction, always run structure grounding (not an LLM)

`agents/structure.py` rebuilds groups from the repository graph (path + layer, canonicalised through `architectural_styles.yaml`) and inserts missing uses/calls/inherits edges among **already selected** elements. Evidence files are rewritten to the graph path of the type. This is the fix for “components in the wrong package”.

### D2. Completeness critic is one optional agent with graph tools

`agents/phase6_critic.py` sees the grounded view, the unanswered questions, and a **diagnosis** computed from the graph (missing neighbours, unused edges). It may name extra types to add. The orchestrator adds a type only if it exists in the graph, then runs D1 again.

This is not ADR-001 Phase 6 (need–evidence reconciliation that restated unanswered questions). It is ArchAgent/SemRef-shaped: critic + static evidence.

`--skip-critic` disables D2. D1 still runs.

### D3. Tools grow LocAgent-style graph operations

`RepoTools` keeps `list_tree` / `search` / `read` / `graph_query` and adds:

- `traverse_graph` — hop neighbourhood (LocAgent TraverseGraph)
- `edges_among` — uses/calls/inherits inside a named set
- `missing_neighbors` — 1-hop types not in the current view
- `package_of` — path + canonical layer

Agents still cannot invent files. The graph remains a **queryable tool**, not the inclusion filter for scoping (ADR-001 D6).

### D4. Knowledge gains architectural styles

`knowledge/data/architectural_styles.yaml` maps Boundary / Control / Entity / Database (and Spring/hexagonal aliases) to stable group names. Viewpoint YAML is unchanged.

### D5. Validation reports organisation errors

Phase 8 records `misplaced_groups` (element group vs graph layer) so a future run cannot silently pass a shuffled BCED diagram.

## Consequences

- Default `task2view run` is still: clean → agents 1–3 → scoper plug-in → extractor plug-in → **structure grounding → critic (optional) → grounding** → notation → gate.
- Homemade Phase 4–7 ReAct extractors stay unused.
- Ablations: `--skip-critic`; grouping quality no longer depends on the extractor guessing packages.
- We do not claim LocAgent, ArchAgent, or SemRef are vendored. Citations live here and in module docstrings.
