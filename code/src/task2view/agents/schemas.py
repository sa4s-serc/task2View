"""Pydantic artifacts for the research-plan agent path (ADR-001)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StakeholderTaskProfile(BaseModel):
    stakeholder: str
    canonical_role: str | None = None
    original_label: str | None = None
    task: str
    target: str = ""
    goal: str = ""
    scope: str = ""
    constraints: list[str] = Field(default_factory=list)
    confidence: float | None = None
    source_goal: str = ""
    concerns: list[str] = Field(default_factory=list)
    environment: str = ""


class ArchitecturalQuestion(BaseModel):
    id: str
    text: str
    concern: str | None = None
    priority: int = 1


class QuestionSet(BaseModel):
    concerns: list[str] = Field(default_factory=list)
    questions: list[ArchitecturalQuestion] = Field(default_factory=list)


class PlannedView(BaseModel):
    id: str
    viewpoint_id: str
    view_type: str
    notation: str | None = None
    diagram_language: str = "plantuml"
    granularity: str = "component_or_service_level"
    purpose: str = ""
    addresses: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    deferred: bool = False


class ViewpointPlan(BaseModel):
    views: list[PlannedView] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AnalysisTask(BaseModel):
    id: str
    goal: str
    candidate_locations: list[str] = Field(default_factory=list)
    expected_evidence: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)
    target_view: str | None = None


class RepositoryAnalysisPlan(BaseModel):
    analysis_goal: str = ""
    target_view: str | None = None
    target_granularity: str | None = None
    analysis_tasks: list[AnalysisTask] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class GroundedClaim(BaseModel):
    claim: str
    source_element: str
    target_element: str | None = None
    relationship: str | None = None
    order: int | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    support_type: str = "directly_observed"
    question_ids: list[str] = Field(default_factory=list)
    analysis_task: str | None = None


class ArchitectureEvidenceModel(BaseModel):
    claims: list[GroundedClaim] = Field(default_factory=list)
    elements: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class EvidenceAwarePlan(BaseModel):
    views: list[dict[str, Any]] = Field(default_factory=list)
    questions: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    unanswered: list[str] = Field(default_factory=list)
