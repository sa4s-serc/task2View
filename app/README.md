# Task2View tool

A local web tool: give it a repository and say what you need to understand; it asks you to confirm how it
understood you, then draws the UML architecture view (or views) that answer your request, each with a README
and the evidence in the code.

It runs on your machine and uses your own Claude Code login. It needs no API key and stores none.

## Requirements

| Needed | Why | Check |
|---|---|---|
| Python 3.11 or newer | runs the tool | `python3 --version` |
| Claude Code, installed and logged in | the agents | `claude --version`, then run `claude` once and log in |
| Java, Graphviz, PlantUML | render the views | `java -version`, `dot -V`, `plantuml -version` |
| git | fetch GitHub repositories | `git --version` |

On macOS: `brew install plantuml graphviz` (PlantUML brings Java). On Ubuntu: `sudo apt install plantuml graphviz`.

The models used are Claude Sonnet 5.5 (drawing) and Claude Opus 5.5 (review); your Claude plan must include them.
A view takes about 5 to 10 minutes and counts against your Claude Code usage.

## Run

```bash
./setup.sh      # once: creates .venv and installs the tool and ../code
./run.sh        # starts the tool at http://127.0.0.1:8642
```

Keep the folder layout of the repository: the tool uses the `task2view` package in `../code`.

## Use

1. **Request.** Write what you need in your own words and give the repository: a zip, or the URL of a public
   GitHub repository (`https://github.com/<owner>/<repository>`).
2. **Confirm.** One page shows how the request was understood, in the terms of ISO/IEC/IEEE 42010:2022: the
   system, your role, what you will use the view for, the questions the view should answer (with what you need
   to see for each), and the detail level. Correct what is wrong. The tool may add up to two questions of its
   own when something else is unclear, and there is a box for anything else you want to say. This is the only
   round of questions.
3. **Result.** The views are chosen (one viewpoint per view; a second view only when your questions need a
   different viewpoint) and drawn one after the other. For each view you get the diagram, a README that says how
   it answers your questions, the checks that ran, and an independent review. "Download everything" gives a zip
   with a top-level `README.md`, `inputs.yaml` (the 42010 inputs) and one folder per view (`view.puml`,
   `view.png`, `inventory.json`, `README.md`).

If a step fails (for example a usage limit), the page shows why; "Try again" continues and keeps finished views.

## What happens inside

| Step | Who | What |
|---|---|---|
| Prepare | program | copy the repository, build a static dependency graph (tree-sitter) |
| Pre-fill | agent, no tools | answer the five fixed questions from the request; at most two extra questions |
| Confirm | you | one page, one round |
| Propose | agent, no tools | fewest views that cover your questions, from six viewpoints (`t2v_app/data/viewpoints.yaml`) |
| Draw | agent with the `uml-view` skill | find the code, list elements with evidence, draw PlantUML |
| Check | scripts | evidence exists, arrows are in the graph, notation and readability, same names across views |
| Review | second agent, other model | are the questions answered, is the detail level right, is it supported by the code |
| Revise | first agent | once, if the review asks; the better-scored version is kept |

The dependency graph covers Java, Python, JavaScript and TypeScript. Other languages still get a view, but its
relations are not checked against a graph.

## Safety

- The server listens on `127.0.0.1` only and rejects requests from other web pages.
- No key is handled: agents run through the `claude` command with the login already on this machine.
- The agents work on a copy of the repository in the job folder. Existing diagrams, binaries, symbolic links and
  agent configuration shipped with the repository (`.claude/`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json`) are not
  copied. The drawing agent may run only the skill's scripts and PlantUML; the reviewing agent may only read,
  and write its review file. Anything else is decided by Claude Code's `auto` permission mode.
- Still, an agent reads the repository's files, so **use repositories you trust**.

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `T2V_HOME` | `~/task2view-jobs` | where jobs are kept (must be outside any git repository) |
| `T2V_PORT` | `8642` | port of the web page |
| `T2V_GENERATOR_MODEL` | `claude-sonnet-5-5` | model that draws |
| `T2V_CRITIC_MODEL` | `claude-opus-5-5` | model that reviews |
| `T2V_PERMISSION_MODE` | `auto` | Claude Code permission mode of the agent sessions |

## Layout

```
t2v_app/
  server.py     web pages
  pipeline.py   a job and its two background stages
  repo.py       zip / GitHub, the working copy, the static graph
  phase1.py     pre-fill, answers, proposed views, 42010 records
  phase2.py     draw, check, review, revise for one view
  report.py     the result README and zip
  claude.py     headless Claude Code calls
  prompts/  data/  skills/  templates/  static/
```

Each job is a folder in `T2V_HOME/jobs/`: `job.json` (state), `repo/` (the copy), `out/` (the result),
`logs/` (the agents' event streams), `work/` (one working copy per view).
