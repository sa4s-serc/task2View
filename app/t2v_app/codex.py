"""Codex as the agent (T2V_AGENT=codex). Uses the Codex login of this machine; no key is handled.

Codex cannot be limited to a list of tools as Claude Code can; its sandbox does the limiting instead:
  draw    sandbox "workspace-write": writes only inside the working copy, no network
  review  sandbox "read-only": the review is given as the final reply and written to its file by this module
Settings in ~/.codex/config.toml are ignored (--ignore-user-config), so every run uses the same settings;
the login is still read from there.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import config
from .agent import AgentError, json_in, run

REVIEW_NOTE = ("\n\nThis session can only read files. Do not try to write the review file: give the review as "
               "your final reply, as the JSON object only; it is saved to that file for you.")


def _flags(model: str, sandbox: str) -> list[str]:
    return ["--json", "--skip-git-repo-check", "--ignore-user-config", "-m", model,
            "-c", f'model_reasoning_effort="{config.CODEX_EFFORT}"', "-c", 'approval_policy="never"',
            "-c", f'sandbox_mode="{sandbox}"']


def _read(lines: list[str]) -> tuple[str, str, dict]:
    """Session id, last agent message and token usage from Codex's JSON events; raises if the turn failed."""
    session_id, text, problem, done = "", "", "", False
    usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": None}
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind, item = event.get("type"), event.get("item") or {}
        if kind == "thread.started":
            session_id = event.get("thread_id", "")
        elif kind == "item.completed" and item.get("type") == "agent_message":
            text = item.get("text") or ""
        elif kind == "turn.completed":
            done = True
            u = event.get("usage") or {}
            usage["input_tokens"] += u.get("input_tokens") or 0
            usage["output_tokens"] += (u.get("output_tokens") or 0) + (u.get("reasoning_output_tokens") or 0)
        elif kind in ("turn.failed", "error"):
            error = event.get("error") or event
            problem = str(error.get("message") if isinstance(error, dict) else error)
    if not done:
        raise AgentError(f"Codex stopped: {problem[:300] or 'no reply'}")
    return session_id, text, usage


def ask(prompt: str, model: str, cwd: Path) -> tuple[str, dict]:
    done = run(["codex", "exec", *_flags(model, "read-only"), "--ephemeral", prompt], cwd, config.QUESTION_TIMEOUT,
               subprocess.PIPE)
    _, text, usage = _read(done.stdout.splitlines())
    return text, usage


def session(prompt: str, workdir: Path, log_file: Path, model: str, role: str, output: str,
            resume: str) -> tuple[str, dict]:
    sandbox = "read-only" if role == "review" else "workspace-write"
    prompt = prompt + REVIEW_NOTE if role == "review" else prompt
    cmd = ["codex", "exec", "resume", *_flags(model, sandbox), resume, prompt] if resume \
        else ["codex", "exec", *_flags(model, sandbox), prompt]
    with log_file.open("w", encoding="utf-8") as stream:
        run(cmd, workdir, config.SESSION_TIMEOUT, stream)
    session_id, text, usage = _read(log_file.read_text(encoding="utf-8", errors="replace").splitlines())
    if role == "review":
        review = json_in(text)
        if review:
            (workdir / output).write_text(json.dumps(review, indent=2), encoding="utf-8")
    return session_id or resume, usage
