"""View format v2 (ADR-006 D3; design 03 §3).

A run produces a ViewSet: one ArchitectureView per selected viewpoint, plus the
correspondences that tie the same architectural element across views. Every
element and relation carries the id of the Architecture Evidence Model entry it
was projected from, so validation is a lookup. Vocabulary: ISO/IEC/IEEE 42010:2011.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ViewAttribute(BaseModel):
    name: str
    type: str | None = None
    key: bool = False
    foreign_key: bool = False


class ViewElement(BaseModel):
    id: str  # AEM element id, or "group:<...>" for layers / boundaries added by projection
    kind: str  # a kind the viewpoint allows (component, layer, entity, lifeline, actor, use_case, node, ...)
    name: str
    stereotype: str | None = None
    parent: str | None = None  # nesting: layer ⊃ component, node ⊃ artifact, system ⊃ use case
    responsibilities: list[str] = Field(default_factory=list)
    attributes: list[ViewAttribute] = Field(default_factory=list)
    realized_by: list[str] = Field(default_factory=list)
    support: str = "observed"
    group: bool = False  # container added by projection (layer, boundary), not an AEM element
    technology: str = ""


class ViewRelation(BaseModel):
    id: str
    kind: str
    source: str
    target: str
    label: str | None = None
    multiplicity: str | None = None  # "source..target", e.g. "*..1"
    support: str = "observed"
    protocol: str = ""
    against_layering: bool = False


class Interaction(BaseModel):
    order: int
    source: str
    target: str
    message: str
    kind: str = "call"  # call | return | create
    fragment: str | None = None


class ViewFragment(BaseModel):
    id: str
    kind: str  # alt | opt | loop
    guard: str


class TraceRow(BaseModel):
    element: str
    name: str
    files: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)


class ArchitectureView(BaseModel):
    id: str
    viewpoint_id: str
    viewpoint_name: str
    vb_ref: str
    model_kind: str
    title: str
    purpose: str
    detail_level: str
    max_elements: int
    addresses: list[str] = Field(default_factory=list)  # question ids
    overlays: list[str] = Field(default_factory=list)
    scenario: str | None = None
    elements: list[ViewElement] = Field(default_factory=list)
    relations: list[ViewRelation] = Field(default_factory=list)
    interactions: list[Interaction] = Field(default_factory=list)
    fragments: list[ViewFragment] = Field(default_factory=list)
    traceability: list[TraceRow] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    overflow: list[str] = Field(default_factory=list)  # AEM ids left out by the element cap

    def element(self, element_id: str) -> ViewElement | None:
        return next((e for e in self.elements if e.id == element_id), None)

    def content_elements(self) -> list[ViewElement]:
        return [e for e in self.elements if not e.group]


class ViewCorrespondence(BaseModel):
    rule: str
    elements: list[str]  # "<view id>:<element id>"


class ViewSet(BaseModel):
    system: str
    stakeholder: str | None = None
    goal: str
    views: list[ArchitectureView] = Field(default_factory=list)
    correspondences: list[ViewCorrespondence] = Field(default_factory=list)
    # behavioural participants that no structural view of the set draws (42010 correspondence check)
    correspondence_gaps: list[str] = Field(default_factory=list)
    declared_gaps: list[str] = Field(default_factory=list)
    uncovered_needs: list[str] = Field(default_factory=list)
    secondary_not_shown: list[str] = Field(default_factory=list)


class RenderResult(BaseModel):
    language: str
    model_kind: str
    source: str
    extension: str
    approximated: bool = False  # the language has no native construct for this model kind
    note: str = ""
    notation: str = ""  # ADR-007: the notation chosen for the view (notations.yaml), for structural views
