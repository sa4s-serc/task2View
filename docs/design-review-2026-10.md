# Task2View design review — root causes and redesign

*October 2026. Inputs: research plan (`research_plantask2view.pdf`), pipeline spec (`Stakeholder_Task_Guided_…docx`), ADR-001…005, `architecture.md`, the pilot (`experiments/pilot-2026-09/`: Task2View outputs, agent baselines, expert review). Every claim below was checked against code or pilot artifacts; file:line refers to the working tree on 2026-10-08.*

## 1. Verdict in one paragraph

The pilot failures are not seven independent bugs. They come from six root causes, and five of them are design-level: the contracts between phases cannot carry what the expert asked for, so no amount of prompt tuning fixes them. The deepest one is that the design changed philosophy three times in six days (ADR-001 agents-with-tools → ADR-002 static scopers + packed prompt → ADR-003/4/5 graph grounding and catalog kernel), and the current code stacks all three without one owning the evidence. The result is a pipeline whose Phase 4–8 look like the research plan in file names but behave like "lexical file pick → one-shot extraction → string filter".

## 2. Root causes

### RC0 — Design drift: no single evidence philosophy
- Research plan §1.5: agents interpret the repository with basic tools; static analysis is *not* the primary mechanism.
- ADR-002 rejected that for Phases 4–6 ("weaker than a typed graph plus a published scoper"). ADR-001 D6 had said the opposite (graph is a tool, not an inclusion filter).
- Current code: static scoper → LLM plan that may only *narrow* the scoper's list → per-task packed prompts. `RepoTools` is never instantiated; `AgentRuntime.tool_loop` has no caller.
- **Effect:** the "SOTA" components are present but either inert (PageRank, see RC2) or used outside their published purpose (CIAO is whole-repo documentation, not question-driven localization).

### RC1 — There is no architecture model in the knowledge base
The plan asks for a chain *stakeholder → task → concern → question → view type → required evidence → granularity*. The KB is a set of lookups joined only by `viewpoints.yaml: frames_concerns`.
- **Catalog = CIAO document sections, not modelling viewpoints.** Reachable view types: context, component ×3, deployment, class (`viewpoints.yaml`). No sequence/behaviour, no layered structure, no information model (entities + attributes), no use-case. `notations.yaml` defines `sequence_view`, but no viewpoint uses it.
- **6 of 14 concerns are framed by no viewpoint** — including `control-flow`, raised in all six IS goals. It is structurally unanswerable and always lands in `unanswered_concerns`. This, more than the one-view cap, is why "add a sequence diagram" can never happen.
- **Role is ignored by design.** `select_correspondence` ranks by V&B Table 9.1, then overwrites the winner with the Phase 3 pick (`correspondence.py:251-253`). Phase 3 is told "Do not choose the viewpoint this role usually receives" (`knowledge_context.py:139`). `aliases.yaml` maps "database engineer" → `analyst` (the security analyst row).
- `viewpoints_for_concerns` drops `general` when other concerns exist (`correspondence.py:146`), which removed `context` for GR10-Q4 and left `decision-record` → an ADR view for a business analyst.

### RC2 — Evidence acquisition is lexical, not investigative
- **Phase 0 throws away the evidence some viewpoints need.** It keeps source code only: `xml/yaml/properties/json/html` and extension-less files are dropped (`corpus.yaml:80-130`, `clean.py:52`). GR10-Q2 lost `pom.xml` and `persistence.xml` (`cleaned_corpus.json`: `non_code_extension`) and drew Java classes as deployment nodes.
- **Graph = co-mention graph.** Edges are identifier mentions anywhere in text, including strings and comments, case-insensitive (`graph.py:261-267`); `has_edge` ignores direction. In IS, 18% of edges come only from strings or comments.
- **Seeds = path substrings + IDF + alphabetical cut at 8.** Package segments pollute document frequency ("reservations" is in 80 of 81 paths, so `ReservationManager` never reaches seat-L3). `_ri_ids_for` makes every file serve every RI, so the tie-break is the path string. GR10-Q3 (database goal): "boundaries" from a Phase 2 question matches `Boundary/` and sorts first → 8 GUI files, `Database/*` cut. IS-reg-L3: "manage" matches Notification/Reservation/StudyRoom managers before `UserManager` (9th, cut).
- **PageRank is a no-op.** `plan.py:27,42` excludes `pagerank_seed` files from what the plan agent may name, then `scope_for_plan` shrinks to the plan. Every pilot scope is 100% `ri_forced` (2–8 files). Runs labelled "pagerank" are not PageRank runs; scoper ablations are invalid.
- The body-search fallback is dead code (`seeds.py:88` vs `:174`).
- **Phase 5 has a closed boundary.** Claims citing a file outside the task list are dropped (`evidence.py:106-116`). The plan's "follow references; candidate locations are starting points" is impossible.

