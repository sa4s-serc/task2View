"""Settings. Each can be overridden with an environment variable of the same name."""

import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent

# Jobs live outside any git repository, so the agent sees only the repository under study.
T2V_HOME = Path(os.environ.get("T2V_HOME", Path.home() / "task2view-jobs")).expanduser()
T2V_PORT = int(os.environ.get("T2V_PORT", "8642"))

GENERATOR_MODEL = os.environ.get("T2V_GENERATOR_MODEL", "claude-sonnet-5-5")
CRITIC_MODEL = os.environ.get("T2V_CRITIC_MODEL", "claude-opus-5-5")
PERMISSION_MODE = os.environ.get("T2V_PERMISSION_MODE", "auto")

MAX_EXTRA_QUESTIONS = 2
MAX_FEEDBACK_CHARS = 4000          # on top of the five fixed questions
DETAIL_LEVELS = ("overview", "balanced", "detailed")
DEFAULT_DETAIL_LEVEL = "balanced"

MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_UNPACKED_BYTES = 1024 * 1024 * 1024
MAX_FILES = 20_000

QUESTION_TIMEOUT = 10 * 60       # seconds, one call without tools
SESSION_TIMEOUT = 45 * 60        # seconds, one agent session
CLONE_TIMEOUT = 5 * 60
