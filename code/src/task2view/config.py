"""Run-profile YAML: swap scoper / extractor / notation without code changes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from task2view.contracts.models import PipelineError, UserRequest


def load_pipeline_config(path: str | Path) -> dict[str, Any]:
    file = Path(path)
    if not file.is_file():
        raise PipelineError(f"pipeline config not found: {file}")
    data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise PipelineError(f"pipeline config must be a mapping: {file}")
    return data


def apply_pipeline_config(raw: UserRequest, data: dict[str, Any] | None) -> UserRequest:
    """Fill unset plugin fields from YAML. Values already on ``raw`` win."""
    if not data:
        return raw
    defaults = UserRequest.model_fields
    if not raw.scope_strategy:
        raw.scope_strategy = str(data.get("scoper") or data.get("scope_strategy") or "") or None
    if not raw.extract_backend:
        raw.extract_backend = str(data.get("extractor") or data.get("extract_backend") or "") or None
    if not raw.diagram_language:
        raw.diagram_language = data.get("diagram_language") or data.get("notation")
    if data.get("skip_critic"):
        raw.skip_critic = True
    if "samples" in data and raw.samples == defaults["samples"].default:
        raw.samples = int(data["samples"])
    return raw
