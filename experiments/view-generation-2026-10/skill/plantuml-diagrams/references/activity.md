# Activity diagrams (new syntax only)

Never generate legacy syntax (`(*) --> "step"`). Mixing the two fails to render.

## Skeleton
```
@startuml
' house preamble from scripts/puml-new activity (activity { MaximumWidth 200 }, diamond/arrow FontSize 12)
title Refund approval
|Customer|
start
:Request refund;
|Support|
:Review request;
if (Amount > $500?) then (yes)
  |Finance|
  :Approve or reject;
else (no)
  |Support|
  :Approve;
endif
|Customer|
:Receive decision;
stop
@enduml
```

## Rules
- Actions: `:Verb object;` 2-5 words. Wrap long ones with `\n` or rely on `activity { MaximumWidth }`.
- Conditions: `if (Question?) then (yes) ... else (no) ... endif`. Branch labels 1-2 words (they sit at 11 px next to the diamond and do not wrap).
  `skinparam conditionStyle diamond` keeps long condition text outside the diamond (`InsideDiamond` overflows, GitHub #649) BUT drops the
  `is (yes) not (no)` labels of `repeat while`; the template leaves the default. If you need it, label the exit with `-> no;` after `repeat while`.
- 3+ branches: use `switch (x?)` / `case (a)` / `endswitch` (cleanest layout). `elseif` chains go horizontal and get wide;
  `!pragma useVerticalIf on` stacks them.
- `fork` / `fork again` / `end fork` for parallel work; `repeat` / `backward :x;` / `repeat while (more?) is (yes) not (no)`; `detach` or `kill` to end a branch without a merge arrow.
- Arrow labels: `-> label;` before the next action; only `\n` wraps them. Style one arrow: `-[#blue,dashed]->`.
- Every `if` needs `endif`, every `fork` an `end fork`: PlantUML **auto-closes silently** (exit 0) and the meaning changes. Check the picture.
- Gates (pipelines): happy path inside `then`, exit (`stop`) in `else`; an empty-else early exit grows a long bypass edge. `kill` inside nested blocks may draw nothing; use `stop`.
- Fork/join bars take the element fill; the template sets `activityBar { BackgroundColor #475569 }` so they stay visible.
- Notes: `note right : text` attaches to the previous action; `floating note left : ...` does not.
- `partition Name { ... }` or `group` to box a phase. Swimlanes: `|Lane|`, `|#EEF|alias| Lane title`.
- Swimlane widths cannot be equalised on 1.2026.8 (`swimlaneWidth same` is a no-op); a fork or if inside a lane widens it. Use `\n` in long lane titles.
- `:a; <<accent>>` applies a style stereotype class.

## Shape
Activity diagrams are tall; swimlanes make them wide. For a 16:9 slide: ≤ 12 actions, ≤ 3 lanes, one decision level.
For letter portrait: no swimlanes (or 2), ≤ 20 actions, then split by phase.
