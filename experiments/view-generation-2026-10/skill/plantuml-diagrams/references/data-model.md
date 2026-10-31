# ER and class diagrams

Verified on PlantUML 1.2026.8 (field test: a 16-table schema and a 13-class domain model).

## ER (`puml-new er`)
- **Columns:** `* col : type` = NOT NULL, no marker = nullable. The template's `skinparam classAttributeIconSize 0`
  makes that visible; without it PlantUML draws the same circle on every column. One tag per column (`<<PK>>`,
  `<<FK>>`, `<<UQ>>`): two tags wrap onto a second line at 12 px.
- **Cardinality comes from the schema, end by end:** a NOT NULL FK is `||` at the parent; a nullable FK is `|o`; a
  UNIQUE FK makes the child end `o|` (one-to-zero-or-one); otherwise `o{`. Check every edge against the DDL.

| Source | Edge |
|---|---|
| `orders.user_id NOT NULL` | `users ||--o{ orders` |
| `orders.hold_id NULL` | `holds |o--o{ orders` |
| `tickets.order_item_id NOT NULL UNIQUE` | `items ||--o| tickets` |

- **Rows:** one dash keeps the same rank (`a ||-o{ b` puts b beside a), two dashes start the next row. Put the table
  with the most links in the middle of a row. Writing the edge reversed (`tiers }o-|| events`) flips which side a table
  lands on. Rows pay off on small, tree-like schemas (a 5-table core: 2.97 left to right, 0.55 top to bottom, 1.76 in
  rows). On a dense 9-table schema they made it worse (13 crossings): there, keep top to bottom with a few `->` pairs
  and check crossings, not just the ratio.
- **Composite keys:** mark each key column `<<PK>>` (`* venue_id : uuid <<PK>>`, `* user_id : uuid <<PK>>`).
- **Two FKs to one table** (`requested_by`, `reviewed_by`): label both edges. Labels need polyline (the house default);
  ortho turns them into overlapping xlabels and merges parallel edges into one line.
- **Large schemas:** an overview with table names only, then one diagram per subject area. Neighbours from other areas
  are stubs: `entity "users" as users <<muted>>` with no body, plus `hide empty members` so the stub is just its name.
  Put stubs in a top row so the FK edges stay short. An overview over the edge cap (16 tables had 25 FKs) stays
  crowded whatever the layout: draw it with names only and the edges between subject areas, or group tables in
  `package` boxes per subject area and link the packages.

## Class (`puml-new class`)
- **Multiplicities sit at their own end:** `A "1" --> "0..*" B` puts `0..*` next to B. They sit on the node border and
  collide with short edge labels on same-rank edges; `skinparam nodesep 80-110` moves them apart. Multiplicities of two
  edges at one class can crowd (puml-check: `crowded-ends`): nodesep moves them apart, unless the edges share one trunk
  into the class (`bundled-edges`), where only `--->` on one of the edges does (1.2026.8).
- **Rows** work as for ER: `->` same rank, `-->` next row; flip the arrowhead (`Order "1" <-- "0..*" Payment`), not
  the operands, to place a class below without reversing the meaning. A 13-class model left to right came out 2.47
  wide with 5.7 px text; rows (services, their products, data) fixed it.
- **Enums:** use them as attribute types (`status: OrderStatus`); draw enum boxes only in a diagram about the states,
  and then beside their owner (`Order -> OrderStatus`).
- **Interfaces:** use `interface` only when the source declares or documents one; otherwise `class`.
- Show 3-6 members per class; past 9-10 classes, drop the ones the takeaway does not need and say which.

## Checker notes
ER diagrams report as `CLASS/ER`. The `ortho-with-labels` lint counts crow's-foot labels and honours a later
`linetype polyline`. Merged or overlapping ortho edges are not detected: look at the PNG.
