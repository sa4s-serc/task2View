# ADR-008: Every view in UML 2.5.1, with the specification as knowledge

- **Status:** accepted and implemented (2026-10-21)
- **Builds on:** ADR-007 (architectural views: parts with their classes, arrows lifted from code)
- **Changes:** ADR-006 D3 (nine notations), ADR-007 D1/D3 (C4-PlantUML for structural views; the notation chosen per viewpoint and reader, added 2026-10-13)
- **Source:** OMG Unified Modeling Language 2.5.1 (formal/17-12-05), https://www.omg.org/spec/UML/2.5.1/PDF, suggested by a collaborator after the pilot review

## Problem
Reviews of the pilot keep finding diagrams that are not syntactically or semantically correct UML:
- shapes UML does not have: the `database` cylinder, C4 macros, ER `entity` boxes, `cloud`;
- too much text in boxes and too many arrows;
- a notation that changes from view to view (C4 for some structural views, UML for others, plain boxes for some readers), which makes views hard to compare and to check.

There was no reference for what a correct diagram of each kind is, so Phase 8 could check that a diagram compiles, not that it is correct UML.

## Decision
1. **One notation: UML 2.5.1, written in PlantUML.** The C4 renderer, the eight other notation renderers (Mermaid, D2, Structurizr, Graphviz, nomnoml, Excalidraw, BPMN, C4-PlantUML), the per-view notation choice, the reader "audience" derived from V&B Table 9.1 and the `--notations` option are removed.
2. **The specification is knowledge.** `knowledge/data/uml/uml-2.5.1.yaml` records, with the clause and page of the specification for each rule:
   - the fourteen diagram types of Annex A (Figure A.5, p. 685);
   - for each type, the symbols and paths it allows;
   - the frame heading kinds (Annex A, p. 684: `pkg`, `cmp`, `sd`, `dep`, `uc`, `act`, `stm`, `class`);
   - the Standard Profile stereotypes (Table 22.1, p. 679), the notation keywords (`«use»`, `«include»`, `«deploy»`, …) and a small Task2View profile (12.3) for what Views & Beyond needs and UML has no keyword for (`«layer»`, `«tier»`, `«database»`, `«external»`).

   The file summarises and cites the specification; the PDF itself is not stored (`code/scripts/fetch_uml_spec.py` downloads it). The skill copies the file, so the skill agent follows the same rules.
3. **Views are constrained to the UML diagram types.** Each viewpoint's model kind maps to one diagram type. Phase 3 selects only viewpoints drawable as one; viewpoints documented only as tables (interfaces, decisions, requirements, work assignment, implementation) are no longer selected.
4. **How the structural views are drawn** (`phase7/uml_arch.py`):
   - decomposition and layered: **package diagram** (12.2.4). Layers and parts are packages; a part's main classes are drawn inside it, the rest as a comment ("and 9 more"). Decomposition views draw no arrows; a database is not a module and is left out.
   - uses: **package diagram** with `«use»` dependencies between parts (7.7.4); the part being changed carries a comment.
   - client-server and other C&C styles: **component diagram** (11.6.4, 11.6.5). Parts are components; their main classes are listed in the optional "realizations" compartment; arrows are dependencies named by intent with the protocol as a property in braces, e.g. `delegates requests {HTTP/JSON}`.
   - a dependency against the layering carries the constraint `{against the layering}`.
   - every diagram has a frame whose heading names its kind (Annex A).

   The other views (`phase7/notations/plantuml.py`) follow the same rules: data stores are components in component views and `«executionEnvironment»` nodes in deployment views (19.4.4), the use-case subject is a rectangle (18.1.4), communication diagrams use lifeline objects with numbered messages (17.9.1), and a stereotype is shown only when UML allows it on that element.
5. **Phase 8 checks UML conformance** (`phase8/uml_check.py`), on any PlantUML source, so the agent conditions can be checked too (`code/scripts/check_uml.py`):
   - a shape that is not a UML symbol (cylinder, cloud, ER entity, C4 macro): **error**;
   - a UML symbol or path of another diagram type: **warning**. Annex A says the boundaries between diagram types "are not strictly enforced", so mixing is allowed but reported;
   - a stereotype outside the keywords, the Standard Profile and the Task2View profile: **warning**;
   - no frame, or a heading that does not name the diagram kind: **warning**.

## Consequences
- **Saved run redrawn** (`experiments/adr7-uml-2026-10-21/`, no model calls): all 23 views compile and pass the UML check. Before this change, 16 of the 23 had UML errors (15 were C4).
- **The same check on the agent conditions** of that run: 16 of 26 plain-agent diagrams and 7 of 18 skill-agent diagrams have UML errors, mostly the `database` cylinder and ER `entity` boxes.
- **Coverage lost:** a need covered only by a table viewpoint (e.g. ownership via work assignment) is now reported as not covered.
- **The check is syntactic.** It shows a view uses UML correctly, not that it is the right view: an empty use-case diagram is valid UML. Semantics stay with the faithfulness and coverage checks and with people.
- **PlantUML limits:** it has no communication diagram (approximated with object lifelines), and UML's ball-and-socket wiring is not used yet (component views use dependencies, as in UML's overview example, Fig. 11.39).

## Not done
- Interaction overview, timing, composite structure, object and profile diagrams are in the knowledge file but no viewpoint uses them.
- Size rules for text in boxes stay in `phase8/readability.py` (descriptions of at most 12 words); the specification sets no size limits.
