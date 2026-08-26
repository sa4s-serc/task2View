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
    architectural_styles: dict[str, Any]
    view_projection: dict[str, Any]

    def keep_without_graph(self) -> frozenset[str]:
        raw = self.view_projection.get("keep_without_graph") or []
        return frozenset(str(x) for x in raw)

    def edge_insertion_mode(self, view_type: str) -> str:
        modes = self.view_projection.get("edge_insertion") or {}
        return str(modes.get(view_type) or modes.get("default") or "inter_group")

    def published_grain(
        self,
        viewpoint_id: str | None = None,
        view_type: str | None = None,
    ) -> dict[str, Any]:
        grains = self.view_projection.get("published_grain") or {}
        if viewpoint_id and viewpoint_id in grains:
            return dict(grains[viewpoint_id] or {})
        if view_type and view_type in grains:
            return dict(grains[view_type] or {})
        return dict(grains.get("default") or {})

    def grain_prompt(self, viewpoint_id: str | None, view_type: str | None) -> str:
        grain = self.published_grain(viewpoint_id, view_type)
        label = viewpoint_id or view_type or "default"
        return (
            f"VIEWPOINT GRAIN ({label}), unit={grain.get('unit')}:\n"
            f"- nodes: {grain.get('nodes')}\n"
            f"- relations: {grain.get('relations')}\n"
            f"- do not: {grain.get('forbid')}"
        )

    def view_unit(self, view_type: str, viewpoint_id: str | None = None) -> str:
        grain = self.published_grain(viewpoint_id, view_type)
        if grain.get("unit"):
            return str(grain["unit"])
        units = self.view_projection.get("view_unit") or {}
        return str(units.get(view_type) or units.get("default") or "component")

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

    def catalog_concerns(self) -> set[str]:
        ids: set[str] = set()
        for row in self.stakeholders.values():
            for item in row.get("concerns") or []:
                cid = item["id"] if isinstance(item, dict) else str(item)
                ids.add(cid)
        for cue in self.task_cues:
            ids.update(cue.get("concerns") or [])
        for viewpoint in self.viewpoints.values():
            ids.update(viewpoint.get("frames_concerns") or [])
        return ids

    def detect_language(self, text: str | None) -> str | None:
        if not text:
            return None
        blob = text.casefold()
        languages = list(self.notations.get("languages", {}))
        aliases = {"c4": "c4plantuml", "c4-plantuml": "c4plantuml", "plant uml": "plantuml"}
        for alias, name in aliases.items():
            if alias in blob and name in self.notations.get("languages", {}):
                return name
        for name in sorted(languages, key=len, reverse=True):
            if name.casefold() in blob:
                return name
        return None

    def bind_concerns(self, role_id: str | None, text: str) -> list[str]:
        ordered: list[str] = []
        catalog = self.catalog_concerns()
        if role_id and role_id in self.stakeholders:
            for item in self.stakeholders[role_id].get("concerns") or []:
                cid = item["id"] if isinstance(item, dict) else str(item)
                if cid in catalog and cid not in ordered:
                    ordered.append(cid)
        lowered = (text or "").lower()
        for cue in self.task_cues:
            if any(phrase in lowered for phrase in cue.get("phrases") or []):
                for cid in cue.get("concerns") or []:
                    if cid in catalog and cid not in ordered:
                        ordered.append(cid)
        return ordered

    def choose_language(
        self,
        view_type: str,
        *,
        preferred: str | None,
        formality: str,
        viewpoint_default: str | None = None,
    ) -> str:
        for candidate in (preferred, viewpoint_default):
            if not candidate:
                continue
            if candidate not in self.notations.get("languages", {}):
                raise PipelineError(f"Unknown diagram_language {candidate!r}")
            if not self.notation_supports(candidate, view_type):
                raise PipelineError(
                    f"{candidate} does not declare support for view_type {view_type}"
                )
            return candidate
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
        architectural_styles=_load_yaml("architectural_styles.yaml"),
        view_projection=_load_yaml("view_projection.yaml"),
    )
