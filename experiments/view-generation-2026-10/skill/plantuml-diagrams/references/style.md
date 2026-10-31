# Style, themes, output sizing

## House style
`scripts/puml-new <type>` inlines it; `scripts/puml-new style` prints it. Summary: Helvetica, 14/12 px (slides) or 12/11 (print),
slate text `#1F2937`, slate lines `#475569`, light fill `#F1F5F9`, one accent `.accent` (deep blue, white text), `.muted` grey,
notes pale yellow, no shadows, rounded 6, `polyline` links, `nodesep 50`, `ranksep 60`, wrap at 180 px.
It is self-contained on purpose: Kroki, the VS Code server renderer and `@plantuml/mcp-js` cannot see local `!include`s or `!theme ... from`.
For a project with many diagrams, `assets/lib/house.puml` can be copied to `docs/diagrams/lib/` and `!include lib/house.puml`
(relative to the diagram; `-I` and `!include <house>` are broken for nested includes on 1.2026.8).
An included file must not contain the text `@startuml` anywhere, even in a comment: PlantUML then treats it as a
multi-diagram file and reports `cannot include`.

## Themes (`!theme name`)
43 built-ins. On a white page only these are safe for business output: `plain`, `mono`, `vibrant`, `mars`, `toy`, `cerulean`, `materia`,
`spacelab`, `sandstone`, `aws-orange`, `bluegray`. Most others are dark-canvas or transparent designs with faint text, and every theme
hardcodes Verdana. Prefer the house style; use a theme only when the user asks. Never invent a theme name (render fails: "Cannot load theme").
Custom theme file: `puml-theme-<name>.puml`, loaded with `!theme <name> from <dir-or-url>`.

## `<style>` block
```
<style>
root    { FontName Helvetica; FontSize 14; FontColor #1F2937 }
element { BackgroundColor #F1F5F9; LineColor #475569; LineThickness 1.2; RoundCorner 6 }
arrow   { LineColor #475569; LineThickness 1.2; FontSize 12; MaximumWidth 180 }
note    { BackgroundColor #FFF7E0; LineColor #B45309; MaximumWidth 220 }
title   { FontSize 18; FontStyle bold }
legend  { FontSize 12; MaximumWidth 320 }
sequenceDiagram { participant { Margin 0 12 } lifeLine { LineColor #94A3B8 } }
activityDiagram { activity { MaximumWidth 200 } diamond { FontSize 12 } arrow { FontSize 12 } }
.accent { BackgroundColor #1D4ED8; FontColor white; LineColor #1E3A8A }
</style>
hide stereotype
```
**Bug (1.2026.8):** any `LineColor transparent`, and `title { LineThickness 0 }`, strips the stroke from EVERY element in description
diagrams (the PNG rasterizer still draws faint borders, the SVG is borderless). Measured: 35 of 36 element shapes lost their stroke.
The house style therefore sets `LineColor`/`LineThickness` on `element`, `arrow`, `note`, `legend` only and leaves `root` and `title` alone,
which also gives a borderless title. `BackgroundColor transparent` is fine. `'` comments are not allowed inside `<style>`.

Apply classes: `class Order <<accent>>`, `rectangle X <<muted>>`, `participant A <<accent>>`, activity `:Step; <<accent>>`.
Colour never carries meaning alone: add a `legend` when it does. Colourblind-safe accents: `#0072B2` blue, `#E69F00` orange, `#009E73` green, `#D55E00` vermillion.

## Output sizing (verified 1.2026.8)
| Want | Do |
|---|---|
| 2x PNG for a 16:9 deck | `scripts/puml-render file.puml --preset slide` (SVG + PNG at dpi 192) |
| print | `--preset print` (SVG + PDF + PNG at 300 dpi). PDF works without extra jars; fonts not embedded |
| exact pixel width | **not possible**: `scale N width` is silently capped at ~4x; `scale max W*H` only shrinks. Use dpi and let the host fit it |
| huge diagram | PNG silently crops at 4096 px (exit 0); `PLANTUML_LIMIT_SIZE=16384` (puml-render sets it) |
| dark slides | `plantuml --dark-mode` or `puml-render --dark` |
| transparent | `skinparam backgroundColor transparent` |
Design sizes at 96 dpi: slide ≈ 1200x600 usable with ≥ 14 px text; letter portrait ≈ 624x860 with ≥ 12 px; letter landscape ≈ 864x624.
A diagram wider than its slot gets scaled down, and so does its text: puml-check `tiny-text` catches this (`--target` sets the fit width).
`skinparam dpi` inside the file also scales the SVG and breaks measurement; set dpi only at export.

## Titles, captions, legends
- Slides: omit `title` when the slide has one; `caption` rarely. Documents: `caption Figure 3: ...` or number in the document.
- `legend bottom right ... endlegend` whenever colour/shape/line style encodes meaning (C4: `SHOW_LEGEND()` last).
- `header`/`footer` are reliable only on sequence diagrams.

## Icons
OpenIconic `<&cloud>`; stdlib icon sets offline: `!include <awslib/AWSCommon>`, `<azure/...>`, `<gcp/...>`, `<tupadr3/font-awesome-5/...>`,
`<logos/...>`, `<kubernetes/...>`. Sprites enlarge nodes and push the ratio tall; use one consistent scale or none. No remote `!include` URLs.
