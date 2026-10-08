# Task2View skill (single-agent baseline)

Give this folder to **Cursor**, **Codex**, or **ChatGPT**. One agent follows the same ISO 42010 / Views-and-Beyond method as the Task2View pipeline and writes the same artifact filenames. Use those folders to compare against `Task2View/code/runs/pagerank-ciao/`.

Phase order matches `run_agentic`: interpret the goal, choose one viewpoint from the concerns it raises, bind that viewpoint's published grain, then write questions at that grain. The agent does not retarget the viewpoint afterward.

This skill is **not** a wrapper around `task2view run`. The agent must do the eight phases itself.

## Give it to Cursor

Project skill (this comparison uses an isolated checkout so a no-skill run cannot see it):

```bash
mkdir -p /path/to/subject/.cursor/skills
cp -R skill /path/to/subject/.cursor/skills/task2view
```

Cursor loads `SKILL.md` from `.cursor/skills/<name>/`. The agent applies it when the request is an architecture view for a stakeholder goal.

## Give it to Codex

Codex loads skills from `.agents/skills/<name>/SKILL.md`.

**Option A — user skill (works for every repo)**

```bash
mkdir -p ~/.agents/skills
cp -R skill ~/.agents/skills/task2view
```

**Option B — drop it into the subject repository**

```bash
cp -R skill /path/to/Progetto-IS/.agents/skills/task2view
```

Restart Codex if `$task2view` does not appear. Invoke with `$task2view` or `/skills`.

## Run one goal

Open Codex **on the English subject repo** (`data/Progetto-IS-main-English` or `data/progetto_ing_software_gr10-main-English`), not on Task2View and not on the Italian originals.

```
$task2view

--code .
--goal "I am a software developer. I need to modify the seat booking functionality and understand the main system components involved and how they interact."
--out ./runs/single-agent/IS-seat-L1
--run-id IS-seat-L1
```

All ten goals: [references/examples.md](references/examples.md). Paste each goal **verbatim**.

## Compare with the multi-agent pipeline

| Side | How it is produced |
|---|---|
| Multi-agent | `task2view run --code … --goal … --out Task2View/code/runs/pagerank-ciao/<id>` |
| Single-agent | this skill + Codex on the same checkout and the same goal text |

Compare, per run id:

1. `viewpoint_plan.json` → same `viewpoint_id`?
2. `view_model.json` → element names (responsibility vs package folders), grounding, count
3. `architecture_view.puml` → readable diagram vs dump
4. `validation_report.json` / `structure_report.json` → gaps the other side missed

## Layout

```
skill/
  SKILL.md                 # what Codex loads
  agents/openai.yaml
  knowledge/               # same catalogs as Task2View
  references/
    quality-rules.md
    output-schema.md
    examples.md
```
