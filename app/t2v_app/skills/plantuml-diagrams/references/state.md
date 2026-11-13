# State diagrams

Verified on PlantUML 1.2026.8 (field test: four lifecycles of 3-7 states).

## Skeleton that renders cleanly
```
@startuml
' house preamble from scripts/puml-new state (includes: hide empty description)
title Order lifecycle
state "Pending payment" as pending      ' long names get an alias; \n wraps them
[*] --> pending
pending --> Paid : payment captured
pending --> Failed : declined
Failed --> pending : retry
Paid --> [*]
@enduml
```

## Rules
- **`hide empty description`** (in the template). Without it every state without a description draws an empty second
  compartment and looks like a table row.
- **Every transition in the source, exactly once, with its trigger.** Count them against the source table or enum and
  say so. Triggers are events, so an event name (`dispute.opened`) is a fine label even though it is not verb-first;
  shorten the rest to 1-4 words and keep the meaning.
- Initial and final pseudo-states: `[*] --> a` and `a --> [*]`. Several initial arrows may carry labels
  (`[*] --> approved : inside refund window`).
- Composite state: `state Active { [*] --> Idle ... }`. Concurrent regions: separate them with `--` inside the braces.
  Each adds a container; keep nesting to 2 levels.

## Shape
A lifecycle is a chain with side branches, and neither pure direction suits it once it has more than 4-5 states.
One field test measured (labels and declaration order change these numbers, so measure your own):
| Lifecycle | left to right | top to bottom | rows (below) |
|---|---|---|---|
| payment, 6 states | 5.11 | 0.76 | 2.55 |
| refund, 6 states | 3.93 | 0.79 | 1.38 |
| order, 7 states, 12 transitions | 2.79 | 1.38 | (TB was enough) |

**Rows:** top to bottom, with `A -> B` (same rank) for the main chain and `A --> B` for the branches below it. Two
opposite edges between the same pair must not both be `->`: their labels land on one line. Make one of them `-up->`
or `-->`, or `-[norank]->` for a pair of peers. A two-sources-to-two-targets shape (K2,2) usually keeps one crossing;
declaring one of the targets first removed it once. If top to bottom stays too tall, try left to right with
`-[norank]->` on the back edges (a retry or "dispute won" edge).

## Several machines
Over the size limits (rule 6), do not draw all machines as one composite diagram. Draw one diagram per machine, plus an
overview with one box per machine (label it "Order: 7 states") and only the cross-machine triggers as edges. Draw the
overview top to bottom with plain `-->`; same-rank `->` rows collapsed four machine boxes into one row with 6-7
crossings in the field test.

## Checker notes
The SVG groups only states that have a description, so puml-check counts states and transitions from the source
(`[*]` arrows are not counted). Edge-over-node checks cannot see undescribed states: look at the PNG.
