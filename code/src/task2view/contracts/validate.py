from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

import jsonschema
from pydantic import BaseModel

from task2view.contracts.models import PipelineError

SCHEMA_NAMES = {
    "normalized_request": "normalized_request.json",
    "view_specification": "view_specification.json",
    "cleaned_corpus": "cleaned_corpus.json",
}


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    filename = SCHEMA_NAMES[name]
    raw = files("task2view.contracts.schemas").joinpath(filename).read_text(encoding="utf-8")
    return json.loads(raw)


def artifact_to_dict(artifact: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(artifact, BaseModel):
        return artifact.model_dump(mode="json", by_alias=True, exclude_none=False)
    return artifact


def validate_artifact(name: str, artifact: BaseModel | dict[str, Any]) -> dict[str, Any]:
    payload = artifact_to_dict(artifact)
    try:
        jsonschema.validate(payload, load_schema(name))
    except jsonschema.ValidationError as exc:
        raise PipelineError(f"{name} failed schema validation: {exc.message}") from exc
    return payload
