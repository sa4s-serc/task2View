# Failure modes: symptom → cause → fix

| Symptom | Cause | Fix |
|---|---|---|
| Exit 200 "Syntax Error? (Assumed diagram type: sequence)" on line N | Mermaid syntax, unquoted multi-word name (`participant Web App`), legacy activity `(*) -->` mixed with `:a;`, C4 macro without `!include <C4/...>` | quote names + `as alias`; new activity syntax only; add the stdlib include |
| "Cannot load theme X" | invented theme | use a built-in from `help themes` or drop it |
| "Cannot open URL" / `cannot include` | remote or missing include, or the included file contains the text `@startuml` (even in a comment) | stdlib `<C4/...>`, local file, or inline style; strip `@startuml` from the include |
| All boxes lose borders (SVG/PDF only; PNG hides it) | `LineColor transparent` or `LineThickness 0` on `root`/`title` in `<style>` | set `LineColor`/`LineThickness` on `element`/`arrow`/`note` only; puml-check reports `missing-stroke` |
| Render OK but setting had no effect | unknown skinparam / style property (silently ignored), or smetana fallback because dot is missing | check spelling against `plantuml -language`; `plantuml -testdot` |
| Yellow "Please use CSS style instead of skinparam X" banner in the image | `skinparam padding`, `ParticipantPadding`, `handwritten` | `<style>` Margin / `participant { Margin 0 N }` / `!option handwritten true` |
| Edge labels overlapping nodes/edges | `linetype ortho` | polyline or default |
| Labels in a crowded row between two layers | long labels on many edges between the same two ranks | shorten to ≤ 4 words, move detail to notes, link to the package, split |
| Edge crosses a package/node title, line runs over nested boxes | edge targets a node nested inside a container; top-to-bottom enters through the title | link the container instead of the inner node, keep nesting ≤ 2, `left to right direction`, `[norank]` on the cross edge |
| Very wide diagram | many siblings at one rank, or sibling packages side by side | grid-wrap (hidden links in a package), stack packages with a hidden link between members, split |
| Very tall diagram | long chain in TB, long sequence | `left to right direction`; for sequence: fewer messages / `newpage` |
| Sequence message text struck through by lifelines | message between non-adjacent participants with long text | reorder participants so most messages are between neighbours; shorten; `maxMessageSize` |
| Participant columns too far apart | a long message, note or group label between that pair | `\n` in the label, shorten |
| Text struck through / underlined / italic unexpectedly | creole `--x--`, `__x__`, two `//` | escape with `~` or `""..""` |
| `<br>` printed literally | not supported | `\n` |
| Activity branch merges unexpectedly | missing `endif` / `end fork` (auto-closed silently) | balance the blocks |
| Diamond text overflows | `conditionStyle InsideDiamond` | `conditionStyle diamond` |
| Swimlanes uneven | by design on 1.2026.8 | accept; `\n` in titles |
| PNG cut off at 4096 px, exit 0 | PLANTUML_LIMIT_SIZE | `PLANTUML_LIMIT_SIZE=16384` (puml-render does this) or split |
| PNG smaller than `scale N width` asked for | scale capped ~4x | dpi at export (`puml-render --dpi`) |
| SVG looks different on another machine | fonts not embedded; dot version | ship PNG/PDF, pin versions, check in the delivery environment |
| Direction hints ignored | `left`/`right` are hints; ELK ignores all; conflicting hints | fewer hints; `together {}`; stay on dot |
| Hidden package-to-package link ignored | nested populated packages | hidden link between one member of each |
| Every state box has an empty lower compartment | states without a description | `hide empty description` (in the state template) |
| ER columns all show the same circle; nullability invisible | default attribute icons | `skinparam classAttributeIconSize 0` and `*` for NOT NULL (in the ER template) |
| Box glyph `▯` before each C4 legend entry | C4-PlantUML's border-colour swatch (U+25AF), by design | nothing to fix |
| `<<accent>>` has no effect on C4 elements | C4 macros set their own colours | `AddElementTag("accent", ...)` and `$tags="accent"` (references/c4.md) |
| Arrows turn grey after adding AWS icons | `awslib/AWSCommon` sets its own arrow style, and an include after the house `<style>` wins | put every `!include <awslib/...>` before the style block |
| Next `!include <awslib/...>` fails with a syntax error | `awslib/AWSCommon` not included first | include it first |
| Two opposite labelled edges between one pair overlap | both written as same-rank `->` | make one `-up->` or `-->` |
