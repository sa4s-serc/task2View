# ADR-001 — Realign the running system with the research-plan multi-agent process

- **Status:** accepted (D5–D7 superseded by [ADR-002](ADR-002-sota-plugins.md))
- **Date:** 2026-08-20
- **Decided in:** chat on implementing Phases 1–5 as agents, logging architecture changes separately
- **Sources:** `docs/research_plantask2view.pdf` §1.5 and Phases 1–8; `docs/pipeline_spec_v2.md` §9 (map-reduce); this conversation

## Context

The first Python implementation followed **pipeline spec v2** (“contracts over agents”, “deterministic where possible”):

- Phase 1 = regex + YAML aliases
- Phase 2 = Table 9.1 numeric scoring + cue phrases (no derived architectural questions)
- Phase 3 = javalang graph + heuristic file union (task tokens, degree, layer, 1-hop) + token-budget exclusion
- Phase 4a = one Gemini call over packed files

That is **not** the system in `research_plantask2view.pdf`. The plan is a knowledge- and evidence-grounded **multi-agent** approach. Input 1 is free-text. Core interpretation and repository reading are agent responsibilities. Parsers and call graphs are not the primary extraction mechanism.

The two documents disagree on LLM-only vs parsers. Feasibility notes record that reviewers rejected LLM-only for **grounding**. This ADR does not pick “LLM-only” or “parser-only”. It picks **agents with tools**, and a **Java graph as a queryable tool**, not as a closed inclusion filter.

## Decision

### D1. Default run path is agentic (research-plan phases)

`task2view run` executes the eight plan phases. The previous regex/graph-scoper pipeline remains as `--legacy` so old tests and ablations still work.

Numbering in **code** (to keep existing artifact names) vs **PDF**:

| PDF phase | Agent | Code module | Artifact |
|---|---|---|---|
| 1 Interpretation | Stakeholder-Task Interpretation | `agents/phase1_interpret.py` | `stakeholder_task_profile.json` |
| 2 Questions | Concern and Question | `agents/phase2_questions.py` | `architectural_questions.json` |
| 3 Viewpoint plan | Knowledge-Grounded Viewpoint Planning | `agents/phase3_viewpoint.py` | `viewpoint_plan.json` (+ `view_specification.json` for the primary view) |
| 4 Analysis plan | Repository Analysis | `agents/phase4_plan.py` | `repository_analysis_plan.json` |
| 5 Evidence | Evidence Extraction (one agent per analysis task) | `agents/phase5_extract.py` | claims merged into `architecture_evidence_model.json` |
| 6 Reconcile | Need–Evidence Reconciliation | `agents/phase6_reconcile.py` | `evidence_aware_plan.json` |
| 7 Generate | Specialized view generation | `agents/phase7_generate.py` | `view_model.json` |
| 8 Validate | Validation | existing `phase4/validate.py` + syntax | `validation_report.json`, `architecture_view.puml` |

Phase 0 (deterministic clean) stays in front of the agents. It is not in the PDF’s eight phases; it remains because student repos mix UML, PDFs, and binaries with code.

### D2. Phase 1 is an LLM agent, not a regex

Free-text is valid (`I am a software developer. I need…`). The agent emits a Stakeholder-Task Profile (stakeholder, task, target, goal, scope, constraints). Canonical V&B role is resolved **after** the agent, using `aliases.yaml` as a check, not as the parser.

### D3. Phase 2 must emit architectural questions

Questions are the bridge between the task and viewpoint selection. YAML `required_information` templates **seed** the agent; they do not replace it.

### D4. Phase 3 (PDF) uses the knowledge base through an agent

The agent may select **more than one** view. `preferences.max_views` still caps how many we generate in this implementation (default 1) so free-tier cost stays bounded. The plan can list additional views as deferred.

### D5. PDF Phase 4 and Phase 5 stay sequential as stages; work inside them is parallel

We do **not** start “scoping” and “extraction” as two independent jobs and glue JSON.

- **Barrier:** analysis plan (PDF 4) must exist before evidence extraction (PDF 5).
- **Parallel reduce:** analysis **tasks** AT1, AT2, … run as separate extraction agents, then claims are **unioned** into one Architecture Evidence Model (name-normalized).
- Default worker count is small (2) because of Gemini free-tier rate limits. `--extract-workers 1` forces sequential.

This is the “repository analysis parallelisation, then combine” decision from chat.

### D6. The Java graph is a tool, not the inclusion/exclusion policy

javalang still builds a typed graph (uses/calls/inheritance). Agents may call `graph_query`. Files are **not** dropped because they lost a keyword/degree contest.

Token budget remains a hard cap on how much **text** is stuffed into one extraction prompt, not on which types exist in the architecture.

Phase 8 still uses the graph as a **semantic gate** (drop names that are not types and have no evidence file). That is grounding, not scoping.

### D7. Agents investigate with repository tools

Tools, sandboxed to the repo root:

- `list_tree` — directory reconnaissance
- `search` — symbol / keyword search
- `read` — open a file (truncated)
- `graph_query` — neighbors/degree/layer of a type

Candidate locations in the analysis plan are **starting points**. The extraction agent may open further files it discovers.

Readable text includes source **and** config/API-like files (HTML, XML, YAML, JSON, properties, SQL). Binaries, Visual Paradigm (`.vpp`), PDFs, and images stay blocked so diagrams are not grounded in a screenshot.

### D8. Gemini free-tier remains the model

`GEMINI_API_KEY`, default `gemini-2.5-flash`, `--samples 1`. No CIAO/ArchView backend in this change.

### D9. Decision log lives here, not in the spec

Future architecture choices go in `docs/architecture-decisions/` as new ADRs. Do not silently rewrite ADR-001; supersede it.

## Consequences

- Natural-language Input 1 no longer depends on a brittle `As a …, I need` regex for the default path.
- View type is justified by derived questions + knowledge base, not only the word “modify”.
- Extraction cost and latency rise (several model calls). Free-tier runs should use `--extract-workers 1` if they hit 429.
- `--legacy` remains for the measured heuristic scoper (composite/lexical/full) until an ablation says otherwise.
- Spec v2 JSON contracts are kept where they still fit (`view_specification.json`, `view_model.json`, `validation_report.json`) and extended with plan/evidence artifacts.

## Out of scope for this change

- Kroki rasterization inside `task2view run`
- CIAO / ArchView as 4a backends
- Embed / cluster+llm / full SWE-agent tool catalogs
- Changing Views & Beyond YAML content (except what Phase 1 already added for `software developer`)
