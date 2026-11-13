"""Headless Claude Code calls. The tool uses the Claude Code login of this machine and never handles a key."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from . import config

ENV = {**os.environ, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}


class ClaudeError(RuntimeError):
    """A call failed (not installed, not logged in, usage limit, timeout, unusable reply)."""


def _run(cmd: list[str], cwd: Path, timeout: int, stdout) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, env=ENV, stdin=subprocess.DEVNULL, stdout=stdout,
                              stderr=subprocess.STDOUT, text=True, timeout=timeout)
    except FileNotFoundError:
        raise ClaudeError("Claude Code is not installed (the `claude` command was not found)") from None
    except subprocess.TimeoutExpired:
        raise ClaudeError(f"Claude Code did not finish within {timeout // 60} minutes") from None


def ask_json(prompt: str, model: str, cwd: Path) -> dict:
    """One call with no tools; returns the JSON object in the reply."""
    cwd.mkdir(parents=True, exist_ok=True)
    run = _run(["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", ""],
               cwd, config.QUESTION_TIMEOUT, subprocess.PIPE)
    try:
        reply = json.loads(run.stdout)
    except ValueError:
        raise ClaudeError(f"Claude Code failed: {run.stdout.strip()[:300]}") from None
    text = reply.get("result") or ""
    if reply.get("is_error") or reply.get("api_error_status"):
        raise ClaudeError(f"Claude Code reported an error: {text[:300]}")
    found = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(found.group(0)) if found else {}
    except ValueError:
        raise ClaudeError(f"The reply was not valid JSON: {text[:300]}") from None


def session(prompt: str, workdir: Path, log_file: Path, model: str, tools: list[str], resume: str = "") -> str:
    """One agent session in workdir, limited to the given tools; returns the session id."""
    cmd = ["claude", "-p", prompt, "--model", model, "--permission-mode", config.PERMISSION_MODE,
           "--output-format", "stream-json", "--verbose", "--allowedTools", *tools]
    if resume:
        cmd += ["--resume", resume]
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w", encoding="utf-8") as stream:
        _run(cmd, workdir, config.SESSION_TIMEOUT, stream)
    session_id = ""
    for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        session_id = session_id or event.get("session_id", "")
        if event.get("type") == "result" and (event.get("api_error_status") or event.get("is_error")):
            raise ClaudeError(f"Claude Code stopped: {str(event.get('result'))[:300]}")
    if not session_id:
        raise ClaudeError(f"Claude Code did not start; see {log_file.name}")
    return session_id
