"""Views and Beyond knowledge model: information needs, viewpoints, role priors.

Design: docs/redesign/01-knowledge-model.md. Data: knowledge/data/vb/*.yaml.
The loader validates every cross-reference, so a typo in the YAML fails at load
time instead of silently producing an unreachable viewpoint.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from task2view.contracts.models import PipelineError

DetailLevel = Literal["overview", "feature", "detailed"]
Family = Literal["module", "cnc", "allocation", "behavior", "beyond"]
NeedCategory = Literal["structure", "behavior", "allocation", "beyond"]
DETAIL_LEVELS: tuple[str, ...] = ("overview", "feature", "detailed")


class Need(BaseModel):
    id: str
    category: NeedCategory
    description: str
    cues: list[str] = Field(default_factory=list)


class Viewpoint(BaseModel):
    id: str
    name: str
    vb_ref: str
    family: Family
    applies_when: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    frames: list[str]
    also_covers: list[str] = Field(default_factory=list)
    style_of: str | None = None
    element_kinds: list[str]
    relation_kinds: list[str]
    fragments: list[str] = Field(default_factory=list)
    scope: str | None = None
    model_kind: str
    combine_with: list[str] = Field(default_factory=list)
    granularity: dict[str, dict] = Field(default_factory=dict)
    evidence_classes: list[str] = Field(default_factory=list)

    @property
    def generic(self) -> bool:
        return not self.applies_when

    def covers(self) -> set[str]:
        return set(self.frames) | set(self.also_covers)


class Role(BaseModel):
    id: str
    label: str
    vb_row: str | None
    aliases: list[str]
    priors: dict[str, float]  # derived from V&B Table 9.1, or the extension priors
    prior_source: str


class Catalog(BaseModel):
    needs: dict[str, Need]
    quality_attributes: list[str]
    signals: dict[str, str]
    viewpoints: dict[str, Viewpoint]  # in catalog order
    roles: dict[str, Role]
    cnc_style_priority: list[str]
    detail_rule: dict[str, int]

    def viewpoint(self, viewpoint_id: str) -> Viewpoint:
        try:
            return self.viewpoints[viewpoint_id]
        except KeyError as exc:
            raise PipelineError(f"unknown viewpoint {viewpoint_id!r}") from exc

    def order(self, viewpoint_id: str) -> int:
        return list(self.viewpoints).index(viewpoint_id)

    def granularity(self, viewpoint_id: str, level: str) -> dict:
        vp = self.viewpoint(viewpoint_id)
        return dict(vp.granularity.get(level) or {})

    def resolve_role(self, label: str | None) -> str | None:
        """Map a free-text role label to a role id (exact alias, then longest alias inside the label)."""
        text = " ".join((label or "").casefold().split())
        if not text:
            return None
        for role in self.roles.values():
            if text == role.id or text in role.aliases:
                return role.id
        best: tuple[int, str] | None = None
        for role in self.roles.values():
            for alias in role.aliases:
                if f" {alias} " in f" {text} " and (best is None or len(alias) > best[0]):
                    best = (len(alias), role.id)
        return best[1] if best else None


def _read(name: str, folder: str | None = "vb") -> dict:
    root = resources.files("task2view.knowledge.data")
    path = root.joinpath(folder, name) if folder else root.joinpath(name)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _role_priors(row: dict, roles_doc: dict, viewpoints: dict[str, Viewpoint], table: dict) -> tuple[dict[str, float], str]:
    """Prior per need = highest Table 9.1 detail weight over the columns whose viewpoint frames it."""
    if row.get("vb_row") is None:
        return dict(row.get("extension_priors") or {}), f"extension: {row.get('extension_reason', '')}"
    cells = table["rows"].get(row["vb_row"])
    if cells is None:
        raise PipelineError(f"role row {row['vb_row']!r} is not in V&B Table 9.1")
    weights = roles_doc["detail_weights"]
    priors: dict[str, float] = {}
    for column, level in cells.items():
        if column == "vb_label":
            continue
        vp_id = roles_doc["table_9_1_columns"].get(column)
        if not vp_id:
            continue
        for need in viewpoints[vp_id].frames:
            priors[need] = max(priors.get(need, 0.0), float(weights[level]))
    return priors, f"V&B Table 9.1 row {row['vb_row']!r}"


@lru_cache(maxsize=1)
def load_catalog() -> Catalog:
    needs_doc, vp_doc, roles_doc = _read("needs.yaml"), _read("viewpoints.yaml"), _read("roles.yaml")
    table = _read("vb_table_9_1.yaml")
    needs = {row["id"]: Need(**row) for row in needs_doc["needs"]}
    families = vp_doc.get("families") or {}
    viewpoints: dict[str, Viewpoint] = {}
    for row in vp_doc["viewpoints"]:
        vp = Viewpoint(**row)
        if not vp.granularity:
            vp.granularity = dict((families.get(vp.family) or {}).get("granularity") or {})
        if not vp.evidence_classes:
            vp.evidence_classes = list((families.get(vp.family) or {}).get("evidence_classes") or [])
        if vp.id in viewpoints:
            raise PipelineError(f"duplicate viewpoint id {vp.id!r}")
        viewpoints[vp.id] = vp
    for column, vp_id in roles_doc["table_9_1_columns"].items():
        if vp_id and vp_id not in viewpoints:
            raise PipelineError(f"Table 9.1 column {column!r} maps to unknown viewpoint {vp_id!r}")
    roles = {}
    for rid, row in roles_doc["roles"].items():
        priors, source = _role_priors(row, roles_doc, viewpoints, table)
        roles[rid] = Role(id=rid, label=row["label"], vb_row=row.get("vb_row"), aliases=row["aliases"],
                          priors=priors, prior_source=source)
    catalog = Catalog(
        needs=needs,
        quality_attributes=list(needs_doc.get("quality_attributes") or []),
        signals=dict(vp_doc["signals"]),
        viewpoints=viewpoints,
        roles=roles,
        cnc_style_priority=list(vp_doc.get("cnc_style_priority") or []),
        detail_rule=dict(needs_doc["detail_levels"]),
    )
    _validate(catalog)
    return catalog


def _validate(cat: Catalog) -> None:
    errors: list[str] = []
    for vp in cat.viewpoints.values():
        for need in vp.covers():
            if need not in cat.needs:
                errors.append(f"{vp.id}: unknown need {need!r}")
        for sig in vp.applies_when + vp.evidence:
            if sig not in cat.signals:
                errors.append(f"{vp.id}: unknown signal {sig!r}")
        for other in vp.combine_with + ([vp.style_of] if vp.style_of else []):
            if other not in cat.viewpoints:
                errors.append(f"{vp.id}: unknown viewpoint {other!r}")
        for level in DETAIL_LEVELS:
            if "max_elements" not in (vp.granularity.get(level) or {}):
                errors.append(f"{vp.id}: no max_elements for detail level {level!r}")
        behavioural = vp.family == "behavior"
        for need in vp.covers():
            category = cat.needs[need].category if need in cat.needs else None
            if behavioural and category == "structure" or not behavioural and category == "behavior":
                errors.append(f"{vp.id}: {vp.family} viewpoint covers {category} need {need!r}")
    for style in cat.cnc_style_priority:
        if style not in cat.viewpoints or cat.viewpoints[style].style_of != "cnc-generic":
            errors.append(f"cnc_style_priority: {style!r} is not a C&C style")
    for role in cat.roles.values():
        for need in role.priors:
            if need not in cat.needs:
                errors.append(f"role {role.id}: unknown need {need!r}")
    framed = {n for vp in cat.viewpoints.values() for n in vp.covers()}
    for need in cat.needs:
        if need not in framed:
            errors.append(f"need {need!r} is framed by no viewpoint")
    if errors:
        raise PipelineError("viewpoint catalog is inconsistent:\n  " + "\n  ".join(errors))


@lru_cache(maxsize=1)
def load_uml() -> dict:
    """UML 2.5.1 knowledge (knowledge/data/uml/uml-2.5.1.yaml, ADR-008): diagram types, their symbols and
    paths, the Standard Profile stereotypes and the Task2View profile."""
    return _read("uml-2.5.1.yaml", "uml")


def uml_diagram_type(model_kind: str) -> str | None:
    """The UML diagram type a view's model kind is drawn as; None when it is not drawable in UML."""
    return load_uml()["model_kinds"].get(model_kind)
