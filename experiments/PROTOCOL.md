# Experiment protocol: three conditions

How to run one goal set through the three conditions so the results can be compared. It works for any goal set and any repositories; the pilot set is `code/tests/fixtures/pilot_goals.yaml` (goal texts for agents: `skill/references/goal-sets.md`).

| Condition | Who produces the views | Instruction |
|---|---|---|
| **plain-agent** | One coding agent with the repository and the goal | §3.1 |
| **skill-agent** | The same agent and model, plus the Task2View skill (`skill/`) | §3.2 |
| **task2view** | The Task2View pipeline (ADR-006) | §3.3 |

## 1. Hold fixed across conditions
- **The same repositories:** a prepared copy of each subject (§2), one fresh copy per run.
- **The same goals:** pasted verbatim, with the same run ids.
- **The same model** wherever possible: run both agent conditions on the same model as the pipeline's `--llm` (e.g. `claude-sonnet-4-5`), and record the exact model id for every run.
- **The same notation:** PlantUML.
- **The same judge:** one judge model, different from the generator, scores all conditions afterwards (§4).
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
.venv/bin/python scripts/run_goal_set.py --goals <goal set>.yaml --out ../experiments/<name>/outputs/task2view \
  --llm <provider:model> --notations plantuml
```
In the goal-set file, `systems:` should point to the prepared copies (or use `code:` per case). Leave `--judge-llm` out here; all conditions are judged together in §4.

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

**Human review:** give reviewers the rendered diagrams with conditions anonymised, in a random order per goal. Use the seven themes of `code/src/task2view/prompts/phase8_judge.md` and the same 1–5 scale, so the judge can later be calibrated against the human scores.

## 5. Report
For every number reported, state:
- the model and tool version per condition;
- the judge model;
- the goal set;
- the repositories and how they were prepared;
- the number of runs per goal.

The pilot goals were used while designing Task2View, so results on them are a regression check. Claims about generalisation need goals and repositories that were not used during design.
