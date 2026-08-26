"""JSON contracts for pipeline artifacts (spec §4–§7)."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class RepositoryRef(BaseModel):
    name: str
    location: str
    revision: str = "unknown"


class StakeholderRef(BaseModel):
    role: str
    original_label: str
    iso_42010_class: str | None = None
    vb_row: str | None = None


class TaskRef(BaseModel):
    description: str


class Preferences(BaseModel):
    diagram_language: str | None = None
    max_views: int = 1
    scope_token_budget: int = 120_000


class CleanedFile(BaseModel):
    path: str
    language: str
    bytes: int
    reason: str = "source_extension"


class DroppedFile(BaseModel):
    path: str
    reason: str


class CleanedCorpus(BaseModel):
    request_id: str
    repository: str
    kept: list[CleanedFile] = Field(default_factory=list)
    dropped: list[DroppedFile] = Field(default_factory=list)
    counts: dict[str, Any] = Field(default_factory=dict)


class NormalizedRequest(BaseModel):
    request_id: str
    repository: RepositoryRef
    stakeholder: StakeholderRef
    task: TaskRef
    goal: str
    preferences: Preferences
    corpus: dict[str, Any] | None = None
    environment: str | None = None
    concerns: list[str] = Field(default_factory=list)


class RequiredInformation(BaseModel):
    id: str
    need: str


class SelectedView(BaseModel):
    view_type: str
    notation: str
    diagram_language: str
    granularity: str
    purpose: str
    viewpoint_id: str | None = None
    grain_unit: str | None = None


class RankedCandidate(BaseModel):
    viewpoint_id: str
    view_type: str
    vb_column: str | None = None
    vb_level: str | None = None
    score: float
    reasons: list[str] = Field(default_factory=list)


class SelectionTrace(BaseModel):
    method: str = "views-and-beyond-steps-1-3"
    vb_candidates: list[dict[str, Any]] = Field(default_factory=list)
    task_concerns: list[str] = Field(default_factory=list)
    preferred_viewpoints: list[str] = Field(default_factory=list)
    ranked: list[RankedCandidate] = Field(default_factory=list)
    dropped_beyond_views: list[str] = Field(default_factory=list)


class ViewSpecification(BaseModel):
    request_id: str
    stakeholder: str
    task_summary: str
    architectural_concerns: list[str]
    selected_view: SelectedView
    required_information: list[RequiredInformation]
    declared_gaps: list[str] = Field(default_factory=list)
    unanswered_concerns: list[str] = Field(default_factory=list)
    selection_trace: SelectionTrace | None = None


class ScopeCandidate(BaseModel):
    path: str
    serves: list[str] = Field(default_factory=list)
    origin: str
    score: float = 0.0
    reason: str = ""


class RepositoryScope(BaseModel):
    request_id: str
    target_view: str
    scope_strategy: str
    graph: dict[str, Any] = Field(default_factory=dict)
    candidate_areas: list[ScopeCandidate] = Field(default_factory=list)
    scope_constraints: dict[str, Any] = Field(default_factory=dict)
    coverage_report: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    file: str | None = None
    symbol: str | None = None
    excerpt: str | None = None


class ViewElement(BaseModel):
    id: str
    name: str
    kind: str
    role: str | None = None
    external: bool = False
    evidence: Evidence | None = None
    support: Literal["observed", "inferred"] = "observed"
    agreement: float | None = None


class ViewRelation(BaseModel):
    id: str
    frm: str = Field(alias="from")
    to: str
    kind: str
    label: str | None = None
    order: int | None = None
    evidence: Evidence | None = None
    support: Literal["observed", "inferred"] = "observed"
    agreement: float | None = None

    model_config = {"populate_by_name": True}


class ViewGroup(BaseModel):
    id: str
    name: str
    kind: str
    contains: list[str] = Field(default_factory=list)


class ViewModel(BaseModel):
    request_id: str
    view_type: str
    granularity: str
    groups: list[ViewGroup] = Field(default_factory=list)
    elements: list[ViewElement] = Field(default_factory=list)
    relations: list[ViewRelation] = Field(default_factory=list)
    unanswered: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    request_id: str
    notation: str | None = None
    syntax: dict[str, Any] = Field(default_factory=dict)
    semantic: dict[str, Any] = Field(default_factory=dict)
    verdict: str


class PipelineError(ValueError):
    """Contract or knowledge-base failure."""


ALLOWED_ELEMENT_KINDS = {
    "actor",
    "component",
    "module",
    "class",
    "service",
    "datastore",
    "external_system",
    "deployment_node",
    "state",
    "system",
}

ALLOWED_RELATION_KINDS = {
    "uses",
    "calls",
    "call",
    "return",
    "depends",
    "dataflow",
    "inherits",
    "implements",
    "contains",
    "deploys",
    "transition",
}

ELEMENT_KIND_ALIASES = {
    "class": "module",
    "service": "component",
    "entity": "module",
}

RELATION_KIND_ALIASES = {
    "call": "calls",
    "depends": "uses",
    "inherits": "uses",
    "implements": "uses",
    "return": "calls",
}


def canonical_element_kind(kind: str) -> str:
    mapped = ELEMENT_KIND_ALIASES.get(kind, kind)
    return mapped if mapped in ALLOWED_ELEMENT_KINDS else "component"


def canonical_relation_kind(kind: str) -> str:
    mapped = RELATION_KIND_ALIASES.get(kind, kind)
    return mapped if mapped in ALLOWED_RELATION_KINDS else "uses"

ALLOWED_GROUP_KINDS = {"layer", "package", "boundary", "node", "subsystem"}
ALLOWED_VIEW_TYPES = {
    "sequence_view",
    "component_view",
    "deployment_view",
    "class_view",
    "state_view",
    "dataflow_view",
    "context_view",
}


class UserRequest(BaseModel):
    """The two pipeline inputs: code (repository) and a stakeholder goal statement.

    `stakeholder` / `task` remain accepted as a split form of the goal.
    """

    code: str | None = None
    repository: str | None = None
    goal: str | None = None
    stakeholder: str | None = None
    task: str | None = None
    request_id: str | None = None
    diagram_language: str | None = None
    max_views: int = 1
    scope_token_budget: int = 120_000
    scope_strategy: str | None = None
    gemini_model: str | None = None
    samples: int = 1
    skip_extract: bool = False
    legacy: bool = False
    extract_workers: int = 2
    extract_backend: str | None = None
    skip_critic: bool = False
    config: str | None = None

    @model_validator(mode="after")
    def require_code_and_goal(self) -> Self:
        repo = (self.code or self.repository or "").strip()
        if not repo:
            raise ValueError("code (repository path) is required")
        self.code = repo
        self.repository = repo
        if self.goal and self.goal.strip():
            self.goal = self.goal.strip()
            return self
        if self.stakeholder and self.task and self.task.strip():
            self.goal = self.task.strip()
            self.task = self.task.strip()
            return self
        raise ValueError(
            "provide a stakeholder goal (--goal), or both --stakeholder and --task"
        )
