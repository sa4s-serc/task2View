"""Settings. Each can be overridden with an environment variable of the same name."""

import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent

# Jobs live outside any git repository, so the agent sees only the repository under study.
T2V_HOME = Path(os.environ.get("T2V_HOME", Path.home() / "task2view-jobs")).expanduser()
T2V_PORT = int(os.environ.get("T2V_PORT", "8642"))

# The agent: "claude" (Claude Code) or "codex" (Codex). Default models per agent: (draws, reviews).
AGENT = os.environ.get("T2V_AGENT", "claude").strip().lower()
DEFAULT_MODELS = {"claude": ("claude-sonnet-5-5", "claude-opus-5-5"),
                  "codex": ("gpt-5.6-terra", "gpt-5.6-terra")}
GENERATOR_MODEL = os.environ.get("T2V_GENERATOR_MODEL") or DEFAULT_MODELS.get(AGENT, ("", ""))[0]
CRITIC_MODEL = os.environ.get("T2V_CRITIC_MODEL") or DEFAULT_MODELS.get(AGENT, ("", ""))[1]
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
