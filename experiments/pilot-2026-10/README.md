# Pilot, October 2026: run book

Three conditions (plain-agent, skill-agent, task2view) × 10 goals (`goals.yaml`) × 1 run, all on Claude Sonnet 4.5 through your Claude subscription. The full design is in [`../PROTOCOL.md`](../PROTOCOL.md). Do the steps in order; every step can be stopped and resumed.

## 0. Before any run
1. Sign in once: run `claude` in a terminal, type `/login`, finish in the browser, then `/exit`. Make sure `ANTHROPIC_API_KEY` is **not** set (`echo $ANTHROPIC_API_KEY` prints nothing), otherwise usage is billed to the key.
2. Optional but recommended: the expert fills `expected:` for each goal in `goals.yaml` (3–6 short facts), before anything is generated. Commit it.

## 1. Prepare the repository copies (once)
```bash
cd ~/research/CIAO_integration/Task2View/code
prep() { .venv/bin/python scripts/prepare_subject.py --src "../data/$1" --dst "$HOME/t2v-subjects/$2/$1"; }
IS=Progetto-IS-main-English; GR=progetto_ing_software_gr10-main-English
prep $IS task2view/progetto-is; prep $GR task2view/gr10
for c in IS-seat-L1 IS-seat-L2 IS-seat-L3 IS-reg-L1 IS-reg-L2 IS-reg-L3; do
  prep $IS plain-agent/$c; prep $IS skill-agent/$c; done
for c in GR10-Q1 GR10-Q2 GR10-Q3 GR10-Q4; do
  prep $GR plain-agent/$c; prep $GR skill-agent/$c; done
for d in ~/t2v-subjects/skill-agent/*/*/; do mkdir -p "$d.claude/skills" && cp -R ../skill "$d.claude/skills/task2view"; done
```
This gives one untouched copy per agent run (agents write into their folder) and one shared copy per system for the pipeline (it only reads).

## 2. Task2View (10 runs, unattended)
```bash
cd ~/research/CIAO_integration/Task2View/code
caffeinate -i .venv/bin/python scripts/run_goal_set.py --goals ../experiments/pilot-2026-10/goals.yaml \
  --out ../experiments/pilot-2026-10/outputs/task2view --llm claude-code:claude-sonnet-4-5 --notations plantuml --wait
```
- Try one goal first and look at its README and diagrams: add `--only IS-seat-L1`.
- On a usage limit it waits for the reset and continues. If you stop it (Ctrl-C) or the Mac restarts, run the same command again: finished goals are skipped, and replies already received are replayed from `outputs/task2view/.llm-cache/` without new usage.
- Don't run agent sessions at the same time; they share the subscription's limits.

## 3. Agents (20 sessions, interactive)
For each goal `<case>` and condition (`plain-agent`, `skill-agent`):
```bash
cd ~/t2v-subjects/<condition>/<case>/<repo folder>
claude --model claude-sonnet-4-5
```
Paste the condition's instruction from PROTOCOL §3.1 (plain) or §3.2 (skill), with the goal text from `goals.yaml` and run id `<case>`. Let it finish; approve writes to `./task2view-out/`.
- **Limit reached:** Claude Code shows the reset time. Leave the window, and after the reset type `continue`. If the window was closed: `cd` into the same folder, run `claude --resume`, pick the session, and type `continue`. Files already written are kept either way.
- When done, copy the outputs:
```bash
cp -R ~/t2v-subjects/<condition>/<case>/<repo folder>/task2view-out/<case> \
      ~/research/CIAO_integration/Task2View/experiments/pilot-2026-10/outputs/<condition>/<case>
```
- Add a line to `runs.csv` (Claude Code version: `claude --version`; session: the name shown by `claude --resume`).

## 4. Rate
When all 30 runs are in `outputs/`, make the blind rating sheet (PROTOCOL §4) and give the expert `rating/rating_sheet.csv` and `rating/items/`.
