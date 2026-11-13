# How the Task2View tool works

The tool is condition H of the view-generation experiment
(`experiments/view-generation-2026-10/`, `run_generate.py` and `elicit.py`) with a real stakeholder in place of
the simulated one. For installing and using it, see [README.md](README.md).

## The flow

```
request + repository
  │
  ├─ Prepare (program)       copy the repository, build the static dependency graph, summarise the repository
  │
  ├─ Phase 1: 42010 inputs
  │    Fill in (agent)       every field from the request and the summary; marks unsure fields; ≤ 2 own questions
  │    Propose (agent)       the fewest views that cover the concerns, one viewpoint each; alternatives only noted
  │    Confirm (stakeholder) one page, one round; skipped if the agent is sure of everything;
  │                          if a field was changed, Propose runs again on the corrected fields
  │
  ├─ Phase 2: per view, in order
  │    Draw (agent, Sonnet)  uml-view skill: find the code, inventory with file:line evidence, PlantUML
  │    Review (agent, Opus)  fresh session: concerns answered? right detail level? supported by the code?
  │    Revise (agent)        once, if the review asks; review again; the better-scored version is kept
  │    Check (scripts)       evidence, inventory = diagram, arrows in the graph, notation and readability
  │  then across views       same names for the same code (check_consistency.py)
  │
  └─ Afterwards (optional, any number of times)
       Feedback (stakeholder → agent → review → checks)
       Rating (stakeholder: four criteria, 1–5, and a comment)
       Export (zip for sharing) → t2v-collect (overview page and tables)
```

## The 42010 fields

| Field (ISO/IEC/IEEE 42010:2022) | Where it comes from | Shown to the stakeholder |
|---|---|---|
| Entity of interest | agent, from the repository summary | yes, editable |
| Part of the system in focus | agent, one sentence | yes, editable |
| Stakeholder | agent, from the request | yes, editable |
| Stakeholder perspective | agent, from the request | yes, editable |
| Detail level (part of the perspective) | agent: overview, balanced or detailed | yes, editable |
| Concerns | agent, as questions the view should answer | yes, editable, can add more |
| Aspect per concern | agent, from six options in `data/questions.yaml` | yes, editable |
| Viewpoint, model kind | Propose, from six viewpoints in `data/viewpoints.yaml` | after confirmation |
| Concern (per view) and concern details | Propose | after confirmation, in the view's inputs |

The six viewpoints are the UML-expressible viewpoints of the Views & Beyond catalogue whose content can be
recovered from code: use case, module (package diagram), component, data model (class diagram), interaction
(sequence diagram), deployment.

**When the agent asks.** The fill-in prompt (`prompts/prefill.txt`) lets the agent mark a field unsure only if
the request gives no basis for it or two readings would lead to different views; extra questions only for
something the fields do not cover that would change the view. Unsure fields are opened and highlighted with the
agent's question; the others show the agent's value with "Edit". No field marked unsure and no extra question:
the confirmation page is skipped.

## Models and Claude Code calls

All calls go through the `claude` command (`t2v_app/claude.py`), with the Claude Code login of the machine.

| Step | Call | Model | Tools |
|---|---|---|---|
| Fill in, Propose | `claude -p … --output-format json --tools ""` | `T2V_GENERATOR_MODEL` (Sonnet 5.5) | none |
| Draw, Revise, Feedback | `claude -p … --permission-mode auto --output-format stream-json` | Sonnet 5.5 | skill scripts, PlantUML, file reading and writing |
| Review | same, fresh session | `T2V_CRITIC_MODEL` (Opus 5.5) | read only; write its own review file |

