# Labels, text, wrapping, notes, creole

Verified on PlantUML 1.2026.8. The single biggest cause of ugly LLM diagrams is **long text on edges and messages**.

## Contents
1. Wrapping matrix
2. Edge labels
3. Notes
4. Fonts and sizes
5. Titles, captions, legends set the canvas width
6. Creole traps
7. `<style>` vs skinparam

## 1. What wraps what (150 px cap tested)
| Text | `skinparam wrapWidth` | `skinparam maxMessageSize` | `<style>` `MaximumWidth` | `\n` |
|---|---|---|---|---|
| Sequence message | yes | yes | `arrow {}` | yes |
| Sequence note | yes | no | `note {}` | yes |
| Participant name | **no** | no | – | **only way** |
| `alt`/`loop` group label | **no** | no | no | **only way** |
| Class member line | yes (breaks signatures) | no | partial | – |
| Class/component edge label | yes | yes (≥1.2026.3) | `arrow {}` | yes |
| Activity action `:...;` | yes | no | `activity {}` | yes |
| Activity arrow label `-> text;` | **no** | no | no | **only way** |
| Legend | no | – | `legend { MaximumWidth }` | yes |
| Title | no | – | no | **only way** |
The house preamble sets `skinparam maxMessageSize`, `skinparam wrapWidth` and `<style> arrow/note { MaximumWidth }`.
Everything in the "only way" rows is your job: keep it short or break it with `\n`.

## 2. Edge labels
- 1-4 words, verb first, reading in the arrow's direction (`gw --> orders : create order`). ≤ 40 characters hard limit (puml-check lints it).
- Detail goes in `note on link` or a `note right of X`, never on the arrow.
- Each extra dash (`--->`) adds a rank and gives a label room.
- `-[#888,dashed]->`, `..>`, bold etc. change drawing only, not placement.
- Multiplicities: `A "1" --> "0..*" B : places`.
- Never `linetype ortho` with labelled edges (see layout.md).

## 3. Notes
```
note left of X : one line                 ' left|right|top|bottom
note right of X
  multi-line, **creole** ok
end note
note "floating" as N1
N1 .. X
A --> B
note on link : about the edge
' activity:  :step;  then  note right : attached to previous action
' sequence:  note over A, B : spans   |  note across : all   |  / note right of B : same row
```
Notes are layout nodes in Graphviz diagrams (they never overlap but pull layout); in sequence diagrams they add height and,
on the rightmost participant, width. ≤ 2 notes per diagram, short.

## 4. Fonts and sizes
Defaults (SVG): participant 14, message 13, class name 14, members/edge labels 13, activity action **12**, diamond/branch label **11**.
- House preamble: root 14 (slides) / 12 (print), arrows/notes 12/11, title 18/15. Raise activity `diamond`/`arrow` sizes (default 11 is too small on slides).
- Minimum readable: ≥ 9 px once the diagram is scaled to its slot (puml-check `tiny-text` uses the `--target` fit width).
- `skinparam defaultFontSize N` flattens the hierarchy (sets everything to N); prefer per-element sizes in `<style>`.
- Fonts are **not embedded** in SVG/PDF. `<style> root { FontName "Helvetica, Arial, sans-serif" }` emits a real CSS stack in SVG;
  `skinparam defaultFontName "A, B"` does not. Helvetica/Arial exist on macOS/Windows. On Linux Java
  renders in DejaVu Sans (about 12% wider) unless fontconfig prefers Liberation Sans; with it, widths match macOS and
  boxes are 3-7% taller (`references/toolchain.md`).
- `skinparam dpi N` scales **both** PNG and SVG coordinates: never put it in the file; `scripts/puml-render` passes `-Sdpi=` at export.

## 5. Chrome sets the canvas
A 120-character `title` turned a 63 px diagram into 916 px wide. Keep `title`/`caption`/`header` ≤ ~50 chars or use `\n`.
`legend { MaximumWidth 320 }` wraps legends; `title { MaximumWidth }` does nothing. On slides omit the title when the slide has one.

## 6. Creole traps (all reproduced)
| You write | You get | Escape |
|---|---|---|
| `--verbose --force` | strikethrough between the dashes | `~--verbose` or `""--verbose""` |
| `__init__` | underlined `init` | `~__init__` or `""__init__""` |
| two `//` on one line (two URLs) | italic between them | `https:~//host` |
| `<br>` | printed literally | `\n` or `%newline()` |
| `**` at line start in a note | sub-bullet, not bold | move it |
Useful: `<b>`, `<i>`, `<color:#888>`, `<size:12>`, `<&icon>` (OpenIconic), `<:1f600:>` emoji, `|= h |= h |` tables in notes, `[[url label]]`.

## 7. `<style>` vs skinparam
- `<style>` is the preferred mechanism; skinparam is deprecated but still the only way to set `linetype`, `nodesep`, `ranksep`,
  `conditionStyle`, `responseMessageBelowArrow`, `maxMessageSize` on old renderers, `dpi`, `groupInheritance`, `classAttributeIconSize`.
- Mixing works; the **later declaration wins**. Keep one `<style>` block near the top, skinparams before it.
- **Unknown skinparams and unknown style properties are silently ignored** (exit 0). A clean render proves nothing; look at the output.
- On 1.2026.x these paint a yellow "Please use CSS style" banner INTO the image: `skinparam padding`, `ParticipantPadding`, `handwritten`.
  Replacements: `<style> element { Margin N }`, `sequenceDiagram { participant { Margin 0 N } }`, `!option handwritten true`.
- Valid selectors include: root, element, document, arrow, note, title, legend, caption, header, footer, participant, actor, lifeLine,
  activationBox, group, groupHeader, box, sequenceDiagram, classDiagram, class, componentDiagram, component, package, node,
  activityDiagram, activity, diamond, swimlane, partition, stateDiagram, state, usecase, database, queue, cloud, rectangle, card, frame.
  Properties: FontName/Size/Color/Style, BackgroundColor, LineColor, LineThickness, LineStyle, RoundCorner, Shadowing, Padding, Margin,
  MaximumWidth, MinimumWidth, HorizontalAlignment, HyperLinkColor.
- Stereotype classes: `.accent { ... }` applied with `<<accent>>` (activity: `:Step; <<accent>>`); add `hide stereotype` or the label shows.
