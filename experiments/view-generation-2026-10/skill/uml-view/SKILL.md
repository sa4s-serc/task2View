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
   - *Detail* is given in the stakeholder perspective as `detail level: overview | balanced | detailed`. Use
     that level; do not choose another one. Overview: the main parts and how they connect; balanced: the parts
     involved in the concern with their interfaces; detailed: the parts of one area the stakeholder will change,
     with their interfaces and rules. If it seems wrong for the concern, still draw at the given level and
     say in the README what a different level would add. Only if no level is given, take it from the
     perspective: whole system / high level → **overview**; one feature or area → **balanced**; a change the
     stakeholder is about to make → **detailed** for that area only.
   - *Wording* from the stakeholder: business/analyst roles get domain terms and no technology names;
     engineering roles get technology and protocol names. [DW, WS, A42]
## Examples
`examples/` holds worked examples from spring-petclinic, a repository unrelated to yours: a request, the view, its
inventory and why it was drawn that way. Before drawing, read the example for your model kind (and both component
examples, which show one system at overview and at detailed level). Copy the level of abstraction and the
notation, not the content. See `examples/README.md`.

## 2. Find the evidence
0. **If `.claude/repo-graph.json` exists, start from it.** It is a static dependency graph built from the code
   before the session: symbols, dependencies between them with `file:line`, entry points, persisted entities,
   deployment and build files. Query it with `python3 -I .claude/skills/uml-view/scripts/graph_query.py`:
   - `summary` for the layers, packages and entry points;
   - `search <terms>` with the words of the concern and its details and the stakeholder's entry points (routes,
     screens, main classes), to find where the concern lives;
   - `around <symbol> [--depth 2]` to follow that code's dependencies.
   Draw only that neighbourhood, not the whole graph. The graph is class level: group it into elements as §3
   says, do not copy it. It has no run-time framework wiring, databases, external systems or users; read the
   code and config for those.
1. Explore in this order and stop when the concern is covered: entry points → interfaces/APIs and their
   callers → data stores, schemas, migrations → deployment and build files → tests → docs (docs give intent
   only; code wins when they disagree). [MP, MEL, NIL, YER]
2. Build an **inventory before drawing**: each candidate element and relation with `file:line` evidence and a
   one-line responsibility. Anything you cannot point to is `unknown`, not guessed. [MP, DW, MEL, MSC]
   Write it as `inventory.json` next to `view.puml`, in this shape (aliases are the ones used in the PlantUML):
   ```json
   {"model_kind": "UML component diagram", "detail_level": "overview | balanced | detailed",
    "elements":  [{"alias": "orders", "name": "Order service", "responsibility": "...", "evidence": ["src/a/B.java:12-40"],
                   "members": ["com.shop.orders.*"]}],
    "relations": [{"from": "web", "to": "orders", "label": "places order", "evidence": ["src/web/C.java:88"]}],
    "concern_details": [{"detail": "...", "answered_by": ["orders"]}, {"detail": "...", "not_answered": "why, and which view would"}],
    "omitted": [{"name": "...", "reason": "..."}]}
   ```
   Evidence is a list of `path:line` or `path:start-end` relative to the repository root, or `"unknown"`.
   `members` says which code an element stands for, so the grouping is a recorded decision: symbol ids
   (`pkg.Class`), packages (`pkg.*`) or paths (`src/a/`); `graph_query.py members <spec>` shows what a spec
   covers. Give members to every element that stands for code; leave them out for users, databases, external
   systems, nodes and use cases.
3. Draw an edge only when code, config or docs show the interaction. If two classifications are plausible or the
   evidence is missing, mark the item "(unconfirmed)" and record it under Assumptions. [MSC, GD, CH]

## 3. Choose what to show (abstraction)
- **One viewpoint per view.** Draw only the elements of the given viewpoint; do not add context elements from
  another viewpoint (no GUI, controllers or services in a data model, no classes in a use case view). If a concern
  detail needs another viewpoint, say in the README which view would answer it. (Reviewer finding 2026-11:
  context elements read as excess detail; 42010 cl. 5: a view is governed by one viewpoint.)
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
  screens or methods. Put the use cases inside a system boundary named after the system
  (`rectangle "<system>" { ... }`), actors outside it (UML 2.5.1 cl. 18, the subject). [VHU, NIL]

