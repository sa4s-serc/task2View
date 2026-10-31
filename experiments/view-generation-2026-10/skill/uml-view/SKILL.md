---
name: uml-view
description: >-
  Produce one UML architecture view (component, deployment, use case, sequence, class) from a repository for a
  stakeholder's concern given as ISO/IEC/IEEE 42010:2022 inputs (stakeholder, perspective, concern, aspect,
  viewpoint, model kind). Use with the plantuml-diagrams skill, which handles PlantUML authoring, rendering and
  layout checks; this skill decides what goes in the view and keeps it UML.
---

# UML view for a stakeholder concern

Derived from published skills (collected 2026-10-30), not written from scratch. Every rule carries its source
tags; the tags are explained in `DERIVATION.md`. Where this skill and `plantuml-diagrams` disagree, this skill wins
(see "UML overrides").

## 1. Before drawing
1. **Write the takeaway**: one sentence that answers the concern for this stakeholder. If it needs "and", the
   concern needs two views; say so in the README and draw the one the model kind names. [GD, NIR, OAI]
2. **Set two dials from the inputs** [CL, DW]:
   - *Detail* from the perspective: whole system / high level → **overview**; one feature or area →
     **balanced**; a change the stakeholder is about to make → **detailed** for that area only.
   - *Wording* from the stakeholder: business/analyst roles get domain terms and no technology names;
     engineering roles get technology and protocol names. [DW, WS, A42]
3. **Element budget** (defaults from the sources; over budget → split or drop, never shrink) [CL, VHU, GD]:

   | model kind | overview | balanced | detailed |
   |---|---|---|---|
   | component / deployment nodes | ≤ 7 | ≤ 12 | ≤ 20 |
   | sequence | ≤ 5 lifelines, ≤ 8 messages | ≤ 7, ≤ 12 | ≤ 7, ≤ 25 |
   | use case | ≤ 8 use cases | ≤ 8 | split by actor group |
   | class | ≤ 7 classes | ≤ 10 | ≤ 15 per subject area |

   The budget is a prompt to cut, not a target to fill; a smaller view that answers the concern is better. [CC, CL]

## 2. Find the evidence
1. Explore in this order and stop when the concern is covered: entry points → interfaces/APIs and their
   callers → data stores, schemas, migrations → deployment and build files → tests → docs (docs give intent
   only; code wins when they disagree). [MP, MEL, NIL, YER]
2. Build an **inventory before drawing**: each candidate element and relation with `file:line` evidence and a
   one-line responsibility. Anything you cannot point to is `unknown`, not guessed. [MP, DW, MEL, MSC]
   Write it as `inventory.json` next to `view.puml`, in this shape (aliases are the ones used in the PlantUML):
   ```json
   {"model_kind": "UML component diagram", "detail_level": "overview | balanced | detailed",
    "elements":  [{"alias": "orders", "name": "Order service", "responsibility": "...", "evidence": ["src/a/B.java:12-40"]}],
    "relations": [{"from": "web", "to": "orders", "label": "places order", "evidence": ["src/web/C.java:88"]}],
    "concern_details": [{"detail": "...", "answered_by": ["orders"]}, {"detail": "...", "not_answered": "why, and which view would"}],
    "omitted": [{"name": "...", "reason": "..."}]}
   ```
   Evidence is a list of `path:line` or `path:start-end` relative to the repository root, or `"unknown"`.
3. Draw an edge only when code, config or docs show the interaction. If two classifications are plausible or the
   evidence is missing, mark the item "(unconfirmed)" and record it under Assumptions. [MSC, GD, CH]

## 3. Choose what to show (abstraction)
- **One abstraction level per view.** No classes inside a deployment view, no deployment nodes in a component
  view. [SW, CH, MP, RC, JR, GD, OAI]
- Components are units the code enforces (modules, services, layers with an interface), not folders. Merge a
  controller/service/repository chain into one component unless the concern is about that chain. [JR, RC, MP]
- **Omit** DTOs, utility/helper classes, framework glue and configuration; libraries and frameworks become a
  technology label, not a box. [RC, JR, EG, CG]
- Sequence lifelines are architectural roles, not every class; collapse repeated internal calls and say how many
  were collapsed. Main flow first; one `alt` for the error path the concern asks about. [MEL, VHA, CG, RT, TM]
- Deployment shows nodes, execution environments, artifacts and communication paths only when the code shows
  where things run (build files, configs, connection strings). [CL, BMA, MSA]
