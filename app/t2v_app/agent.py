"""The coding agent that does the work: Claude Code (default) or Codex, chosen with T2V_AGENT.

Both are used the same way, through the agent's own command-line tool and its login on this machine:
  ask_json(prompt, cwd, name)        one call that only answers, for Phase 1; returns the JSON object in the reply
  session(prompt, workdir, log_file, role, output="", resume="")
                                     one agent session in workdir; returns its session id
      role "draw"    may read the repository, write in workdir, run the skill's scripts and PlantUML
      role "review"  may only read, and write its review to `output` (a path relative to workdir)

Every call adds a line to usage.jsonl next to its log: which agent and model, how long, tokens, cost if known.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from . import config

AGENTS = {"claude": "Claude Code", "codex": "Codex"}


class AgentError(RuntimeError):
    """A call failed (not installed, not logged in, usage limit, timeout, unusable reply)."""


def _backend():
    if config.AGENT == "codex":
        from . import codex
        return codex
    from . import claude
    return claude


def run(cmd: list[str], cwd: Path, timeout: int, stdout, env: dict | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, stdin=subprocess.DEVNULL,
                              stdout=stdout, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    except FileNotFoundError:
        raise AgentError(f"{AGENTS[config.AGENT]} is not installed (the `{cmd[0]}` command was not found)") from None
    except subprocess.TimeoutExpired:
        raise AgentError(f"{AGENTS[config.AGENT]} did not finish within {timeout // 60} minutes") from None


def json_in(text: str) -> dict:
    found = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(found.group(0)) if found else {}
    except ValueError:
        raise AgentError(f"The reply was not valid JSON: {text[:300]}") from None


def _record(usage_file: Path, name: str, model: str, started: float, usage: dict) -> None:
    with usage_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"call": name, "agent": config.AGENT, "model": model,
                            "seconds": round(time.monotonic() - started, 1), **usage}) + "\n")


def ask_json(prompt: str, cwd: Path, name: str) -> dict:
    """The prompt and reply are kept in cwd/<name>.json."""
    cwd.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    text, usage = _backend().ask(prompt, config.GENERATOR_MODEL, cwd)
    _record(cwd / "usage.jsonl", name, config.GENERATOR_MODEL, started, usage)
    (cwd / f"{name}.json").write_text(json.dumps({"agent": config.AGENT, "model": config.GENERATOR_MODEL,
                                                  "prompt": prompt, "reply": text}, indent=2), encoding="utf-8")
    return json_in(text)


def session(prompt: str, workdir: Path, log_file: Path, role: str, output: str = "", resume: str = "") -> str:
    model = config.CRITIC_MODEL if role == "review" else config.GENERATOR_MODEL
    log_file.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    session_id, usage = _backend().session(prompt, workdir, log_file, model, role, output, resume)
    _record(log_file.parent / "usage.jsonl", log_file.stem, model, started, usage)
    return session_id
