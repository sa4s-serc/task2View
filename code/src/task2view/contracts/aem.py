"""Architecture Evidence Model and the artifacts that feed it (ADR-006 D2; design 02 §4-6).

Questions (Phase 2) -> investigation tasks (Phase 4) -> verified claims (Phase 5)
-> consolidated architectural elements, relations and scenarios (Phase 5b).
Every element and relation keeps the code symbols and claims behind it, so a
view projected from the model can be checked by lookup, not by name matching.
Vocabulary: ISO/IEC/IEEE 42010:2011.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Support = Literal["observed", "inferred", "weak", "documented"]


class Question(BaseModel):
    id: str
    view_id: str
    viewpoint_id: str
    need: str
    subject: str | None = None
    element_kinds: list[str] = Field(default_factory=list)
    relation_kinds: list[str] = Field(default_factory=list)
    fragments: list[str] = Field(default_factory=list)
    text: str


class Seeds(BaseModel):
    symbols: list[str] = Field(default_factory=list)  # card symbol ids
    paths: list[str] = Field(default_factory=list)  # files or directories
    classes: list[str] = Field(default_factory=list)  # corpus classes to search


class InvestigationTask(BaseModel):
    id: str
    view_id: str
    viewpoint_id: str
    question_ids: list[str]
    need: str
    subject: str | None = None
    goal: str
    seeds: Seeds
    expect_elements: list[str] = Field(default_factory=list)
    expect_relations: list[str] = Field(default_factory=list)
    budget_steps: int
    suggested_by: list[str] = Field(default_factory=list)


class EvidenceRef(BaseModel):
    file: str
    symbol: str | None = None
    lines: list[int] = Field(default_factory=list)  # [start, end], 1-based
    excerpt: str = ""


class Claim(BaseModel):
    id: str
    task: str
    kind: Literal["element", "relation", "interaction", "state", "transition"]
    element_kind: str | None = None  # element claims
    name: str | None = None  # element / state name as the code names it
    symbol: str | None = None  # resolved card symbol for element claims
    responsibilities: list[str] = Field(default_factory=list)
    attributes: list[dict] = Field(default_factory=list)  # {name, type, key}
    source: str | None = None  # relation / interaction / transition source (symbol or name)
    target: str | None = None
    relation: str | None = None  # relation kind or message label
    label: str | None = None
    order: int | None = None  # interactions
    scenario: str | None = None
    condition: str | None = None  # guard of an alternative path
    evidence: list[EvidenceRef] = Field(default_factory=list)
    support: Support = "inferred"
    confidence: float = 0.5
    question_ids: list[str] = Field(default_factory=list)


class Responsibility(BaseModel):
    text: str
    claims: list[str] = Field(default_factory=list)


class Attribute(BaseModel):
    name: str
    type: str | None = None
    key: bool = False
    foreign_key: bool = False


class ArchElement(BaseModel):
    id: str
    kind: str  # catalog element kind: component, entity, actor, use_case, node, artifact, datastore, state, ...
    name: str
    realized_by: list[str] = Field(default_factory=list)  # card symbol ids
    layer: str | None = None
    responsibilities: list[Responsibility] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    details: dict[str, str] = Field(default_factory=dict)
    support: Support = "observed"
    claims: list[str] = Field(default_factory=list)
    named_by: Literal["symbol", "package", "model", "fact"] = "symbol"


class ArchRelation(BaseModel):
    id: str
    kind: str  # uses, association, composition, generalization, deploys, communicates, include, ...
    source: str  # element id
    target: str
    label: str | None = None
    multiplicity: str | None = None
    member_edges: list[str] = Field(default_factory=list)  # "src -kind-> tgt" card edges behind a lifted relation
    claims: list[str] = Field(default_factory=list)
    support: Support = "observed"


class Step(BaseModel):
    order: int
    source: str  # element id
    target: str
    message: str
    kind: Literal["call", "return", "create"] = "call"
    fragment: str | None = None
    claims: list[str] = Field(default_factory=list)


class Fragment(BaseModel):
    id: str
    kind: Literal["alt", "opt", "loop"]
    guard: str


class Scenario(BaseModel):
    id: str
    name: str
    steps: list[Step] = Field(default_factory=list)
    fragments: list[Fragment] = Field(default_factory=list)


class Correspondence(BaseModel):
    rule: str
    elements: list[str]
    note: str = ""


class EvidenceModel(BaseModel):
    elements: dict[str, ArchElement] = Field(default_factory=dict)
    relations: dict[str, ArchRelation] = Field(default_factory=dict)
    scenarios: dict[str, Scenario] = Field(default_factory=dict)
    claims: dict[str, Claim] = Field(default_factory=dict)
    rejected_claims: list[dict] = Field(default_factory=list)  # {claim, reason}
    component_of: dict[str, str] = Field(default_factory=dict)  # symbol id -> element id
    correspondences: list[Correspondence] = Field(default_factory=list)
    # convergence / divergence / absence -> relation ids (code edges vs claims, between components)
    reflexion: dict[str, list[str]] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
