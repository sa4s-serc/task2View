from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from task2view.contracts.models import PipelineError, RepositoryRef


def new_request_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"REQ-{stamp}-{uuid.uuid4().hex[:4]}"


def _git_revision(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def resolve_repository(location: str) -> RepositoryRef:
    path = Path(location).expanduser().resolve()
    if not path.exists():
        raise PipelineError(f"Repository path does not exist: {path}")
    if not path.is_dir():
        raise PipelineError(f"Repository path is not a directory: {path}")
    return RepositoryRef(name=path.name, location=str(path), revision=_git_revision(path))