## 4. Notation
- Relations point from the caller/dependent to the dependency and carry a short verb label (1–4 words), plus the
  protocol for engineering audiences; never a bare "uses". [RCH, SW, GD]
- One name per element, the same in the view, the README and the code. Declare every element up front with an
  alias, in reading order. [GD, NIR, A365]
- **Plain words, no codes.** Every label reads on its own: no invented codes or numbering (IP1, UC3, C2) that need
  a legend to decode. To mark what the concern asks about (e.g. integration points), say it in words in the label
  or a note. (Reviewer finding 2026-11: "IP5" was not understood.)
- Title = model kind + scope. A legend only if colour or line style carries meaning. [GD, ART, RCH, NIR]

### Component views: build them from a model (only when the prompt asks for model.json)
When the prompt asks for it, do not write the PlantUML of a UML component diagram by hand. Write `view-out/<case>/model.json` (shape in the
docstring of `scripts/component_model.py`) and run
`python3 -I .claude/skills/uml-view/scripts/component_model.py build view-out/<case>/model.json --graph .claude/repo-graph.json`.
It checks the model and draws the PlantUML and inventory.json. UML 2.5.1 (Clause 11) in short:
- A component is a replaceable unit of the system that hides its contents behind interfaces: a package or group
  of classes with one responsibility, not a single class (a single class is a module-view element; the checker
  notes it).
- Components meet through interfaces: a provided interface (lollipop) is what a component offers, a required
  interface (`«use»` dependency) what it needs from another. Name interfaces after what they offer (an API, a
  repository, a form), not after one method.
- Use a plain dependency only when no interface exists, with a 1–4 word label, never a method call.
- Nest components with `parent` to show a subsystem and its parts; mark databases and outside systems
  `"external": true`.
Fix every error it reports; then render view.png from view.puml with plantuml.

### UML overrides (rules from the sources that are rejected because they break UML 2.5.1)
- Stereotypes only from the UML 2.5.1 standard profile (e.g. «device», «executionEnvironment», «artifact»,
  «deploy», «manifest», «include», «extend», «create», «use», «call», «interface», «enumeration») or a profile
  you declare in a note. No invented stereotypes such as «factory», «tables», «REST», «docker». (Rejects UMCP, SW,
  REL #52.)
- Do not use a bare `hide stereotype`: it also hides UML keywords. The vendored templates hide only the
  `<<accent>>`, `<<alert>>` and `<<muted>>` styling stereotypes; use those for emphasis, with a legend, and keep
  the `hide <<name>> stereotype` line for each one you use so it is not printed. (Amends
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
3. Run `python3 -I .claude/skills/uml-view/scripts/check_inventory.py view-out/<case>/inventory.json --level <given
   detail level>` (add `--graph .claude/repo-graph.json` when the graph exists) and fix what it reports: evidence
   that does not exist, elements or relations drawn but not in the inventory (or the reverse), concern details
   with no answer, a detail level different from the given one, members that match nothing, and drawn relations with no code
   dependency behind them. For each "undrawn" dependency, draw it if the concern needs it, otherwise list it under
   `omitted` with the reason. Exit 0 means clean.
4. Run `python3 -I .claude/skills/uml-view/scripts/check_view.py view-out/<case>/view.puml` (use-case system
   boundary, no codes in labels, styling stereotypes hidden) and fix what it reports. Exit 0 means clean.
5. Keep the best version, not the last: if a revision has more issues or loses a concern detail, revert it.
   [GD, DIO, YH]
6. No renderer, no claim: if it did not render or you could not view it, say so. [GD, A365]

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
- Omitted on purpose (what was left out to stay at the given level, including undrawn dependencies).
- Assumptions and "(unconfirmed)" items. [CH, DW, MP]
- Check result: final puml-check and check_inventory.py results; after a revision, what changed and why.