Revise and Feedback continue the drawing session (`--resume`), so the agent keeps what it found in the code.
Agent sessions run with `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, in a working copy of the repository that has
the two skills in `.claude/skills/` and the static graph in `.claude/repo-graph.json`.

## The skills

`t2v_app/skills/` is a copy of the experiment's skills:

- `uml-view`: what goes in the view and how it stays UML. Rules derived from published skills
  (`DERIVATION.md`), worked examples from spring-petclinic, and the check scripts:
  - `check_inventory.py`: every `file:line` exists; diagram and inventory match both ways; drawn relations have a
    code dependency in the graph; every concern detail is answered or explained; the detail level is the given one.
  - `check_view.py`: notation and readability (use cases inside a boundary, no invented codes, house style, fits a
    screen, one reading direction, grouping).
  - `check_consistency.py`: the same code has the same name in all views of a request.
  - `graph_query.py`, `component_model.py`: queries on the static graph for the agent.
- `plantuml-diagrams`: PlantUML authoring, rendering and layout checks (`puml-check`, `puml-render`).

Check results are kept in the view folder (`inventory-check.txt`, `view-check.txt`, `consistency-check.txt`),
each starting with `passed` or `issues`.

## Feedback on a finished view

`prompts/feedback.txt`: the agent changes what the stakeholder asks and keeps the rest and the model kind. Each
point is checked against the code: supported points get evidence; points the code does not show are drawn,
marked "(unconfirmed)" and listed under Assumptions as stated by the stakeholder; where the code contradicts
the stakeholder, the view follows the stakeholder and the README says what the code shows. Then a fresh review
(`critique-feedback-<n>.json`) and the checks. The view before each round is kept in `before-feedback-<n>/`.
The feedback is also added to the view's clarifications, so later rounds and the review see it.

## Code

```
app/
  setup.sh  check.sh  run.sh     install into .venv / check requirements and login / start
  pyproject.toml                 package t2v-app; commands t2v-app and t2v-collect
  t2v_app/
    config.py     settings (environment variables), limits, timeouts
    server.py     web pages and routes; only 127.0.0.1; form token; content security policy
    pipeline.py   a job, its states and background stages (prepare, generate, feedback); ratings
    repo.py       zip / GitHub clone, the agents' copy, static graph (task2view package), repository summary
    phase1.py     fill in, unsure fields, answers from the form, propose, 42010 records
    phase2.py     draw, review, revise, checks for one view; feedback rounds; consistency across views
    report.py     inputs.yaml, the result README, check and review summaries, download and export zips
    collect.py    t2v-collect: export zips → index.html, jobs.csv, ratings.csv
    claude.py     the two kinds of headless Claude Code calls
    prompts/      prefill, propose, generate, critic, revise, feedback
    data/         questions.yaml (fields and their plain-language explanations), viewpoints.yaml
    skills/       uml-view, plantuml-diagrams
    templates/ static/   pages, one small script, styles
```

## A job on disk

Each request is a folder `~/task2view-jobs/jobs/<YYYYMMDD-HHMMSS-xxxxxx>/`:

| Path | Content | In the export |
|---|---|---|
| `job.json` | state, request, fill-in, answers, records, progress, feedback, ratings | yes |
| `timeline.jsonl` | one line per state or step change, with time | yes |
| `calls/` | prompt and reply of each Fill in and Propose call | yes |
| `logs/` | full event stream of each agent session (`view-N.jsonl`, `.critic-N`, `.revise`, `.feedback-N`) | yes |
| `repo-graph.json` | static dependency graph | yes |
| `out/` | `README.md`, `inputs.yaml`, and `view-N/` (view, inventory, README, checks, reviews, earlier versions) | yes |
| `error.txt` | details of an unexpected failure | yes |
| `upload.zip`, `source/`, `repo/`, `work/` | the repository and the agents' working copies | no |

The export adds `tool.json`: the tool's git commit and whether it was changed locally, the models, the
permission mode, the Claude Code, PlantUML and Python versions, the platform, and whether a personal
`~/.claude/CLAUDE.md` existed.

States of a job: `preparing` → `confirm` (only if the agent asks) → `generating` → `done`; `failed` from any
running state, continued with "Try again" from the stage that failed.

## Ratings and collected results

Ratings use the four criteria of the experiment's blind rating page (`rating.html`): answers the concern; right
level of detail for this stakeholder; correct for the code and correct UML; easy to read; each 1–5, plus a
comment. Each rating records how many feedback rounds the view had at the time, so ratings before and after
feedback can be told apart.

`t2v-collect` reads export zips and writes, next to the unpacked jobs:

- `index.html`: per job the request, what the agent asked, the confirmed fields, each view with its takeaway,
  checks, review verdict, feedback and ratings, and time and estimated cost.
- `jobs.csv`: job, repository, request, state, whether the confirmation page was shown, views, feedback rounds,
  wall-clock minutes, number of agent calls, agent minutes, estimated cost.
- `ratings.csv`: job, view, model kind, time, feedback rounds before the rating, the four scores, comment.

Time and cost come from the result events Claude Code writes in the logs (`duration_ms`, `total_cost_usd`);
the cost is Claude Code's API-price estimate, also on a subscription.

## Not covered yet

- Run with real agents only on single-view requests; two-view requests, feedback on the second view, and the
  automatic start without a confirmation page were checked on rendered pages only.
- No hosting: each person runs the tool on their own machine with their own Claude Code login.
- Only Claude Code; no other model providers.
- The module viewpoint has no worked example in the skill.
