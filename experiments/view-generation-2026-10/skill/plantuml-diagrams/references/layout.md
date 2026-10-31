# Layout control (Graphviz-backed diagrams: component, deployment, class, state, use case, object, ER)

Verified on PlantUML 1.2026.8 + Graphviz 15.1.1 by reading the `.dot` PlantUML emits (`!pragma svek_trace on`
writes `svek.dot`). Sequence and activity diagrams do not use Graphviz; see `sequence.md` / `activity.md`.

## Contents
1. The mental model (ranks and order)
2. Arrow length and direction keywords: what they really do
3. Declaration order, hidden links, together, norank
4. Spacing and line routing
5. Shape: how to get landscape vs portrait
6. Density controls
7. Engines: dot vs smetana vs elk
8. Debug recipe

## 1. Mental model
`dot` assigns every node a **rank** (a layer), then **orders** nodes within each rank to reduce crossings.
Packages/rectangles/nodes/clouds are **clusters**: contiguous boxes that cannot interleave. Edge labels are
virtual nodes that take space during layout (except under `linetype ortho`, where they are placed afterwards
and overlap). Everything below is a lever on rank, order, or spacing.

## 2. Arrows
| You write | dot gets | Effect |
|---|---|---|
| `A -> B` | `minlen=0` | A and B may share a rank (side by side) |
| `A --> B` | `minlen=1` | B at least one rank below (right, under LTR) |
| `A ---> B` | `minlen=2` | each extra dash/dot adds a rank |
| `A -up-> B` / `A -left-> B` | edge reversed | B ends up above / to the left |
| `A -right-> B` | `minlen=0` + order hint | extra dashes ignored; crossing-minimisation may override |
| `A -[norank]-> B` | `constraint=false` | drawn, ignored for ranking (use for back/cross edges) |
| `A -[hidden]-> B` | same as `-->` | not drawn, still constrains layout |
| `A <-- B` | `A->B` | A still above B; only the arrowhead moves |

Rules:
- Write every edge in the flow direction you want and flip the arrowhead (`<--`) if semantics need it.
- Start with plain `-->` everywhere. Add a direction hint only to fix a specific defect, then re-render; delete hints that change nothing.
- Under `left to right direction` the keywords transpose: `down` draws rightward, `right` draws downward.
- `up`/`down` are constraints (reliable). `left`/`right` are hints (can be ignored, especially across packages).

## 3. Order, hidden links, together
- **Declare elements in reading order** (top-left to bottom-right) before any link; dot seeds within-rank order from declaration order.
- `together { A  B }` = a borderless cluster: keeps members adjacent. It is NOT "same rank".
- `A -[hidden]-> B` stacks B under A (one `ranksep` of space). `A -[hidden]right- B` nudges B to the right on the same rank.
- Stack sibling packages vertically with a hidden link **between one member of each** (package-to-package hidden links are flaky with nested content).
- **Grid-wrap a wide fan-out**: put the siblings in a package, chain columns with hidden links, link the parent to the package:
  ```
  package "Handlers" as H { [C1]  [C2]  [C3]  [C4]  [C5]  [C6] }
  C1 -[hidden]-> C4
  C2 -[hidden]-> C5
  C3 -[hidden]-> C6
  Root --> H : dispatches
  ```
  (12 children: 1041x145 flat vs 487x409 as a grid.)
- Link to the **package** rather than to every member when the relationship is with the group.

## 4. Spacing and routing (skinparam only, no `<style>` equivalent; ignored by smetana/elk)
```
skinparam nodesep 50        ' px between nodes in a rank (default 35)
skinparam ranksep 60        ' px between ranks (default 60); 40-80 reads as professional
skinparam linetype polyline ' straight segments, labels keep their space. Default = curved splines.
```
- **Never `skinparam linetype ortho` on a diagram with edge labels.** Labels become Graphviz `xlabel`s with no reserved
  space and overlap nodes/edges/each other (GitHub #2326, still open). Ortho is fine for ER diagrams with crow's-foot ends and no text.
- Edges that target a node nested inside a container (`node`, `cloud`, `package`) are drawn across the container and, in top-to-bottom, straight through its title; with two levels of nesting the line visibly runs over the boxes. Measured on the deployment template: linking the inner nodes gave 3 title crossings; linking the containers (`user --> browser`, `browser --> runtime`, `runtime --> payments`) gave 0 with the same information. Rules: link the container when it is the real boundary; keep nesting ≤ 2; `left to right direction` makes edges enter from the side, which avoids the title. puml-check reports `edge-through-text` and `edge-crosses-nested-borders` for these.
- `!pragma edge_corner_radius 10` only rounds ortho corners.

## 5. Shape
There is no "fit to 16:9". `!pragma ratio 0.5625` (height/width) is passed to Graphviz, but it only **stretches whitespace**
(node positions scale, sizes don't): use it at most to nudge a nearly-right diagram. `scale` and `dpi` resize pixels, never layout.
Change the graph instead:
- **Landscape (slides)**: `left to right direction` for chains, pipelines, layered architectures (layers become columns),
  C4 (`LAYOUT_LEFT_RIGHT()`), use cases (actors left). Broad shallow trees are already wide in TB.
- **Portrait (documents)**: top-to-bottom; grid-wrap wide ranks; stack packages with hidden links; narrower nodes via `MaximumWidth`.
- Trim: `ranksep`/`nodesep` move the ratio by 10-30%. Beyond that, split the diagram.
- Measure with `scripts/puml-check --target 16:9|letter`; it reports the ratio error and a hint.

## 6. Density
```
hide empty members                  ' class/object: drop empty compartments
hide circle                         ' drop the (C)/(I)/(E) spot
skinparam classAttributeIconSize 0  ' +/-/# text instead of icons (monochrome-safe)
skinparam groupInheritance 2        ' merge >=2 inheritance arrows into one trunk
skinparam wrapWidth 180             ' or <style> element { MaximumWidth 180 }
skinparam MinClassWidth 120         ' uniform small boxes; NEVER SameClassWidth (one long name doubles the width)
set separator none                  ' a.b.C no longer nests packages
remove @unlinked                    ' drop orphans
```
Keep a diagram to ~12 nodes (20 hard cap) and ≤ 7 groups; split by subsystem or phase beyond that.

## 7. Engines
| | dot (default) | `!pragma layout smetana` | `!pragma layout elk` |
|---|---|---|---|
| arrow length / up-down hints | yes | mostly | **ignored** |
| `left to right direction` | yes | yes | **ignored** |
| nodesep / ranksep / linetype | yes | **ignored** | **ignored** |
| label collisions | possible (ortho) | possible | none, but labels can sit away from their edge |
| SVG groups for puml-check | full | full | **no link/cluster groups** (edge checks disabled) |
Stay on dot. Since 1.2026.7 PlantUML **silently falls back to smetana when `dot` is missing** (exit 0, no warning):
run `plantuml -testdot` once per machine. ELK is still "alpha", needs Java 17, and is only worth it for an
orthogonal look on label-light diagrams.

## 8. Debug recipe
1. `plantuml -testdot` (Graphviz present?).
2. `scripts/puml-check file.puml --target ...` and read the issue lines (source line numbers are 1-based).
3. Add `!pragma svek_trace on`, render, read `svek.dot`: check `minlen`, reversed edges, `constraint=false`, clusters, node order.
4. Change **one** thing per iteration (a direction, a hidden link, a split). Re-check. When to stop, and what to
   simplify or split then: `references/choosing-and-design.md`, "When the fix loop stalls".
