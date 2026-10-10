# Experiment protocol: three conditions

How to run one goal set through the conditions so the results can be compared. It works for any goal set and any repositories.

**The pilot** is `experiments/pilot-2026-09/goals.yaml`: the 2 repositories and their 10 goals, 3 runs per goal and condition. The goals were used while Task2View was designed, so the pilot is **exploratory**: it reports effect sizes with intervals and describes what happened, and makes no claim of generalisation or significance. No external diagram dataset is used.

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
4. **Rubric:** rubric v1 of `code/src/task2view/phase8/judge.py` (answers-questions, second-view, layers, placement, layout), frozen.

## 1. Hold fixed across conditions
- **The same repositories:** a prepared copy of each subject (§2), one fresh copy per run.
- **The same goals:** pasted verbatim, with the same run ids.
- **The same generator model in every condition:** run both agent conditions on the same model as the pipeline's `--llm` (`anthropic:claude-sonnet-4-5` for the pilot), and record the exact model id for every run. A condition on another model confounds the comparison.
- **Three runs per goal and condition**, with run ids `<case>@1`, `<case>@2`, `<case>@3`: model output varies between runs even at temperature 0.
- **The same notation:** PlantUML.
- **The same judge:** one judge model from a **different model family** than the generator (not Anthropic when the generator is Claude) scores all conditions afterwards (§4).
- **Nothing shared between runs:** no agent sees another run's output or any `Task2View/` folder.

## 2. Prepare the subjects
UML models and exported diagrams are the evaluation reference, so no condition may read them. Make a clean copy per run:
```bash
cd Task2View/code
.venv/bin/python scripts/prepare_subject.py --src ../data/<repo> --dst /tmp/t2v-subjects/<run-id>/<repo>
```
The script copies the repository without UML models, diagram images, binaries or VCS folders, and writes `<copy>.PREPARED.json` beside the copy (never inside it) listing what it removed. IntelliJ `.form` GUI files are kept: they are source, not diagrams. The pipeline never reads such files anyway, so the copy changes nothing for it; it makes the agent conditions equal to it.

## 3. Run

### 3.1 plain-agent
Open the agent on the prepared copy, with **no skill installed**, and send exactly:
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
Install the skill in the prepared copy (see `skill/README.md`: Codex `.agents/skills/`, Cursor `.cursor/skills/`, Claude Code `.claude/skills/`), open the agent on it, and send exactly:
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
.venv/bin/python scripts/run_goal_set.py --goals ../experiments/pilot-2026-09/goals.yaml --repeat 3 \
  --out ../experiments/pilot-2026-09/outputs/task2view --llm anthropic:claude-sonnet-4-5 --notations plantuml
```
In the goal-set file, `systems:` should point to the prepared copies (or use `code:` per case). Leave `--judge-llm` out here; all conditions are judged together in §4. Each run's `run.log` records the tool use of every evidence task, and its README the component relations that code and claims agree on, the ones only in code (possible omissions), and the ones only claimed.

### Collect
Copy each agent run's `task2view-out/<run-id>/` to `experiments/<name>/outputs/<condition>/<run-id>/`. Record one line per run in `experiments/<name>/runs.csv`:
```text
condition,run_id,model,tool,tool_version,date,duration_min,notes
```

## 4. Score
**Task fit:** score every view of every condition with the same judge model. The judge reads `view.json` when a condition wrote one, and otherwise the diagram source only.
```bash
cd Task2View/code
.venv/bin/python scripts/judge_outputs.py --runs ../experiments/<name>/outputs --goals <goal set>.yaml \
  --judge-llm <provider:model different from the generator>
```
This writes `judge.json` per run and `experiments/<name>/judge_summary.csv`.

**Structural checks** need no model:
- view kinds chosen (`view_plan.json`, or the plain agent's README);
- grounding (`evidence_model.json`: verified vs rejected claims);
- the validation verdicts (`validation_report.json`).

**Human rating (primary outcome):** the expert rates, blind to the condition. One rater is enough for the pilot's outcome; a second, independent rater would later allow the judge to be validated (human–human agreement as the yardstick).
```bash
.venv/bin/python scripts/make_rating_sheet.py --runs ../experiments/pilot-2026-09/outputs \
  --goals ../experiments/pilot-2026-09/goals.yaml --out ../experiments/pilot-2026-09/rating --rater <name>
```
Each rater gets `rating_sheet.csv` and `items/` (anonymised, shuffled per goal); `rating_key.csv` stays with the organiser. Per item, a rater records `facts_shown` (how many of the goal's expected facts the view shows) and a 1–5 score per rubric theme. Rate all items, or a random sample of 60–100 views when that is too many. Then:
```bash
.venv/bin/python scripts/judge_agreement.py --ratings ratings.csv --key ../experiments/pilot-2026-09/rating/rating_key.csv \
  --judge ../experiments/pilot-2026-09/judge_summary.csv
```
This prints the weighted kappa of the judge against each rater (and between raters, when there are two), with 95% bootstrap intervals. With one rater it is indicative only. The judge stays a reported, non-gating signal.

**The earlier expert review** (`pilot-2026-09/review/expert_labels.yaml`, 18 comments on 20 outputs) is compared with the judge only descriptively (`judge_agreement.py --labels …`): the rubric themes came from those comments, so they cannot validate it.

**Run stability:** `scripts/run_stability.py --runs ../experiments/pilot-2026-09/outputs` reports, per condition and goal, how often repeated runs chose the same views, and the overlap of their elements and relations.

## 5. Report
For every number reported, state:
- the model and tool version per condition;
- the judge model;
- the goal set;
- the repositories and how they were prepared;
- the number of runs per goal.

**Analysis for the exploratory pilot:** pair conditions by goal (the mean over its 3 runs); report the per-goal differences in the primary outcome, their mean and a 95% bootstrap interval; report secondary outcomes descriptively (judge themes, verdicts, grounding, reflexion counts, stability, tokens and cost). With 10 goals on 2 repositories, only large differences are detectable, and nothing generalises beyond these systems. Claims about generalisation need goals and repositories that were not used during design.
