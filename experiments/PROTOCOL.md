# Experiment protocol: three conditions

How to run one goal set through the conditions so the results can be compared. It works for any goal set and any repositories.

**The pilot** is `experiments/pilot-2026-10/` (run book: its README): the 2 repositories and their 10 goals in `goals.yaml`, **1 run per goal and condition**. Every condition uses Claude Sonnet 5.5 on the researcher's own Claude subscription: the agents in interactive Claude Code, the pipeline through the Claude Agent SDK (`--llm claude-code:claude-sonnet-5-5`). The goals were used while Task2View was designed, so the pilot is **exploratory**: it reports effect sizes with intervals and describes what happened, and makes no claim of generalisation or significance. No external diagram dataset is used.

| Condition | Who produces the views | Instruction |
|---|---|---|
| **plain-agent** | One coding agent with the repository and the goal | §3.1 |
| **skill-agent** | The same agent and model, plus the Task2View skill (`skill/`) | §3.2 |
| **task2view** | The Task2View pipeline (ADR-006) | §3.3 |

The pipeline's `--evidence retrieval` mode (one call over retrieved code, no tool loop) is an optional ablation for later; it is not part of the pilot.

## 0. Before generating anything
Fix these in writing, with a date, before the first run (a short pre-registration):
1. **Expected facts:** for each goal, the expert lists the facts a good answer must show, in `goals.yaml` under `expected:` (e.g. "ReservationController calls ReservationService.makeReservation"). They are written from the code and the goal, never from any output.
2. **Primary outcome:** the share of a goal's expected facts that its views show, rated by people (§4). Everything else is secondary.
3. **Comparison:** the three conditions against each other: task2view vs skill-agent, task2view vs plain-agent, and skill-agent vs plain-agent, all reported.
4. **Rubric:** rubric v1 of `code/src/task2view/phase8/judge.py` (answers-questions, second-view, layers, placement, layout), frozen. The expert rates with it; the LLM judge is set aside for this pilot.

## 1. Hold fixed across conditions
- **The same repositories:** a prepared copy of each subject (§2), one fresh copy per run.
- **The same goals:** pasted verbatim, with the same run ids.
- **The same generator model in every condition:** Claude Sonnet 5.5 (`claude --model claude-sonnet-5-5` for the agents, `--llm claude-code:claude-sonnet-5-5` for the pipeline). Record the exact model id for every run. A condition on another model confounds the comparison.
- **Runs per goal:** the pilot makes 1 per goal and condition (run id = case id). More runs (`--repeat N`, run ids `<case>@<k>`) would show run-to-run variation.
- **The same notation:** PlantUML.
- **If an LLM judge is used later:** one judge model from a **different model family** than the generator scores all conditions afterwards (§4).
- **Nothing shared between runs:** no agent sees another run's output or any `Task2View/` folder.

## 2. Prepare the subjects
UML models and exported diagrams are the evaluation reference, so no condition may read them. Make a clean copy per run:
```bash
cd Task2View/code
.venv/bin/python scripts/prepare_subject.py --src ../data/<repo> --dst ~/t2v-subjects/<condition>/<run-id>/<repo>
```
Keep the copies outside `Task2View/`, so no agent can wander into the project's own files. The pipeline only reads the repository, so it can share one copy per system.
The script copies the repository without UML models, diagram images, binaries or VCS folders, and writes `<copy>.PREPARED.json` beside the copy (never inside it) listing what it removed. IntelliJ `.form` GUI files are kept: they are source, not diagrams. The pipeline never reads such files anyway, so the copy changes nothing for it; it makes the agent conditions equal to it.

## 3. Run

### Running agents in interactive Claude Code
- One fresh session per run: `cd` into that run's prepared copy and start `claude --model claude-sonnet-5-5`. Paste the instruction below as the first message, then let it work; approve file writes in `./task2view-out/` when asked.
- **Usage limit reached:** Claude Code says when the limit resets. Nothing is lost: the session's history is saved, and the views already written stay in `./task2view-out/`. After the reset, type `continue` in the same window, or reopen the session later with `claude --resume` from the same folder and pick it.
- Order for the pilot: all plain-agent runs, then all skill-agent runs, then the Task2View runs; never two at once, since all draw on the same subscription limits.
- Record the session's name or id in `runs.csv` (see Collect), so an interrupted run can be resumed.