### RC3 — No abstraction / consolidation step (claims → boxes 1:1)
- `_view_from_claims` turns every distinct name string in a claim into a box (`evidence.py:224-285`). Nothing groups classes into components, assigns layers, or canonicalises names across tasks. ADR-001 D5's "name-normalized union" is not implemented.
- Kind is copied from the grain unit, not from the element (`evidence.py:229`), so the Phase 8 grain check is tautological.
- Effects: `SeatDTO` as a component; `User Login Boundary Component`, `UserLoginGUI` and `User Boundary Module` as three boxes for one class (GR10-Q1); `InternalNoteGUI` vs `Boundary.InternalNoteGUI` as different elements (GR10-Q3).
- Claim schema: no `confidence`; 2 support classes instead of 4; 111/111 pilot claims are `directly_observed`. Excerpts are never checked against files.

### RC4 — The view contract cannot express the views the expert asked for
`ViewModel` (`contracts/models.py:142-182`):
- Groups are flat, and no producer fills them (Phase 7 hard-sets `"groups": []`, `generate.py:251`). All 10 pilot views have no groups. → **Layers** theme.
- One `role` string, no `responsibilities[]`. → **Placement** theme (responsibilities on edges).
- No attributes/operations, no stereotype field; `entity`/`class` alias to `module`. → **Notation** theme; a data model with attributes is impossible.
- `order` exists on relations but is never set. One view per model, `max_views=1`, Phase 3 prompt says "Exactly one view" (`viewpoint.py:63`). → **Second view** theme.
- Renderer: every element `[X]`, every relation `-->`, `contains` drawn as an arrow, no `node/artifact/database/actor/usecase` shapes in practice (`render.py:90-93`). → **Layout/Notation**.

### RC5 — No closed loop: Phase 6 annotates, Phase 8 rubber-stamps
- Phase 6 is forbidden to change anything ("Do not add boxes. Do not change the viewpoint", `reconcile.py:24`); its schema has no decision fields. IS-seat-L3 reconciliation itself notes that the grain blocks sequencing — and nothing acts on it. `critic.py` is dead code.
- Phase 8 verdict: 10/10 pilots `pass_with_corrections`, because any unanswered concern triggers it (`validate.py:324`); `fail` needs broken syntax or zero elements. `forbid` lines are prose, never checked. "Covered" = any claim names any element in the view. Render failures (GR10-Q4 mmdc) are not seen.
- **Phase 8 creates the duplicates.** For non-component kinds it renames an element to the type of its `evidence.symbol` (`validate.py:186-189`). `SystemServicesController` and `Boundary.InternalNoteGUI` both become `InternalNoteGUI`; the edges become self-loops and are deleted → GR10-Q3 ends with 0 relations.

### Theme → root cause
| Expert theme | Root cause(s) |
|---|---|
| Second view | RC1 (no behavioural viewpoint), RC4 (single-view contract), RC5 (Phase 6 cannot split) |
| Grain | RC3 (no abstraction), RC2 (2–8 lexical files), RC1 (no detail level from Phase 1) |
| Layers | RC4 (groups never produced), RC1 (no layered viewpoint) |
| Names | RC3 (no canonical registry), RC5 (no name-fidelity check) |
| Notation | RC4 (no stereotypes/kinds/shapes) |
| Placement | RC4 (no responsibilities/attributes fields) |
| Layout | RC4 (no nesting/ordering hints) |

## 3. Prior hypotheses (from the claude.ai analysis), re-checked
| Hypothesis | Status |
|---|---|
| IDF filter drops central domain nouns | Mechanism confirmed, example wrong: "registration" survived; "reservations", "entities", "report(s)", "control" were dropped. The real culprit is package-path pollution plus the alphabetical cap. |
| No deduplication | Confirmed, and worse: Phase 5 emits name variants and Phase 8 *creates* duplicates. |
| No role→viewpoint guard | Confirmed. It is deliberate (prompt + overwrite), plus a wrong alias for DBA. |
| Forbidden names pass validation | Confirmed. `forbid` is prose only. |
| Fixed budget regardless of query | Confirmed, but what binds is `max_files=8`, not the 120k token budget. |
| No layer grouping | Confirmed (RC4). |
| No multi-view detection | Confirmed (RC1 + RC4). |

