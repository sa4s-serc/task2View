# Task2View skill (single-agent method)

This folder teaches one coding agent (Codex, Cursor, Claude Code, …) to carry out the Task2View method by hand. The phases, rules, catalogs and output files are the same as the Task2View pipeline (ADR-006). In experiments it is the **agent + skill** condition. The experiment protocol is in [`../experiments/PROTOCOL.md`](../experiments/PROTOCOL.md).

| File | What it is |
|---|---|
| `SKILL.md` | The workflow the agent follows (Phase 0 → 8) |
| `references/catalogs.md` | Needs, viewpoints, roles with priors, signals, constraints. **Generated** |
| `references/selection.md` | The deterministic viewpoint selection, step by step |
| `references/evidence.md` | Claims, citation checks, and how the evidence model is built |
| `references/views.md` | Projection rules, UML drawing rules, Phase 6 decisions, Phase 8 checks |
| `references/output-schema.md` | Every output file and its fields |
| `references/goal-sets.md` | Goal texts used in experiments (no expected answers). **Generated** |
| `knowledge/*.yaml` | Copies of the pipeline's catalog files. **Generated** |
| `agents/openai.yaml` | Codex agent metadata |

Generated files come from `code/scripts/sync_skill.py`. Run it after any change to `code/src/task2view/knowledge/data/vb/`. The test `code/tests/test_skill_sync.py` fails when the skill is stale.

```bash
cd ../code
.venv/bin/python scripts/sync_skill.py
```

## Install

The skill must be visible to the agent in the **agent + skill** condition and invisible in the **plain agent** condition. Install it per run, in a separate copy of the subject repository.

**Codex** (loads `.agents/skills/<name>/SKILL.md`):
```bash
mkdir -p /path/to/subject-copy/.agents/skills
cp -R skill /path/to/subject-copy/.agents/skills/task2view
```

**Cursor** (loads `.cursor/skills/<name>/SKILL.md`):
```bash
mkdir -p /path/to/subject-copy/.cursor/skills
cp -R skill /path/to/subject-copy/.cursor/skills/task2view
```

**Claude Code** (loads `.claude/skills/<name>/SKILL.md`):
```bash
mkdir -p /path/to/subject-copy/.claude/skills
cp -R skill /path/to/subject-copy/.claude/skills/task2view
```

## Run one goal
Open the agent **on the subject copy**, not on Task2View, and send the instruction from the protocol (it invokes the skill and passes the goal verbatim):

```text
Use the task2view skill.
--code .
--goal "<goal text, verbatim from references/goal-sets.md>"
--out ./task2view-out/<run-id>
--run-id <run-id>
```

## Compare with the pipeline
The pipeline writes the same files:
```bash
task2view run --code <subject> --goal "<same goal>" --out <dir>
```
So the conditions can be compared directly:

| Compare | How |
|---|---|
| Views chosen | `view_plan.json` → `views[].viewpoint_id` |
| Needs typed | `stakeholder_profile.json` → `needs` |
| Grounding | `evidence_model.json` → verified vs `rejected_claims` |
| Diagram content | `V*/view.json` → `elements`, `relations`, `interactions` |
| Quality checks | `validation_report.json` → verdicts and constraint findings |

Task fit is scored afterwards for all conditions with the same judge model.