### 3.1 plain-agent
In the run's prepared copy, with **no task2view skill installed** (neither in the copy nor in `~/.claude/skills/`), send exactly:
```text
I am giving you a software repository (the current folder) and a stakeholder's request.
Produce the architecture view or views that best serve this stakeholder for this request,
as a software architect would document them.

Request (verbatim):
<goal>

Write each view as PlantUML source in ./task2view-out/<run-id>/view-<n>.puml (n = 1, 2, …),
and a short ./task2view-out/<run-id>/README.md that says, for each view, what it shows and why.
Base every element on the code in this folder.
```

### 3.2 skill-agent
Copy the skill into the run's prepared copy as `.claude/skills/task2view/` (see `skill/README.md`), start Claude Code there, and send exactly:
```text
Use the task2view skill.
--code .
--goal "<goal>"
--out ./task2view-out/<run-id>
--run-id <run-id>
--notation plantuml
```

### 3.3 task2view
```bash
cd Task2View/code
caffeinate -i .venv/bin/python scripts/run_goal_set.py --goals ../experiments/pilot-2026-10/goals.yaml \
  --out ../experiments/pilot-2026-10/outputs/task2view --llm claude-code:claude-sonnet-5-5 --notations plantuml --wait
```
In the goal-set file, `systems:` points to the prepared copies. Leave `--judge-llm` out. `caffeinate -i` keeps the Mac awake.

**Interruptions lose nothing.** Every model reply is stored in `outputs/task2view/.llm-cache/`, and finished runs are skipped. On a usage limit, `--wait` sleeps until the reset and carries on; without it, the script stops and prints the reset time, and the same command continues later. A run that stopped half-way replays its stored replies (no new usage) and continues from the first call it had not made. Each run's `run.log` records the tool use of every evidence task, and its README the component relations that code and claims agree on, the ones only in code (possible omissions), and the ones only claimed.

### Collect
Copy each agent run's `task2view-out/<run-id>/` to `experiments/<name>/outputs/<condition>/<run-id>/`. Record one line per run in `experiments/<name>/runs.csv`:
```text
condition,run_id,model,tool,tool_version,session,date,duration_min,interrupted,notes
```

## 4. Score
**Expert rating (the outcome).** The expert rates every view blind to the condition:
```bash
cd Task2View/code
.venv/bin/python scripts/make_rating_sheet.py --runs ../experiments/pilot-2026-10/outputs \
  --goals ../experiments/pilot-2026-10/goals.yaml --out ../experiments/pilot-2026-10/rating --rater <name>
```
The expert gets `rating_sheet.csv` and `items/` (anonymised diagram sources, shuffled per goal; render them with any PlantUML viewer). `rating_key.csv`, which maps items back to conditions, stays with the organiser until rating is done. Per item: `facts_shown` (how many of the goal's expected facts the view shows, when expected facts were written) and a 1–5 score per rubric theme.

**Structural facts** need no model: the views each condition chose; for Task2View also grounding (`evidence_model.json`: verified vs rejected claims, code-vs-claim relations) and the validation verdicts (`validation_report.json`); tokens and time per run (`usage.json`).

**Later, not in this pilot:** an LLM judge from another model family (`scripts/judge_outputs.py`), its agreement with human ratings (`scripts/judge_agreement.py`, meaningful with a second rater), and run-to-run stability with repeated runs (`scripts/run_stability.py`).

## 5. Report
For every number reported, state:
- the model and tool version per condition;
- the goal set;
- the repositories and how they were prepared;
- the number of runs per goal.

**Analysis for the exploratory pilot:** pair conditions by goal (one run each); report the per-goal differences in the expert's scores, their mean and a 95% bootstrap interval; report the rest descriptively (views chosen, verdicts, grounding, code-vs-claim relations, tokens and time). With one run per goal, a difference on a single goal can be run-to-run noise; read the pattern across goals. With 10 goals on 2 repositories, only large differences are detectable, and nothing generalises beyond these systems. Claims about generalisation need goals and repositories that were not used during design.
