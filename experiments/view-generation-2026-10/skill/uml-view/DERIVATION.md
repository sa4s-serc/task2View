# Where the uml-view skill comes from

Collected 2026-10-30 from about 130 published skills, in three groups. The full notes and the raw files are in
`research_notes/UML skills collected/`: `plantuml_uml.md`, `architecture.md`, `review_quality.md` and `raw/`.

## Base used as is
- **plantuml-diagrams** by gregodouglas (MIT, commit 77af596, 2026-10-15),
  https://github.com/gregodouglas/plantuml-diagrams-skill
- What it provides:
  - PlantUML authoring rules
  - templates
  - layout levers
  - `puml-check`, a script that renders the diagram, measures the SVG and runs the stop rule
- It is the only published skill that measures layout instead of guessing.
- Its checks of SVG geometry need PlantUML 1.2026.4 or later. The local version is 1.2025.7, so only its text checks would run until PlantUML is upgraded.

## Source tags

| Tag | Skill | Used for |
|---|---|---|
| GD | gregodouglas/plantuml-diagrams-skill | takeaway first, element caps, labels, check loop, no claim without a render |
| A365 | Agents365-ai/365-skills (plantuml) | vision checklist, at most 2 rounds |
| NIR | nirumand/skills diagram-create / review | one purpose per diagram; review against the INNOQ 12 rules |
| OAI | openai/plugins uml-and-software-architecture-visualization | choose the type from the question; one level of abstraction |
| NIL | nilernous/diagram-skills sequence-diagram | code is ground truth; real role names |
| YER | yer9ali/sequence-diagram-skill | sequence from code |
| ART | artem-from-ua plantuml-diagram-guide | title rules |
| RCH | rchaganti/skills c4-diagram | edge labels with intent and protocol; rules for finding components |
| VHU / VHA | VictorHueni arch-uml / arch-arc42 | UML caps (classes, messages, use cases); runtime lifelines |
| CL | cathrynlavery diagram-design | two dials, audience and detail (7 / 12 / 24 nodes); budgets per type |
| CC | ccheney mermaid-diagrams | split when readability suffers, not at a fixed count |
| DW | microsoft/skills deep-wiki | wording and level per audience; `file:line` for every claim |
| MSC / MSA | microsoft/hve-core c4-architecture / architecture-diagrams | edge only with evidence; stop and record when unclear |
| MP | mercatorproj c4-structurizr | order of evidence search; inventory before drawing |
| MEL | melodic-software architecture plugin | `unknown` instead of guessing; collapse hops into roles |
| CH | cheriftj c4-model-skill | Assumptions section; one level per view |
| SW / JR / RC / RT | softaworks, jrjsmrtn, rchaganti, robtaylor C4 skills | audience-to-level table; abstraction and omission rules |
| WS / A42 | wshobson c4-architecture; MSiccDev arc42 | wording for non-technical readers |
| EG / CG | egamma architecture-overview; athola cartograph | omit DTOs and helpers; class member rules |
| BMA | bm629 architecture authoring | deployment view only when placement is real |
| TM | awesome-copilot threat-model conventions | main flow first |
| DIO | jgraph drawio skill | change the graph, not the pixels; score candidates and keep the best |
| YH | YutaroHara1129/mermaid-design | two-way fact check; review records which images were viewed |

## What no source had, and what we added
- **The link to 42010 inputs.** No skill reads a stakeholder, perspective or concern in the 42010 sense. The mapping from perspective to detail and from stakeholder to wording in §1 joins CL's two dials with DW's audiences.
- **UML 2.5.1 conformance.** None of the 32 PlantUML skills checks it, and several break it. The overrides in §4 reject those rules (numbered as in `plantuml_uml.md` §2) and limit stereotypes to the standard profile.
- **Relations checked against a static graph (condition F).** Most sources ask for evidence per edge (MSC, DW, MP),
  but none check it. With a dependency graph built from the code before the session, `check_inventory.py
  --graph` checks each drawn relation between code elements, and lists dependencies between drawn elements that
  are not drawn. Static dependency context improved LLM architecture output in ArchAgent (arXiv 2601.13007), and
  Briechle et al. (arXiv 2605.20055) validate LLM-written models against deterministic extraction. The agent
  still does the grouping, recorded as `members`, because the graph is class level and copying it gives the
  code-level views that failed in Miryala et al. (ICSA 2026).
- **README tied to each concern detail.** The sources write general docs. Ours states, for each concern detail, where the view answers it.

## Conflicts between sources and how they were settled
- **Orthogonal vs polyline lines:** polyline when edges have labels (GD measured this; UMCP did not).
- **Element cap of 12 vs 30:** budget by detail level (CL), with CC's warning that the budget is a reason to cut, not a target.
- **Unlabelled edge vs mandatory label:** a short verb label is required, but never a bare "uses".
- **Activation bars always vs when needed:** when needed (GD), since UML does not require them.
