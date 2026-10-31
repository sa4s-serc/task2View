---
name: plantuml-diagrams
description: >-
  Designs, writes, renders and self-checks PlantUML (.puml) diagrams (sequence, activity/swimlane, component,
  deployment, cloud/AWS, network, class, state, ER, use case, C4) so they render without errors, have no overlapping or struck-through
  labels, sane density, and a shape that fits a 16:9 slide or a letter page. Use whenever the user asks to draw,
  diagram, visualize, sketch or document an architecture, flow, lifecycle, API interaction, data model or system
  context, mentions PlantUML, .puml, @startuml, UML or C4, or asks to fix, tidy or de-clutter an existing PlantUML
  diagram, even if they do not name PlantUML. Not for data charts or Mermaid-only targets.
license: MIT
---

# PlantUML diagrams that look professional

Goal: one diagram, one takeaway, renders clean, nothing overlaps, fits its slot. Verification is mechanical:
`scripts/puml-check` renders the file and measures the SVG (text boxes, edges, size), so never claim a diagram is
good without running it. All paths below are relative to this skill's directory.

## Hard rules (these cause most ugly output; the checker enforces them)
1. **Scaffold from a template**: `scripts/puml-new <type> <file>` gives a tested skeleton with the house style inlined. Adapt it; do not write a preamble from memory.
2. **Declare every element up front, in reading order, with a short alias** (`participant "Web App" as web`, `[Order Service] as orders`). Quote any display name with spaces or punctuation. Never reference an undeclared name.
3. **Edge and message labels: 1-4 words, verb first, ≤ 40 characters.** Detail goes in a `note`, not on the arrow. Participant names, `alt`/`loop` labels, titles and activity arrow labels never auto-wrap: use `\n`.
4. **Never `skinparam linetype ortho` when any edge has a label** (labels overlap, GitHub #2326). Use the template's `polyline`. Ortho only for ER crow's-foot diagrams with no edge text.
5. **Never** `skinparam padding`, `ParticipantPadding`, `handwritten` (they paint a yellow warning banner into the image), `wrapMessageWidth`, `lifelineStrategy` (dead), `SameClassWidth`, `LineColor transparent` in a style block (strips every border), `skinparam dpi` inside the file (breaks measurement; dpi is set at export), `!pragma layout elk|smetana` unless asked, remote `!include http...`, invented `!theme` names, the public plantuml.com server.
6. **Size limits**: ≤ 12 nodes (20 hard cap), ≤ 12-15 edges, ≤ 3-4 containers on a slide (≤ 7 groups ever), ≤ 2 nesting levels, sequence ≤ 7 participants and ≤ 25 messages (about 8 messages fit a 16:9 slide). Over the cap: split by subsystem or phase (or `newpage`), and say so. Prefer a table for mappings/matrices with no flow.
7. **Direction is a measured choice, not a habit**: `puml-new` defaults Graphviz diagrams to `left to right direction` for slides and top-to-bottom for documents, but a broad, shallow graph (one layer fanning out to many) is often already wide in top-to-bottom while a chain or layered system needs left-to-right. If the first check reports `aspect` or a title crossing, flip the direction before anything else and compare. Write every edge in the flow direction; flip the arrowhead (`A <-- B`) instead of the operands. Add a hint (`-right->`, `-[hidden]->`, `-[norank]->`) only to fix a specific reported defect, one per iteration.
8. **Shape is changed by changing the graph** (direction, grid-wrap wide fan-outs, stack packages with hidden links, split), not by `scale` (capped at ~4x and never re-flows) or `!pragma ratio` (only stretches whitespace).
9. **New activity syntax only** (`start`, `:Action;`, `if (q?) then (yes)`, `fork`, `switch`). Balance every `if/endif`, `fork/end fork`: PlantUML auto-closes silently and changes the meaning.
10. **Legend whenever colour, shape or line style carries meaning.** Title = type + scope; on slides omit the title if the slide has one.
11. **A clean render proves nothing**: unknown skinparams and style properties are silently ignored. Trust `puml-check` and your eyes on the PNG, not exit code 0 alone.
12. **Never invent a relationship, component, or technology.** Draw only what the code, config, or the user's words establish; when unsure, ask in plain text or mark it `<<muted>>` with "(unconfirmed)" in the label. Few accurate diagrams beat many speculative ones.
13. **Prefer updating an existing diagram** in the repo over creating a new one that overlaps it; keep names and aliases stable so diffs stay readable. Context and container views hide implementation detail.
14. **No renderer, no claim**: if neither `plantuml` nor `PLANTUML_JAR` is available, still write the file from a template, say that it was not rendered or checked, and stop there.

## Workflow (copy this checklist into your reply and tick it)
1. **Takeaway**: write the one sentence the diagram must prove. Pick the type from the table below (or recommend a table instead).
2. **Inventory** (verifiable intermediate): list `alias | label | group` and `from -> to : label`; count; split if over the limits; decide target (`16:9`, `letter`, or none).
3. **Scaffold**: `scripts/puml-new <type> docs/diagrams/<slug>.puml --title "..." [--preset slide|print] [--direction lr|tb]` then replace the example body.
4. **Check**: `scripts/puml-check docs/diagrams/<slug>.puml --target 16:9 --png --out docs/diagrams/out`. Read every `warn`/`ERROR` line; each carries a 1-based source line. `err` is ln(ratio/target): warnings start at ±0.29 (1.33x off) unless the diagram fits its slot unscaled; `info` lines are advisory.
5. **Fix**: one change per issue kind (shorten label, reorder declarations, direction, hidden link, split). Re-run. Count `warn` lines from the first run that renders and keep going while a run sets a new low; dense diagrams inside the size limits take 4-10 runs. Stop when two runs in a row do not beat the lowest count, or at 12 runs, then simplify or split (moves per type: `references/choosing-and-design.md`, "When the fix loop stalls") and tell the user what you dropped.
6. **Look**: open the PNG the checker wrote (read the image). Judge reading order, crowding, whether labels sit on their edge, consistent shapes, legend. Fix at most 2 more rounds.
7. **Export**: `scripts/puml-render docs/diagrams/<slug>.puml --preset slide|print --out docs/diagrams/out` (SVG + 2x PNG, or SVG + PDF + 300 dpi PNG).
8. **Report**: the takeaway, the `.puml` path, the exported files, the checker's last line (size, ratio, issues), and any simplifications made.

## Commands
| Command | Purpose | Exit |
|---|---|---|
| `scripts/puml-new list` / `scripts/puml-new TYPE [out] [--preset slide\|print] [--direction lr\|tb] [--title T]` | tested template + house style | 0 |
| `scripts/puml-check FILE... [--target 16:9\|4:3\|letter\|letter-landscape\|a4] [--png] [--out DIR] [--format json\|gcc] [--lint-only]` | lint source, render SVG, measure, report issues with line numbers | 0 clean · 1 issues · 2 error |
| `scripts/puml-render FILE... [--preset slide\|print\|web] [--out DIR] [--dark]` | final export, no error images, dpi at export, crop guard | 0 · 2 |
Prerequisite once per machine: `plantuml -testdot` prints "Installation seems OK". If Graphviz is missing PlantUML silently uses a fallback engine that ignores spacing and direction hints. The scripts find the renderer via `plantuml` on the PATH or `PLANTUML_JAR` (plus `JAVA_HOME`/`PLANTUML_JAVA`); with neither they exit 2 with a clear message.

Issue kinds you will see and the usual fix: `text-overlap` / `edge-through-text` / `text-on-node` (shorten labels, drop ortho, reorder, `left to right direction`, link to the package instead of members), `bundled-edges` (`--->` on one edge, or the detail into the node's text), `message-crosses-lifeline` (reorder participants so most messages are between neighbours, shorten), `group-label-crosses-lifeline` (1-2 word `else`/`loop` labels), `aspect` (direction, grid-wrap, hidden links, split), `tiny-text` (cut content, split), `banned-skinparam` / `deprecated-skinparam-banner` (use the `<style>` form named in the message), `long-edge-label`, `ortho-with-labels`, `mermaid-syntax`. Full table: `references/toolchain.md`.

## Choosing the type
| Question the diagram answers | Type (`puml-new` name) |
|---|---|
| Who talks to whom, in what order? (API, auth, webhook) | `sequence` |
| What are the steps, decisions, owners? | `activity` (swimlanes) |
| What states can X be in, what moves it? | `state` (see `references/state.md`) |
| What are the parts and dependencies? (developers) | `component` |
| Same for stakeholders | `c4-context`, `c4-container`, `c4-component` (see `references/c4.md`) |
| Where does it run? (servers, cloud, AWS) | `deployment` (cloud recipe and AWS icons in `references/domains.md`) |
| What is the data shape? | `er` (tables), `class` (code) (see `references/data-model.md`) |
| What is in scope, who uses it? | `usecase` or `c4-context` |
| Network zones, firewalls, VLANs | `network` (see `references/domains.md`) |
| Data flows with trust boundaries / PII | `dfd` |
| Pipeline flow / pipeline infrastructure | `activity` / `component` (recipes in `references/domains.md`) |

## Layout levers (Graphviz diagrams), in the order to try them
1. Declaration order (sets left-to-right order within a layer). 2. `left to right direction` (slides) or top-to-bottom (documents).
3. Shorter labels / move text to notes. 4. Link to the package or container instead of its members: an edge that targets a node nested inside `node`/`cloud`/`package` is drawn across the container and, top-to-bottom, through its title. `user --> browser` (the container) instead of `user --> ui` fixes it when the container is the real boundary; keep nesting ≤ 2 levels. 5. `A -[hidden]-> B` to stack; `together { }` to keep adjacent.
6. `-[norank]->` on a back/cross edge. 7. `skinparam nodesep 40-80` / `ranksep 40-80`. 8. Grid-wrap a wide fan-out (hidden links inside a package).
9. Split. Details and measured evidence: `references/layout.md`. Note: `-right->`/`-left->` and hidden `right` links do not reorder nodes inside clusters (they only allow same rank); reorder declarations instead.

Arrow semantics: `->` same layer, `-->` next layer, each extra dash one more layer; `-up->`/`-left->` reverse the edge; under left-to-right the keywords transpose (`down` draws rightward).

## House style
`puml-new` inlines it (Helvetica, slate text and lines, light fills, one blue `.accent` class, `polyline`, `nodesep 50`, `ranksep 60`,
wrap at 180 px, `hide stereotype`). Apply `<<accent>>` (the one thing to look at), `<<alert>>` (gate / PII / risk) and `<<muted>>` (context, cross-diagram stubs) sparingly and explain them in a legend. Never set `LineColor`/`LineThickness` on `root` or `title`: it strips every element's border in the SVG. Keep one `<style>` block; skinparams only for
layout knobs with no style form. The include form (`assets/lib/house.puml`) exists for projects with many diagrams; the inline form is
portable to Kroki, VS Code server rendering and MCP renderers, which cannot see local includes.

## Output contract
Save sources under `docs/diagrams/<slug>.puml` (or where the project keeps them) and exports under `docs/diagrams/out/` unless told otherwise.
Never overwrite a user's `.puml` without saying what changed. Never send diagram content to a remote renderer or the public plantuml.com server; architecture must not leave the machine.

## References (one level deep)
- `references/choosing-and-design.md`: takeaway-first, limits, inventory format, table-vs-diagram.
- `references/layout.md`: ranks and order, arrow semantics, hidden links, grid-wrap, spacing, shape, engines, debug recipe.
- `references/labels-and-text.md`: wrapping matrix, edge labels, notes, fonts, creole traps, `<style>` vs skinparam.
- `references/sequence.md`, `references/activity.md`, `references/state.md`: type-specific rules, skeletons and shape.
- `references/data-model.md`: ER (cardinality from the schema, rows, stubs for split schemas) and class diagrams.
- `references/c4.md`: C4 macros and argument order, emphasis with tags, boundary titles, splitting container views.
- `references/style.md`: house style, themes that work on white, output sizing (scale cap, dpi, PDF), legends, icons.
- `references/toolchain.md`: CLI facts, exit codes, error formats, checker issue table, vision pass.
- `references/failure-modes.md`: symptom → cause → fix.
- `references/domains.md`: recipes for network zones/VLANs, CI/CD pipelines, DFDs, VMware, Kubernetes, AWS (with icons), learned from the sample runs.
- `assets/templates/*.puml`: the rendered-and-checked templates `puml-new` produces.

## Old patterns (recognise, convert, never generate)
Legacy activity syntax `(*) --> "step"`; `skinparam` for colours and fonts; `!pragma teoz true` (default engine since 1.2026.7);
`skinparam ParticipantPadding`; `scale 1920 width` for resolution; `!include https://raw.githubusercontent.com/.../C4_Container.puml`
(use `!include <C4/C4_Container>` from the bundled stdlib).
