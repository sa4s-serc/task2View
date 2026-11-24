# Task2View tool

A local web tool: give it a repository and say what you need to understand; it works out what you need, asks
you only where it is unsure, then draws the UML architecture view (or views) that answer your request, each with
an explanation and the evidence in the code. You can then ask for changes, rate each view, and export everything
to share.

It runs on your machine and uses your own login to a coding agent: **Claude Code** (default) or **Codex**. It needs
no API key and stores none. Install and log in to one of them; you do not need both.

How it works inside, file by file: [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

## 1. Requirements

macOS or Linux; on Windows, use WSL (see "Windows (WSL)" below). Install these first:

| Needed | Why | Install (macOS / Ubuntu) | Check |
|---|---|---|---|
| git | get this repository, fetch GitHub repositories | preinstalled / `sudo apt install git` | `git --version` |
| Python 3.11 or newer | runs the tool | `brew install python@3.13` / `sudo apt install python3.12 python3.12-venv` | `python3 --version` |
| Claude Code **or** Codex | the agents | Claude Code: `curl -fsSL https://claude.ai/install.sh \| bash` (or `brew install --cask claude-code`). Codex: `npm install -g @openai/codex` (or `brew install codex`) | `claude --version` / `codex --version` |
| Java, Graphviz, PlantUML **from 2023 or later** | render and check the views | macOS: `brew install plantuml graphviz` (brings Java). Ubuntu: `sudo apt install graphviz default-jre`, then PlantUML as below | `plantuml -version`, `dot -V` |

**PlantUML on Ubuntu (and WSL).** Do not use `apt install plantuml`: Ubuntu 24.04 ships version 1.2020, which lays
diagrams out differently and leaves out the element data the tool's layout checks read, so those checks cannot
run. Install the current release instead:

```bash
mkdir -p ~/.local/bin
curl -L -o ~/.local/bin/plantuml.jar https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar
printf '#!/bin/sh\nexec java -jar "$HOME/.local/bin/plantuml.jar" "$@"\n' > ~/.local/bin/plantuml
chmod +x ~/.local/bin/plantuml
plantuml -version          # should print a 2023 or later version; if not, put ~/.local/bin first in PATH
```

If you installed the old package before, remove it (`sudo apt remove plantuml`) or make sure `~/.local/bin` comes
first in your `PATH`. `./check.sh` fails with "plantuml is too old" until a recent one is found.

### Windows (WSL)

The tool runs in WSL 2 (Ubuntu), not in Windows itself. Do everything inside the WSL terminal:

1. Clone the repository **inside the Linux file system** (for example `~/task2view`), not under `/mnt/c/...`.
   A checkout on the Windows drive leads to "dubious ownership" errors from git, a broken `.venv`, and scripts
   that do not run.
2. Install the requirements above with the Ubuntu commands, including PlantUML from its release.
3. Log in to Claude Code or Codex inside WSL; a login on the Windows side is not seen there.
4. Open the tool at http://127.0.0.1:8642 in your Windows browser; WSL forwards the port.
5. Exports are downloaded by the Windows browser, usually to `/mnt/c/Users/<you>/Downloads/` as seen from WSL.

If a script says "cannot execute: required file not found", it was checked out with Windows line endings: clone
again inside WSL (the repository now forces Unix line endings for its scripts).

### Choosing the agent

Claude Code is the default. To use Codex, start the tool with `T2V_AGENT=codex` (section 3). The agent and its
models are shown on the home page and recorded in every job and export, so results from the two can be told apart.

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

### Codex login

1. Run `codex login` and log in with your ChatGPT account (or an OpenAI API key, which is then billed).
   `codex login status` should say you are logged in.
2. Models: which ones you can use depends on your ChatGPT plan, so the tool uses the best one your login offers,
   in this order: **gpt-6-astra**, **gpt-6.1-sol**, **gpt-6.1-terra**, and **gpt-5.6-terra** as the fallback
   (offered also on the free plan). The best one draws; the next best reviews, so that a different model reviews
   when your plan has two. `./run.sh` prints the models chosen, and `T2V_AGENT=codex ./check.sh` tests them.
   Keep Codex up to date (`codex update`; gpt-6.1-terra needs version 0.159 or later). To choose yourself, set
   `T2V_GENERATOR_MODEL` and `T2V_CRITIC_MODEL`; `codex debug models` lists what your plan offers.
3. The tool ignores your `~/.codex/config.toml` (model, MCP servers, profiles) so that every run uses the same
   settings; only the login is used from there. A personal `~/.codex/AGENTS.md` still reaches the agents: keep it
   out of the way for comparable results. The export records whether it existed.

Differences from Claude Code that matter for results: Codex cannot be limited to a list of tools, so its
sandbox limits it instead (the drawing agent can write only inside its working copy and has no network; the
reviewing agent can only read, and the tool saves its review); and Codex reports tokens but no cost.

## 2. Install

```bash
git clone git@github.com:sa4s-serc/task2View.git
cd task2View
git checkout research-question-reframe
cd app
./setup.sh      # creates app/.venv (a Python virtual environment) and installs the tool into it
./check.sh      # checks every requirement, including the Claude Code login and both models
T2V_AGENT=codex ./check.sh      # the same, for Codex
```

`setup.sh` finds Python 3.11 or newer, creates the virtual environment `app/.venv`, and installs two packages
into it: this tool (`app/`) and the `task2view` package from `../code` (static code analysis with tree-sitter).
Nothing is installed outside `app/.venv`. Keep the folder layout of the repository: the tool needs `../code`.

You do not need to activate the virtual environment; the scripts use it directly.

## 3. Run

```bash
./run.sh                    # starts the tool with Claude Code; open http://127.0.0.1:8642 in your browser
T2V_AGENT=codex ./run.sh    # or with Codex
```

The agent is set when the tool starts and applies to every job started then; restart the tool to switch. Use the
same agent when you press "Try again" on a job, so that one job is not done by two agents.

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
   answer; the others show its value with an "Edit" button. Questions the tool added that your request does not
   ask are always shown for you to keep or remove. It may add up to two questions of its own. If it is
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
the time and tokens of every agent call; and `tool.json` (tool version, agent and its version, models,
platform). It does **not** contain the repository
itself, but the logs and views quote parts of its code, so share exports only of code you may share.

Whoever receives exports collects them into one overview:

```bash
cd app
.venv/bin/t2v-collect ~/Downloads/task2view-export-*.zip --out ~/task2view-results
open ~/task2view-results/index.html      # Linux: xdg-open
```

Give the zip files as they are named, or with an unquoted `*` pattern; check first where your browser saved them
(on WSL, usually `/mnt/c/Users/<you>/Downloads/`). This writes `index.html` (every job: agent, request, questions asked, confirmed fields, views, checks, review,
feedback, ratings, time, tokens, and cost where Claude Code estimates it), `jobs.csv` (one row per job) and `ratings.csv` (one row per rating), next to
the unpacked exports. Running it again with more zips adds them.

## 6. Troubleshooting

| Problem | What to do |
|---|---|
| `./check.sh` says FAILED with a model | Log in again (`claude`, or `codex login`); check that your plan includes that model, or set `T2V_GENERATOR_MODEL` / `T2V_CRITIC_MODEL` |
| "Claude Code stopped: ... limit" | Usage limit reached. Wait until it resets, then "Try again" |
| "Port 8642 is in use" | Another copy of the tool is running; stop it, or start with `T2V_PORT=8650 ./run.sh` |
| `plantuml cannot render` | Install Java and Graphviz (`java -version`, `dot -V`) |
| `plantuml is too old` | Install the current PlantUML (section 1); Ubuntu's package is from 2020 |
| A check shows "skipped" | The view is fine, but some layout checks could not run because PlantUML is too old; install a newer one |
| `Python 3.11 or newer is needed` | Install a newer Python (table above), then `./setup.sh` |
| An agent asks for permission or a step hangs | Agents run in Claude Code's `auto` permission mode. If your account does not offer it, set `T2V_PERMISSION_MODE=acceptEdits` |
| Codex: "model is not supported when using Codex with a ChatGPT account" | Pick a model from `codex debug models` and set `T2V_GENERATOR_MODEL` / `T2V_CRITIC_MODEL` |
| Codex: "Codex stopped: ..." | Run `codex login status`; the message after "stopped" says why (often a usage limit) |
| Something else failed | The page shows the error; details are in `~/task2view-jobs/jobs/<job>/error.txt` and `logs/` |

## 7. Settings (environment variables)

Set before `./run.sh`, for example `T2V_PORT=8650 ./run.sh`.

| Variable | Default | Meaning |
|---|---|---|
| `T2V_HOME` | `~/task2view-jobs` | where jobs are kept (must be outside any git repository) |
| `T2V_PORT` | `8642` | port of the web page |
| `T2V_AGENT` | `claude` | the agent: `claude` (Claude Code) or `codex` (Codex) |
| `T2V_GENERATOR_MODEL` | `claude-sonnet-5-5`; Codex: the best model your plan offers | model that fills in the fields, chooses and draws the views |
| `T2V_CRITIC_MODEL` | `claude-opus-5-5`; Codex: the next best (or the same) | model that reviews |
| `T2V_PERMISSION_MODE` | `auto` | Claude Code only: permission mode of the agent sessions |
| `T2V_CODEX_EFFORT` | `high` | Codex only: reasoning effort |

## 8. Safety

- The server listens on `127.0.0.1` only (not reachable from other machines) and rejects requests from other web
  pages.
- No key is handled: agents run through the `claude` or `codex` command with the login already on this machine.
- The agents work on a copy of the repository in the job folder. Existing diagrams, binaries, symbolic links and
  agent configuration shipped with the repository (`.claude/`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json`) are not
  copied. With Claude Code, the drawing agent may run only the skill's scripts and PlantUML; the reviewing agent
  may only read, and write its review file; anything else is decided by Claude Code's permission mode. With
  Codex, the drawing agent runs in Codex's `workspace-write` sandbox (writes only in its working copy, no
  network) and the reviewing agent in the `read-only` sandbox.
- Still, an agent reads the repository's files, so **use repositories you trust**.