## 4. Redesign (proposal)

**Principle.** Go back to the research plan's split, and use the SOTA mechanisms as *tools inside agents*, not as replacements for phases (this restores ADR-001 D6/D7 and supersedes ADR-002 D1–D3). Put one explicit **Architecture Evidence Model (AEM)** in the middle, and make every view a *projection* of it.

| Phase | New contract (root cause addressed) |
|---|---|
| 0 Reconnaissance (deterministic) | Typed evidence corpus: code / build / deploy / config / schema / web / test / docs. Directed dependency graph from imports and type references only (no strings/comments, tests flagged). **Repository card**: package tree, languages, manifests, entry points (main, controllers, routes), datastores, a cluster summary. (RC2) |
| 1 Interpretation | Add `detail_level` and `subjects[]` (the enumerated sub-responsibilities of L3 goals). Fix aliases. (RC1) |
| 2 Questions | Typed questions `{target, asks: elements \| interactions \| order \| attributes \| actors \| deployment \| rationale, subjects[]}`. One per enumerated subject; no generic quality questions. (RC1) |
| 3 Viewpoint planning | Expanded catalog: context/use-case, layered module structure, component & connector, **behaviour (sequence)**, **information model**, deployment. `asks → viewpoint` lives in the KB. Choose the *minimal set of views covering all questions* (cap 2–3). Role prior from Table 9.1 as a tie-breaker. (RC1, RC4) |
| 4 Investigation plan | Agent gets the repository card and tools; emits tasks per view with seed directories and symbols, expected evidence, and constraints. Budget scales with the number of questions and subjects. (RC2) |
| 5 Evidence | Bounded tool loop (list / search / read / graph neighbours), open boundary. Claim schema with 4 support classes and confidence; excerpt and symbol mechanically verified in the file. (RC0, RC2) |
| 5b Consolidation → AEM | Canonical element registry (one id per symbol, aliases merged); explicit class→component abstraction with member sets; layer assignment from packages and `architectural_styles`; responsibilities and attributes attached to elements. **This is the "architecture model".** (RC3) |
| 6 Reconciliation | Typed decision per planned view: `confirm \| simplify(grain) \| split \| drop \| request_evidence(task)`; `request_evidence` loops to 4/5, at most N times. (RC5) |
| 7 Generation | Deterministic projection AEM → ViewModel v2 (nested groups, stereotypes, responsibilities[], attributes[], ordered messages, view id), LLM only for labels and layout hints. Adapters draw real UML shapes. (RC4) |
| 8 Validation | Structured `forbid` predicates, name fidelity, post-canonical dedup, no mixed levels, connectivity, render success, cross-view name consistency, and an LLM task-fit judge against the profile and questions (= Track 2). Failure → bounded regenerate. (RC5) |

**What stays:** Phases 1–3 as agents; the notation adapter registry; scopers as *ablation baselines and as tools* (after fixing the cap/tie-break/PageRank bugs so the labels are honest); the JSON phase artifacts.

## 5. Experiment provenance issues to fix in the write-ups
1. The expert reviewed the **Italian-code agent runs** (`experiments/pilot-2026-09/outputs/*/italian-reviewed`): the comments quote `Segnalazione`, `id_cittadino`, `BoundaryAutenticazione POST /api/auth/registrazione`, which exist only there. `outputs/*/english-rerun` are English re-runs made about 10 minutes later, with different content. The spec §11–12 and `main.tex` ("all conditions on the English variants") are wrong for the reviewed set.
2. `manifest.json` points the agent runs at the Italian subjects (upstream commits: Progetto-IS `070e4fc`, GR10 `63b0160`).
3. Task2View pilot = `outputs/task2view` (Sep 24) on the English variants. The scope is lexical forced seeds, not PageRank (§RC2). The code has changed since.
4. Three skill comments name the other feature (already noted in `main.tex`). Check whether the reviewer's IS-reg/IS-seat labels were swapped.
