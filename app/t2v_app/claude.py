"""Claude Code as the agent (T2V_AGENT=claude). Uses the Claude Code login of this machine; no key is handled."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import config
from .agent import AgentError, run

ENV = {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
DRAW_TOOLS = ["Bash(python3 -I .claude/skills/*)", "Bash(python3 .claude/skills/*)", "Bash(.claude/skills/*)",
              "Bash(plantuml *)"]


def _usage(result: dict) -> dict:
    u = result.get("usage") or {}
    return {"input_tokens": sum(u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens",
                                                         "cache_creation_input_tokens")),
            "output_tokens": u.get("output_tokens") or 0, "cost_usd": result.get("total_cost_usd")}


def ask(prompt: str, model: str, cwd: Path) -> tuple[str, dict]:
    done = run(["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", ""],
               cwd, config.QUESTION_TIMEOUT, subprocess.PIPE, ENV)
    try:
        reply = json.loads(done.stdout)
    except ValueError:
        raise AgentError(f"Claude Code failed: {done.stdout.strip()[:300]}") from None
    text = reply.get("result") or ""
    if reply.get("is_error") or reply.get("api_error_status"):
        raise AgentError(f"Claude Code reported an error: {text[:300]}")
    return text, _usage(reply)


def session(prompt: str, workdir: Path, log_file: Path, model: str, role: str, output: str,
            resume: str) -> tuple[str, dict]:
    tools = ["Read", "Grep", "Glob", f"Write({output})"] if role == "review" else DRAW_TOOLS
    cmd = ["claude", "-p", prompt, "--model", model, "--permission-mode", config.PERMISSION_MODE,
           "--output-format", "stream-json", "--verbose", "--allowedTools", *tools]
    if resume:
        cmd += ["--resume", resume]
    with log_file.open("w", encoding="utf-8") as stream:
        run(cmd, workdir, config.SESSION_TIMEOUT, stream, ENV)
    session_id, usage = "", {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        session_id = session_id or event.get("session_id", "")
        if event.get("type") == "result":
            if event.get("api_error_status") or event.get("is_error"):
                raise AgentError(f"Claude Code stopped: {str(event.get('result'))[:300]}")
            got = _usage(event)
            usage = {k: (usage[k] or 0) + (got[k] or 0) for k in usage}
    if not session_id:
        raise AgentError(f"Claude Code did not start; see {log_file.name}")
    return session_id, usage
