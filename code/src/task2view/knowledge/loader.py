from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

import yaml

from task2view.contracts.models import PipelineError

DATA = files("task2view.knowledge.data")


def _load_yaml(name: str) -> dict[str, Any]:
    text = DATA.joinpath(name).read_text(encoding="utf-8")
    return yaml.safe_load(text)


@dataclass(frozen=True)
class KnowledgeBase:
    aliases: dict[str, str]
    vb_table: dict[str, Any]
    stakeholders: dict[str, dict[str, Any]]
    viewpoints: dict[str, dict[str, Any]]
    task_cues: list[dict[str, Any]]
    notations: dict[str, Any]
    required_information: dict[str, list[dict[str, str]]]
    corpus_rules: dict[str, Any]

    def resolve_role(self, raw: str) -> str:
        key = " ".join(raw.strip().lower().replace("_", " ").replace("/", " ").split())
        hyphen = key.replace(" ", "-")
        if hyphen in self.stakeholders:
            return hyphen
        if hyphen in self.aliases:
            return self.aliases[hyphen]
        if key in self.aliases:
            return self.aliases[key]
        raise PipelineError(
            f"Unknown stakeholder role {raw!r}. "
            f"Known roles: {sorted(self.stakeholders)} / aliases: {sorted(self.aliases)}"
        )

    def stakeholder(self, role_id: str) -> dict[str, Any]:
        try:
            return self.stakeholders[role_id]
        except KeyError as exc:
            raise PipelineError(f"No profile for stakeholder {role_id!r}") from exc

    def viewpoint(self, viewpoint_id: str) -> dict[str, Any]:
        try:
            return self.viewpoints[viewpoint_id]
        except KeyError as exc:
            raise PipelineError(f"Unknown viewpoint {viewpoint_id!r}") from exc

    def notation_supports(self, language: str, view_type: str) -> bool:
        spec = self.notations.get("languages", {}).get(language)
        if not spec:
            return False
        return view_type in spec.get("view_types", [])

    def choose_language(
        self,
        view_type: str,
        *,
        preferred: str | None,
        formality: str,
    ) -> str:
        if preferred:
            if preferred not in self.notations.get("languages", {}):
                raise PipelineError(f"Unknown diagram_language {preferred!r}")
            if not self.notation_supports(preferred, view_type):
                raise PipelineError(
                    f"{preferred} does not declare support for view_type {view_type}"
                )
            return preferred
        order = self.notations.get("preference_order", {}).get(formality, [])
        for language in order:
            if self.notation_supports(language, view_type):
                return language
        for language in self.notations.get("languages", {}):
            if self.notation_supports(language, view_type):
                return language
        raise PipelineError(f"No registered notation supports {view_type}")


@lru_cache(maxsize=1)
def load_knowledge() -> KnowledgeBase:
    aliases_doc = _load_yaml("aliases.yaml")
    stakeholders_doc = _load_yaml("stakeholders.yaml")
    viewpoints_doc = _load_yaml("viewpoints.yaml")
    cues_doc = _load_yaml("task_cues.yaml")
    ri_doc = _load_yaml("required_information.yaml")
    stakeholders = {row["id"]: row for row in stakeholders_doc["stakeholders"]}
    viewpoints = {row["id"]: row for row in viewpoints_doc["viewpoints"]}
    return KnowledgeBase(
        aliases=aliases_doc["aliases"],
        vb_table=_load_yaml("vb_table_9_1.yaml"),
        stakeholders=stakeholders,
        viewpoints=viewpoints,
        task_cues=cues_doc["cues"],
        notations=_load_yaml("notations.yaml"),
        required_information=ri_doc["templates"],
        corpus_rules=_load_yaml("corpus.yaml"),
    )
