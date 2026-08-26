# ADR-002 — SOTA plug-ins for analysis; any notation for the view

- **Status:** accepted
- **Date:** 2026-08-20
- **Supersedes:** ADR-001 D5–D7 (homemade analysis-plan + ReAct extract + Phase 6 agent)
- **Decided in:** chat on using published scoping/extraction methods as plug-and-play stages, dropping a separate reconcile agent, and generating the last view in any registered notation

## Context

ADR-001 made `task2view run` an eight-agent loop. Phases 1–3 (interpret, questions, viewpoint) match the research plan and should stay agents.

Phases 4–6 as we implemented them did **not** match stronger published methods:

- PDF Phase 4 as an LLM that writes an “analysis plan” from a directory tree is weaker than a typed graph plus a published scoper.
- PDF Phase 5 as a ReAct claim loop is weaker than packing the scoped files with the graph (ArchAgent / CIAO shape).
- A separate Phase 6 agent only restated unanswered questions.

Reviewers already rejected LLM-only for **grounding**. The right split is: agents for stakeholder/task/viewpoint; **plug-in catalog** for repository analysis; **plug-in catalog** for extraction; **adapter catalog** for notation.

Whole-repo copies of LocAgent, Aider, ArchAgent, and CIAO are not drop-in (different languages, harnesses, APIs). We implement the **published mechanism** of each as a named plug-in, cited below, not a fork of their SWE-bench or OpenAI stack.

## Decision

### D1. Default pipeline after viewpoint planning is SOTA plug-ins, not homemade agents

```
0 clean
1 interpret agent
  correspondence (catalog; no LLM)  → correspondence.json
2 questions agent (grain of selected viewpoint)
3 viewpoint-planning agent (ranked catalog ids only)
4 Scoper plug-in          → repository_scope.json
5 Extractor plug-in       → view_model.json  (VIEWPOINT GRAIN)
7 NotationAdapter         → architecture_view.<ext>
8 semantic + syntax gate  → validation_report.json
```

Viewpoint selection and grain are [ADR-005](ADR-005-correspondence-and-published-grain.md). Plug-in catalogs for scoper / extractor / notation are unchanged.

There is **no Phase 6 agent**. The rule “do not present unsupported views as fact” stays in the extractor (`unanswered`) and in the Phase 8 gate (empty view fails; unanswered AQs → `pass_with_corrections`).

`--legacy` remains the regex Phase 1–2 path with the same Phase 4–8 plug-ins.

`--skip-extract` stops after the scoper.

Homemade modules `agents/phase4_plan.py`, `phase5_extract.py`, `phase6_reconcile.py`, `phase7_generate.py` were removed. They are not the production analysis stack.

### D2. Phase 4 is a Scoper catalog (`--scope-strategy`)

| Name | Mechanism (as published) | Source |
|---|---|---|
| `composite` (default) | Union of task seeds ∪ degree centrality ∪ layer coverage ∪ 1-hop, then token budget | pipeline spec v2; LocAgent-style hop + Aider-style centrality + thin-layer coverage |
| `graph1` | Task seeds + 1-hop on the typed uses graph | LocAgent / RepoGraph 1-hop localization |
| `locagent` | Task seeds + **2-hop** BFS (multi-hop graph walk without vendoring their LLM tool loop) | LocAgent (Chen et al., graph-guided multi-hop) |
| `central` | Top-k degree | Aider RepoMap ablation (degree, not PageRank) |
| `pagerank` | Weighted PageRank on uses/calls, personalized by task seeds | Aider `repomap.py` (`nx.pagerank`, α=0.85) |
| `layer` | Top-n types per package | recovers thin mandatory layers |
| `grep` | Full-text keyword hit in path or file body | SWE-bench / LocAgent grep baseline |
| `lexical` | Filename/path tokens only | cheap ablation |
| `dataflow` | Task seeds + 1-hop on the **call** graph | call-graph localization for sequence/dataflow |
| `full` | Entire cleaned corpus, budget-truncated | upper bound |

The Java graph is again the **inclusion policy** for graph-based scopers. Phase 8 still uses it as a semantic gate.

### D3. Phase 5 is an Extractor catalog (`--extract-backend`)

None of these clone a third-party repo wholesale. Each is the published *shape* on our contracts (`ViewSpecification` + `RepositoryScope` + graph → `ViewModel`).

| Name | Mechanism | Source |
|---|---|---|
| `gemini` (default) | Graph summary + packed scoped files → JSON view model | pipeline spec v2 Phase 4a |
| `archagent` | Same packing; prompt is honest that Task2View's javalang uses/calls **summary** is attached (not ArchAgent's analysis loop) | ArchAgent (static analysis + LLM diagram synthesis; paper + `panrusheng/ArchAgent-supplement` prompts, no runnable pipeline to copy) |
| `ciao` | Same packing; **verbatim** CIAO `prompt.json` is inlined, with an explicit override: ignore markdown/full-repo instructions; emit ViewModel JSON from the scoped files | CIAO-system/prompt.json |

All three share Gemini as the LLM (student key). CIAO’s original OpenAI flatten-the-whole-repo loop is **not** reproduced; the scoper is what limits files, which is the point of Phase 4. The ciao extractor still asks for Task2View `ViewModel` JSON rather than CIAO’s markdown document, because later stages consume that contract. The graph listing sent to Gemini prefers types from the scoped files and states that only Java has typed edges.

### D4. Phase 7 can emit any registered notation

`NotationAdapter` is keyed by `--diagram-language` (or the language Phase 3 chose). Registered ids match `knowledge/data/notations.yaml`: `plantuml`, `mermaid`, `d2`, `c4plantuml`, `structurizr`, `graphviz`, `nomnoml`, `excalidraw`, `bpmn`.

Adapters are deterministic. They emit **source** (Kroki render is optional later). Adding a language is: implement `emit`, register, add an extension in `DIAGRAM_EXT`.

### D5. How to add a plug-in

- Scoper: class with `name` + `scope(...)`, `@register_scoper`.
- Extractor: class with `name` + `extract(...)`, `@register_extractor`.
- Notation: class with `id` + `emit(...)`, `@register_adapter`.

`task2view plugins` lists what is loaded.

## Consequences

- Default `task2view run` is no longer eight LLM agents. It is three agents plus catalogs.
- Ablations are CLI flags, not forks: `--scope-strategy pagerank --extract-backend archagent --diagram-language mermaid`.
- We do **not** claim LocAgent or CIAO are fully vendored. Citations live in this ADR and in the scoper/extractor docstrings.