- Class views show key attributes and public operations the concern needs; hide private members. [CG, EG, GD]
- Use case views: actors are real roles from the code (permissions, user types), use cases are user goals, not
  screens or methods. [VHU, NIL]

## 4. Notation
- Relations point from the caller/dependent to the dependency and carry a short verb label (1–4 words), plus the
  protocol for engineering audiences; never a bare "uses". [RCH, SW, GD]
- One name per element, the same in the view, the README and the code. Declare every element up front with an
  alias, in reading order. [GD, NIR, A365]
- Title = model kind + scope. A legend only if colour or line style carries meaning. [GD, ART, RCH, NIR]

### UML overrides (rules from the sources that are rejected because they break UML 2.5.1)
- Stereotypes only from the UML 2.5.1 standard profile (e.g. «device», «executionEnvironment», «artifact»,
  «deploy», «manifest», «include», «extend», «create», «use», «call», «interface», «enumeration») or a profile
  you declare in a note. No invented stereotypes such as «factory», «tables», «REST», «docker». (Rejects UMCP, SW,
  REL #52.)
- Do not use a bare `hide stereotype`: it also hides UML keywords. The vendored templates hide only the
  `<<accent>>`, `<<alert>>` and `<<muted>>` styling stereotypes; use those for emphasis, with a legend. (Amends
  GD house style #53.)
- Deployment elements are `node`, `node <<device>>`, `node <<executionEnvironment>>`, `artifact`; no `cloud`,
  `queue`, `rectangle` or `database` as UML elements (rejects A365, JAB, REL #54). `artifact ..> node : <<deploy>>`.
- Keep the «component» notation: no `skinparam componentStyle rectangle` (rejects REL, NII #55).
- A dashed arrow is a dependency or a reply, never "async"; async messages are `->>`. (Rejects GD #56.)
- No crow's-foot in a class diagram; that is ER notation (#59).

## 5. Render, check, revise
1. Render and check with the `plantuml-diagrams` skill's `scripts/puml-check` (renders the SVG and measures
   overlaps, edges through text, lifeline crossings, tiny text). Fix one issue kind per run; stop when two runs in
   a row do not reduce the issue count. [GD]
2. Do not grade your own view. A separate reviewer with a fresh context will judge whether it answers the concern
   at the right level, and you may get its critique back for one revision. (Self-review with shared context
   inflates scores without improving them for people: Pan et al. 2024; a separate evaluator is easier to tune:
   Anthropic harness design. This replaces the image self-review of GD and A365.)
   When fixing, change the graph (direction, grouping, splitting, dropping), never add elements that are not in
   the inventory. [GD, DIO, YH]
3. Run `python3 -I .claude/skills/uml-view/scripts/check_inventory.py view-out/<case>/inventory.json` and fix
   what it reports: evidence that does not exist, elements or relations drawn but not in the inventory (or the
   reverse), concern details with no answer, and elements over the budget. Exit 0 means clean.
4. Keep the best version, not the last: if a revision has more issues or loses a concern detail, revert it.
   [GD, DIO, YH]
5. No renderer, no claim: if it did not render or you could not view it, say so. [GD, A365]

## Tooling notes
Written up from what the agent had to rediscover in earlier runs (they hold for any repository):
- Run the scripts as `python3 -I .claude/skills/plantuml-diagrams/scripts/puml-check FILE.puml` (and `puml-new`).
- Start the file with a bare `@startuml`; a name after it changes the output file name and `puml-check` then
  finds no SVG.
- Inside a `note`, `\n` is printed literally; use real line breaks.
- Class diagrams: declare `class "Display name" as alias`; to lay out rows, keep top-to-bottom and add
  `-[hidden]->` links rather than switching direction.
- A `label-on-border` warning usually goes away with a longer edge (`----->`), which moves the label off the
  container border.
- On macOS, `sed -i` needs an empty suffix argument (`sed -i '' ...`).

## 6. README (next to view.puml)
- The takeaway sentence, the stakeholder, and the detail level chosen and why.
- For each concern detail: where the view answers it, or why it does not (and which other view would).
- A pointer to `inventory.json` (do not repeat it) and the final `check_inventory.py` result.
- Omitted on purpose (what was left out to stay within budget or level).
- Assumptions and "(unconfirmed)" items. [CH, DW, MP]
- Check result: final puml-check and check_inventory.py results; after a revision, what changed and why.
