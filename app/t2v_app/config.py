"""Settings. Each can be overridden with an environment variable of the same name."""

import json
import os
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent

# Jobs live outside any git repository, so the agent sees only the repository under study.
T2V_HOME = Path(os.environ.get("T2V_HOME", Path.home() / "task2view-jobs")).expanduser()
T2V_PORT = int(os.environ.get("T2V_PORT", "8642"))

# The agent: "claude" (Claude Code) or "codex" (Codex).
AGENT = os.environ.get("T2V_AGENT", "claude").strip().lower()

# Codex: the models a ChatGPT plan offers differ, so the best one this login offers is used, in this order
# (Codex documentation, models page, 2026-11). The last one is the fallback, offered also on the free plan.
CODEX_MODELS = ("gpt-6-astra", "gpt-6.1-sol", "gpt-6.1-terra", "gpt-5.6-terra")


def _codex_offered() -> list[str]:
    """The models of CODEX_MODELS that this machine's Codex login offers, best first."""
    try:
        catalog = json.loads(subprocess.run(["codex", "debug", "models"], capture_output=True, text=True,
                                            timeout=60).stdout)
        slugs = {m.get("slug") for m in catalog.get("models", [])}
    except (OSError, ValueError, subprocess.TimeoutExpired, AttributeError):
        slugs = set()
    return [m for m in CODEX_MODELS if m in slugs] or [CODEX_MODELS[-1]]


def _default_models() -> tuple[str, str]:
    """(draws, reviews). Claude Code: Sonnet draws, Opus reviews. Codex: the best offered model draws; the next
    best reviews, so that a different model reviews when the plan has two, otherwise the same one."""
    if AGENT != "codex":
        return "claude-sonnet-5-5", "claude-opus-5-5"
    if os.environ.get("T2V_GENERATOR_MODEL") and os.environ.get("T2V_CRITIC_MODEL"):
        return "", ""
    offered = _codex_offered()
    return offered[0], (offered[1:] or offered)[0]


_DRAWS, _REVIEWS = _default_models()
GENERATOR_MODEL = os.environ.get("T2V_GENERATOR_MODEL") or _DRAWS
CRITIC_MODEL = os.environ.get("T2V_CRITIC_MODEL") or _REVIEWS
PERMISSION_MODE = os.environ.get("T2V_PERMISSION_MODE", "auto")     # Claude Code only
CODEX_EFFORT = os.environ.get("T2V_CODEX_EFFORT", "high")           # Codex only: reasoning effort

MAX_EXTRA_QUESTIONS = 2
MAX_FEEDBACK_CHARS = 4000          # on top of the five fixed questions
DETAIL_LEVELS = ("overview", "balanced", "detailed")
DEFAULT_DETAIL_LEVEL = "balanced"

MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_UNPACKED_BYTES = 1024 * 1024 * 1024
MAX_FILES = 20_000

QUESTION_TIMEOUT = 10 * 60       # seconds, one Phase 1 call
SESSION_TIMEOUT = 45 * 60        # seconds, one agent session
CLONE_TIMEOUT = 5 * 60
