# Choosing the diagram and designing its content

## Write the takeaway first
One sentence: "This diagram shows that ___." If the sentence needs more than ~5 bullets to explain, split (Google tech-writing).
Prefer a **table** when the content is a mapping or matrix with no flow or topology (env var → service → secret source).

## Question → type
| Question | Type | Template |
|---|---|---|
| Who talks to whom, in what order? (API, auth, webhook) | sequence | `puml-new sequence` |
| What are the steps, decisions, owners? | activity (+ swimlanes) | `puml-new activity` |
| What states can X be in and what moves it? | state | `puml-new state` |
| What are the parts and dependencies? (dev audience) | component | `puml-new component` |
| Same, for non-developers / stakeholders | C4 context or container | `puml-new c4-context` / `c4-container` |
| Where does it run? | deployment | `puml-new deployment` |
| What is the data shape? | ER (tables) or class (code) | `puml-new er` / `class` |
| What is in scope and who uses it? | use case or C4 context | `puml-new usecase` |
Not covered by templates but valid: object, timing, Gantt, mindmap, WBS, JSON/YAML, network (nwdiag), Salt wireframes, archimate.

## Limits (policy, tunable)
- One takeaway per diagram. ≤ 12 nodes target, 20 hard cap. ≤ 7 top-level groups, ≤ 3 nesting levels.
- Edge labels ≤ 4 words, verb first, read in the arrow's direction. Unlabelled is better than "uses".
- One dominant flow direction. Consistent arrow semantics (solid = call, dashed = async/event, state as separate legend entries).
- Legend whenever colour, shape or line style carries meaning. Title = type + scope ("Container diagram: Order API").
- Over the cap: split by subsystem or phase (context diagram + one diagram per subsystem), not a bigger diagram.
- Edge crossings are the biggest readability killer (Purchase 1997); fewer crossings beat symmetry and short edges.

## Inventory before code (the verifiable intermediate)
```
nodes: alias | label | group        (count them; split if > 20)
edges: from -> to : label           (≤ 4 words)
direction: TB | LR                  (TB for hierarchies/trees; LR for chains, pipelines, layered flows on slides)
target: 16:9 | letter | none
```
Then scaffold (`puml-new`), fill in, check, look, fix (see below for when to stop), export.

## When the fix loop stalls
Count the `warn` lines from the first run that renders; fix a syntax `ERROR` first, it does not count. Keep going while
a run sets a new lowest count. Stop when two runs in a row do not beat the lowest count so far, or at 12 runs. In the
field tests, dense diagrams inside the size limits took 4-10 runs. When they stall, the remaining issues usually just
move around (an edge that crosses a boundary title crosses another title after each change). Then simplify before you
split, and tell the user what you dropped:

| Type | Simplify | Split |
|---|---|---|
| Sequence | reorder participants so most messages go between neighbours; payload detail in a `note right` | one diagram per flow or phase (`references/sequence.md`) |
| Activity | `switch` instead of `elseif` chains; ≤ 3 lanes on a slide | by phase (`references/activity.md`) |
| Component, deployment, cloud | link to the package, not its members; move a one-to-many fan-out ("writes PDFs, sends email") into the source node; leave out an edge that loops around the whole diagram and say so in the legend | overview + one diagram per layer or zone, `<<muted>>` "(see X)" stubs (`references/domains.md`) |
| Data flow | draw writes only, "reads omitted" in the legend | level 0, then one level-1 diagram per process (`references/domains.md`) |
| Network | a redundant pair as one node ("A / B") with one edge; ports in the node label, not on edges | by site and by layer; physical and logical apart past ~12 nodes (`references/domains.md`) |
| C4 | people and externals beside the boundary; shorter boundary title | split the container view by path and repeat the shared containers (`references/c4.md`) |
| ER, class | names only; `package` per subject area, link the packages | one diagram per subject area with stub tables (`references/data-model.md`) |
| State | composite state for a sub-lifecycle | one diagram per machine + an overview of machines (`references/state.md`) |
