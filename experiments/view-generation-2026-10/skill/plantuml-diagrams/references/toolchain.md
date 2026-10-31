# Toolchain and verification loop

## Install / check (macOS)
```
brew install plantuml          # pulls graphviz + openjdk; wrapper at /opt/homebrew/bin/plantuml
plantuml -version              # prints PlantUML AND Graphviz versions
plantuml -testdot              # "Installation seems OK" — if dot is missing PlantUML silently falls back to smetana
```
Linux/CI: download `plantuml-<ver>.jar` from GitHub releases (Debian's apt package is years old) or `docker run --rm -i plantuml/plantuml -tsvg -pipe`.
Pin PlantUML ≥ 1.2026.7 (dot crashes now fail the run) and pin Graphviz; layouts differ across versions (the 0.2.0 dfd
template: 722x541 on Graphviz 15.1.1, 573x610 on 2.43; CI runs both) and across fonts. Linux: Java does not find Helvetica and renders in
fontconfig's first sans-serif family, DejaVu Sans (about 12% wider), even with Liberation Sans installed. Install
Liberation Sans and prefer it, then widths match macOS (boxes 3-7% taller):
```
mkdir -p ~/.config/fontconfig/conf.d
cat > ~/.config/fontconfig/conf.d/50-plantuml-liberation.conf <<'XML'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias><family>sans-serif</family><prefer><family>Liberation Sans</family></prefer></alias>
  <alias><family>Helvetica</family><prefer><family>Liberation Sans</family></prefer></alias>
</fontconfig>
XML
fc-cache -f && fc-match sans-serif   # "Liberation Sans"
```

## The three scripts (relative to the skill directory)
| Script | Does | Exit |
|---|---|---|
| `scripts/puml-new TYPE [out.puml] [--preset slide\|print] [--title ...]` | tested template + inline house style | 0 |
| `scripts/puml-check FILE... [--target 16:9\|4:3\|letter\|letter-landscape\|a4] [--png] [--out DIR] [--format json\|gcc]` | source lint → render SVG → geometry checks → report with source lines | 0 clean, 1 issues, 2 error |
| `scripts/puml-render FILE... [--preset slide\|print\|web] [--out DIR] [--dark]` | final export with `--no-error-image`, dpi at export, crop guard | 0, 2 |

### puml-check issue kinds
| kind | meaning | typical fix |
|---|---|---|
| `banned-skinparam` (lint) | padding/ParticipantPadding/handwritten/wrapMessageWidth/lifelineStrategy/SameClassWidth | use the `<style>` form named in the message |
| `ortho-with-labels` (lint) | `linetype ortho` + labelled edges | polyline / default |
| `long-edge-label` (lint) | label > 40 chars | shorten, `\n`, note |
| `mermaid-syntax`, `missing-start/end` (lint, error) | not PlantUML | rewrite |
| `deprecated-skinparam-banner` | PlantUML painted a warning into the image | remove that skinparam |
| `missing-stroke` | most element shapes have no stroke in the SVG (invisible in PNG review; borderless in SVG/PDF) | remove `LineColor transparent` / `LineThickness 0` from `root`/`title`; put line properties on `element`/`arrow` |
| `text-overlap` | two text boxes intersect | shorten labels, more `nodesep`, reorder, split |
| `edge-through-text` | an edge crosses a label (ortho, or edges entering a package through its title) | polyline, `left to right direction`, move source, `[norank]` |
| `text-on-node` | a label sits on a foreign node | as above |
| `edge-through-node` / `edge-through-cluster` (info) | an edge passes over a node or package it does not connect to | reorder declarations, `[norank]`, move the node, split |
| `edge-crosses-nested-borders` (info) | an edge crosses 3+ container borders (line drawn over boxes) | link the container instead of the inner node; flatten nesting |
| `detached-label` | label > 5x font size from its edge | drop ortho; shorter edge |
| `crowded-ends` | class diagrams: multiplicities of two edges at one node less than half a font size apart (on a shared trunk they are reported in `bundled-edges` instead) | raise `skinparam nodesep`, or `--->` on one of the edges |
| `bundled-edges` | two or more edges at one node run along one shared trunk (40 px or more within 3 px of each other, 20 px clear of the node); they read as one line with crowded labels | give each target its own rank (`--->` on one edge), move the detail into the node's text, link to a package |
| `message-crosses-lifeline` | sequence text crossed by intermediate lifelines | reorder participants, shorten, wrap |
| `message-spans-lifelines` (info) | sequence arrows drawn across the lifelines between their two participants; names the worst pairs. The summary line prints `crossings=n/a lifeline-crossings=N` for sequence diagrams | reorder participants so the named pairs are neighbours |
| `group-label-crosses-lifeline` | an `alt`/`else`/`loop` label runs past the next lifeline (they never wrap) | 1-2 word labels; start the group at a participant further left |
| `group-label-on-lifeline` (info) | the group's own first lifeline touches the label's first characters (always drawn there) | keep the label short |
| `label-on-border` | an edge label lies on a container border line | shorten, lengthen the edge (`--->`), move text into the node |
| `edge-through-own-label` | an edge runs through its own label (same-rank `->` edges, HA pair links) | move the text into the node or a note |
| `text-struck-by-line` | activity / nwdiag text crossed by a line | shorter partition title, move the branch; nwdiag: `description` not `address` |
| `busy` (info) | > 15 edges or > 4 containers | split, draw primary flows only |
| `comment-in-style`, `nwdiag-under-startuml`, `stray-start-marker` (lint) | source constructs PlantUML rejects or misreads | as the message says |
| `aspect` | ratio off target by > 1.33x and larger than the target's usable slot; `info` when it fits the slot unscaled (and says how much of the slot it fills) | direction, rows (`->` same rank, `-->` next row), grid-wrap, hidden links, split |
| `tiny-text` | smallest text < 9 px when fit to the slot width | direction or rows to use the slot's shape, cut content, split |
| `stale-render` / `STALE` (on error) | an older SVG/PNG/PDF of the same file is still in `--out` after this render failed | do not look at it; fix the error first |
| `png-cropped` | hit PLANTUML_LIMIT_SIZE | raise limit or shrink |
| `sparse`, `many-crossings` (info) | metrics, not failures | reorder, link to packages, split |

Line numbers in reports are 1-based source lines of your file (PlantUML `-stdrpt:2`, and SVG `data-source-line`+1). With
`!include` (C4, awslib, a house style file) `data-source-line` points into the expanded library, so the checker maps each
issue back through the element's alias (or both ends of an edge) to the line in your file. The checker reads PlantUML's own
`textLength` widths, so it measures layout intent, not viewer font substitution.

Slots (usable px at 96 dpi): 16:9 1200x600, 4:3 900x560, letter 624x864, letter-landscape 864x624, a4 602x931,
a4-landscape 930x602. Node and edge counts leave out notes and `[*]` pseudo-states; ER diagrams report as `CLASS/ER`.

## Raw CLI facts (1.2026.8)
- Best error output: `plantuml -tsvg -stdrpt:2 --no-error-image file.puml` → `file.puml:LINE:error:msg` (1-based), exit 200.
  Without `--no-error-image` a syntax error **still writes an image** (a red error picture).
- `plantuml -syntax < file` prints type or `ERROR` + 0-based line. `--check-syntax` gives no line and misses: unknown skinparams,
  unknown style properties, bad skinparam values, a missing `endif`.
- Exit codes: 0 ok, 50 no file, 100 no diagram, 200 syntax error.
- `-ttxt` ASCII art: full fidelity for sequence diagrams (cheap structure check in tokens), boxes only for class/component.
- `--preproc` shows the expanded source (debug includes); `!pragma svek_trace on` dumps the Graphviz input (`svek.dot`).
- Includes: `!include lib/house.puml` resolves relative to the diagram file. The included file must not contain `@startuml` (even in a comment) or you get `cannot include`.
- `--list-keywords`, `-language` (skinparam + colour lists), `help themes` / `skinparameters` as diagram bodies list what exists.
- Servers: `plantuml -picoweb:8080` (headers give width/height/error line, 1-based); `plantuml/plantuml-server` and Kroki
  (0-based error lines; cannot see local includes). The CLI is enough for one agent (~0.7 s per call; batch files per call).
- Official MCP `@plantuml/mcp-js` renders SVG only and ignores `!theme`/`!include`; not a substitute for the local CLI.
- Never use the public plantuml.com server for client content.

## Vision pass
After puml-check is clean, render a PNG (`puml-check --png` or `puml-render`) and look at it (Read the PNG). Judge: reading order,
crowding, labels near their edge, consistent shapes, legend usefulness, ratio for the slot. Fix at most 2 more rounds; then
simplify or split and say so.
