# Sequence diagrams

Teoz is the only sequence engine since 1.2026.7 (`!pragma teoz true` is a harmless no-op; older renderers still need it
for `&` parallel messages, nested `box`, anchors).

## Skeleton that renders cleanly
```
@startuml
' house preamble from scripts/puml-new sequence (includes: participant { Margin 0 12 }, arrow { MaximumWidth 180 })
title Checkout
hide footbox
autonumber "<b>00"
actor       "Customer"      as cust
participant "Web App"       as web
participant "Order\nService" as orders      ' \n is the ONLY way to wrap a participant name
database    "Orders DB"     as db
cust   -> web    : place order
web    -> orders ++ : POST /orders          ' ++ activate, -- deactivate, ** create, !! destroy
orders -> db     : insert PENDING
orders --> web   -- : 201 Created
web    --> cust  : confirmation
@enduml
```

## Rules
- **Declare every participant up front, in left-to-right reading order**, with a short alias. Otherwise first mention sets the order and a later edit reshuffles the diagram.
- Order participants so that most messages go between neighbours. A message between distant participants is drawn across
  the lifelines in between and its text is crossed by them (puml-check: `message-crosses-lifeline`; the arrows alone: `message-spans-lifelines`, info).
- Message text ≤ ~40 chars; the preamble wraps at 180 px (`maxMessageSize` + `arrow { MaximumWidth }`). Put payload detail in a `note right`.
- `alt`/`loop`/`opt` labels and `participant` names **never auto-wrap**; break them with `\n`. A long group label widens
  the gap between that pair of lifelines for the whole diagram.
- ≤ 7 participants and ≤ 25 messages per diagram; beyond that `newpage Part 2` or split by phase. One level of `alt` nesting.
- `hide footbox` (saves height), `autonumber "<b>00"` (lets prose refer to steps).
- Spacing: `<style> sequenceDiagram { participant { Margin 0 N } }` widens the gap between lifelines. `skinparam ParticipantPadding` paints a warning banner into the image and is ignored. `participant { Padding }` only fattens the boxes.
- `|||` or `||40||` add vertical space; `== Phase ==` divider; `... 5 min later ...` delay; `ref over A, B : see diagram X`.
- `skinparam responseMessageBelowArrow true` only affects arrows written right-to-left in source (`A <-- B`).
- `skinparam style strictuml` = filled arrowheads and no footbox.
- Solid lifelines: `<style> sequenceDiagram { lifeLine { LineStyle 0 } }` (`lifelineStrategy solid` is dead).
- Boxes: `box "Backend" #EEF5FF` ... `end box` groups participants (nested boxes OK on teoz).
- Parallel messages on one row: second line starts with `&`. Anchors `{start}`/`{end}` and `{start} <-> {end} : <2s` exist but the duration arrow draws over text; avoid on dense diagrams.
- `!pragma sequenceMessageSpan true` saves width but lets text cross lifelines; avoid.
- **Group labels** (`alt`, `else`, `loop` text): write `else declined`, never `else [declined]`. PlantUML adds the
  brackets itself, and `[text]` is link syntax: it renders as link text and drops words (lint `bracket-group-label`).
  The label usually starts about 11 px left of the group's first lifeline, so that lifeline touches its first characters
  (`info`); a note spanning further left widens the frame and moves the label with it. A label long enough to reach the
  next lifeline is a defect (`group-label-crosses-lifeline`): 1-2 words (`else ok`, `else declined`, `loop 30 s`), or
  start the group at a participant further left. Padding the label with spaces only moves the crossing into the gap.
- One level of nesting is fine (`alt` inside `alt`); the inner frame starts further left of its content and makes
  the label problem worse, so keep inner labels shortest.
- **Notes:** `note over a, b` spans a pair and is the narrowest place for detail; use the block form for more than one
  line (`note over a, b` ... `end note`). A one-line note with `\n` centres its lines unevenly. `note right of x`
  next to a busy lifeline spills across the next one.
- **Activations** (`++`/`--`) are optional. Skip them unless the reader needs to see who is busy: notes and group
  frames draw over the bar.
- **Self-messages** (`api -> api : validate`) add a loop and about 50 px of height each; a note is shorter.
- Participant shapes: `actor`, `participant`, `database`, `queue`, `boundary`, `control`, `entity`, `collections`.
  `database` puts its name under the cylinder, so its header sits higher than its neighbours (cosmetic).

## Shape
A sequence diagram is as wide as its participants (plus the longest message between neighbours) and as tall as its
messages: about 50 px per message plus about 40 px per `alt`/`else` branch, measured on 1.2026.8.
- **16:9 slide:** 4-6 participants and about 8 messages. 13 messages with 5 participants came out 704x644 (ratio 1.09).
  Over that, split by phase (one diagram per flow) rather than shrinking text.
- **To get wider:** fewer self-messages and activations, detail in `note over a, b`, and more lifeline spacing with
  `<style> sequenceDiagram { participant { Margin 0 40 } }`. The effect is steep: 4 participants measured 613, 881 and
  1265 px wide at Margin 12, 62 and 110. Raise it in steps of about 15 and re-check.
- **Letter portrait:** splits reach about 0.8 only at about 20 messages. Short flows (4-10 messages) come out 1.3-2.0
  wide; that is fine when the diagram fits the page width unscaled (puml-check then reports `aspect` as `info`).
- **Documents:** any count, split by flow at about 25 messages. Splitting by flow beats `newpage` when the flows use
  different participants: `newpage` repeats one participant row on every page.
- `left to right direction` does nothing here.
