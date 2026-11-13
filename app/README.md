# Task2View tool

A local web tool: give it a repository and say what you need to understand; it works out what you need, asks
you only where it is unsure, then draws the UML architecture view (or views) that answer your request, each with
an explanation and the evidence in the code. You can then ask for changes, rate each view, and export everything
to share.

It runs on your machine and uses your own Claude Code login. It needs no API key and stores none.

How it works inside, file by file: [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

## 1. Requirements

macOS or Linux (on Windows, use WSL). Install these first:

| Needed | Why | Install (macOS / Ubuntu) | Check |
|---|---|---|---|
| git | get this repository, fetch GitHub repositories | preinstalled / `sudo apt install git` | `git --version` |
| Python 3.11 or newer | runs the tool | `brew install python@3.13` / `sudo apt install python3.12 python3.12-venv` | `python3 --version` |
| Claude Code | the agents | `curl -fsSL https://claude.ai/install.sh \| bash` (or `brew install --cask claude-code`) | `claude --version` |
| Java, Graphviz, PlantUML | render the views | `brew install plantuml graphviz` (brings Java) / `sudo apt install plantuml graphviz default-jre` | `plantuml -version`, `dot -V` |

### Claude Code login

The tool calls the `claude` command, so Claude Code must be logged in on this machine:

1. Run `claude` in a terminal.
2. Choose how to log in: a Claude subscription (Pro, Max, Team or Enterprise) or an Anthropic Console account.
   A browser window opens; log in there. Then leave Claude Code with `/exit`.
3. The tool uses two models: **Claude Sonnet 5.5** draws, **Claude Opus 5.5** reviews. Your plan must include
   both. `./check.sh` (below) tests this. If Opus is not available to you, set `T2V_CRITIC_MODEL=claude-sonnet-5-5`
   before `./run.sh` and tell the person you share results with (the export records the models used).

Every view takes about 5 to 10 minutes of agent work and counts against your Claude usage (on a subscription,
your usage limits; on a Console account, it is billed). One view uses roughly as much as a long Claude Code
session. If a limit is reached, the job stops with the message and can be continued later with "Try again".

Your personal Claude Code setup also reaches the agents: a `~/.claude/CLAUDE.md`, user-level skills, hooks or
MCP servers. For results that can be compared with other people's, keep them out of the way while you use the
tool (for example rename `~/.claude/CLAUDE.md` for the time being). The export records whether that file existed.

## 2. Install

```bash
git clone git@github.com:sa4s-serc/task2View.git
cd task2View
git checkout research-question-reframe
cd app
./setup.sh      # creates app/.venv (a Python virtual environment) and installs the tool into it
./check.sh      # checks every requirement, including the Claude Code login and both models
```

`setup.sh` finds Python 3.11 or newer, creates the virtual environment `app/.venv`, and installs two packages
into it: this tool (`app/`) and the `task2view` package from `../code` (static code analysis with tree-sitter).
Nothing is installed outside `app/.venv`. Keep the folder layout of the repository: the tool needs `../code`.

You do not need to activate the virtual environment; the scripts use it directly.

## 3. Run

```bash
./run.sh        # starts the tool; open http://127.0.0.1:8642 in your browser
```

Stop it with Ctrl+C. Jobs are kept in `~/task2view-jobs` and are still there next time. If the tool was stopped
while a view was being drawn, that job shows "failed"; "Try again" continues it and keeps finished views.

To update later: `git pull`, then `./setup.sh` again.

## 4. Use

1. **Request.** Write what you need in your own words (who you are, what you are about to do, what you want to
   understand) and give the repository: a zip, or the URL of a public GitHub repository
   (`https://github.com/<owner>/<repository>`). Code analysis covers Java, Python, JavaScript and TypeScript.
2. **Confirm.** The tool fills in every ISO/IEC/IEEE 42010:2022 field itself: the system, the part of the system
   in focus, your role, what you will use the view for, the questions the view should answer (with the aspect of
   each), and the detail level. One page shows them. Fields it is unsure of are highlighted and open for your
   answer; the others show its value with an "Edit" button. It may add up to two questions of its own. If it is
   sure of everything, this page is skipped and drawing starts at once. This is the only round of questions.
3. **Drawing.** After you confirm, the tool chooses the views (viewpoint and model kind; a second view only when
   your questions need a different viewpoint) and draws them one after the other. The page shows each view's
   fields and the step it is at. A finished view can be opened while the next one is drawn. You can close the
   page and come back.
4. **Result.** Each view shows the diagram and a one-line takeaway. The full explanation, the 42010 inputs, and
   the checks with the independent review open on click.
5. **Change.** "Anything to change?" under the result takes feedback on a view, including what you know that the
   code does not show. The view is revised, reviewed and checked again (about 5 minutes). What the code does not
   confirm is drawn but marked "(unconfirmed)" and listed under Assumptions as stated by you. Any number of rounds.
6. **Rate.** Under each view, rate it from 1 (poor) to 5 (very good) on four criteria (answers the concern, right
   level of detail, correct for the code and correct UML, easy to read) and add a comment. If you change the view
   afterwards, the page asks you to rate it again; every rating is kept.
7. **Export.** "Export for sharing" downloads `task2view-export-<job>.zip` (see below). "Download everything"
   gives only the views and their READMEs, for your own use.

## 5. Sharing results

For each request you want to share: open it, make sure every view is rated, click **Export for sharing**, and
send the zip (by email or a shared drive).

The export contains: your request; what the tool filled in, asked, and what you answered; the views
(`view.png`, `view.puml`, `inventory.json`, `README.md`, earlier versions); checks and reviews; your feedback and
ratings; a timeline of the steps; the prompts and replies of the agents and their full logs (each tool call);
and `tool.json` (tool version, models, Claude Code version, platform). It does **not** contain the repository
itself, but the logs and views quote parts of its code, so share exports only of code you may share.

Whoever receives exports collects them into one overview:

```bash
cd app
.venv/bin/t2v-collect ~/Downloads/task2view-export-*.zip --out ~/task2view-results
open ~/task2view-results/index.html      # Linux: xdg-open
```

This writes `index.html` (every job: request, questions asked, confirmed fields, views, checks, review, feedback,
ratings, time and estimated cost), `jobs.csv` (one row per job) and `ratings.csv` (one row per rating), next to
the unpacked exports. Running it again with more zips adds them.

## 6. Troubleshooting

| Problem | What to do |
|---|---|
| `./check.sh` says Claude Code FAILED with a model | Run `claude` and log in again; check that your plan includes that model, or set `T2V_GENERATOR_MODEL` / `T2V_CRITIC_MODEL` |
| "Claude Code stopped: ... limit" | Usage limit reached. Wait until it resets, then "Try again" |
| "Port 8642 is in use" | Another copy of the tool is running; stop it, or start with `T2V_PORT=8650 ./run.sh` |
| `plantuml cannot render` | Install Java and Graphviz (`java -version`, `dot -V`) |
| `Python 3.11 or newer is needed` | Install a newer Python (table above), then `./setup.sh` |
| An agent asks for permission or a step hangs | Agents run in Claude Code's `auto` permission mode. If your account does not offer it, set `T2V_PERMISSION_MODE=acceptEdits` |
| Something else failed | The page shows the error; details are in `~/task2view-jobs/jobs/<job>/error.txt` and `logs/` |

## 7. Settings (environment variables)

Set before `./run.sh`, for example `T2V_PORT=8650 ./run.sh`.

| Variable | Default | Meaning |
|---|---|---|
| `T2V_HOME` | `~/task2view-jobs` | where jobs are kept (must be outside any git repository) |
| `T2V_PORT` | `8642` | port of the web page |
| `T2V_GENERATOR_MODEL` | `claude-sonnet-5-5` | model that fills in the fields, chooses and draws the views |
| `T2V_CRITIC_MODEL` | `claude-opus-5-5` | model that reviews |
| `T2V_PERMISSION_MODE` | `auto` | Claude Code permission mode of the agent sessions |

## 8. Safety

- The server listens on `127.0.0.1` only (not reachable from other machines) and rejects requests from other web
  pages.
- No key is handled: agents run through the `claude` command with the login already on this machine.
- The agents work on a copy of the repository in the job folder. Existing diagrams, binaries, symbolic links and
  agent configuration shipped with the repository (`.claude/`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json`) are not
  copied. The drawing agent may run only the skill's scripts and PlantUML; the reviewing agent may only read,
  and write its review file. Anything else is decided by Claude Code's permission mode.
- Still, an agent reads the repository's files, so **use repositories you trust**.
