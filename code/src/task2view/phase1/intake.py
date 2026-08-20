from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from task2view.contracts.models import (
    NormalizedRequest,
    PipelineError,
    Preferences,
    RepositoryRef,
    StakeholderRef,
    TaskRef,
    UserRequest,
)
from task2view.contracts.validate import validate_artifact
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase1.goal import parse_goal


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


def normalize_request(
    raw: UserRequest,
    *,
    knowledge: KnowledgeBase | None = None,
) -> NormalizedRequest:
    knowledge = knowledge or load_knowledge()
    role_label, task, goal = parse_goal(
        raw.goal or "",
        stakeholder=raw.stakeholder,
        knowledge=knowledge,
    )
    role_id = knowledge.resolve_role(role_label)
    profile = knowledge.stakeholder(role_id)
    repo = resolve_repository(raw.code or raw.repository or "")
    artifact = NormalizedRequest(
        request_id=raw.request_id or new_request_id(),
        repository=repo,
        stakeholder=StakeholderRef(
            role=role_id,
            original_label=role_label,
            iso_42010_class=profile.get("iso_42010_class"),
            vb_row=profile.get("vb_row") or role_id,
        ),
        task=TaskRef(description=task),
        goal=goal,
        preferences=Preferences(
            diagram_language=raw.diagram_language,
            max_views=raw.max_views,
            scope_token_budget=raw.scope_token_budget,
        ),
    )
    validate_artifact("normalized_request", artifact)
    return artifact
