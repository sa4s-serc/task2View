"""Phase 6 — need-evidence reconciliation decides, per view (ADR-006 D3; design 03 §5).

Rule-based and logged; no model call. For each projected view:
1. Coverage per assigned question: supported (an AEM claim answering it is drawn
   in the view), partial (claims exist but none is drawn, or the view is built
   from repository facts only), unsupported (no evidence at all).
2. A decision:
   - drop               nothing to draw and no evidence will come
   - gap                the viewpoint's evidence is absent from the repository: keep
                        what exists and report the declared gap (decision 01 §8)
   - request_evidence   questions unsupported and evidence rounds remain
   - simplify           the selection overflows the detail-level cap: coarser grain
   - confirm            otherwise (limitations stay visible)

A `split` into several views is part of the design but not yet automatic; an
overflowing view is simplified instead, and the limitation says so.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from task2view.contracts.aem import EvidenceModel, Question
from task2view.contracts.views import ArchitectureView
from task2view.phase3.selection import PlannedView

Decision = Literal["confirm", "simplify", "request_evidence", "gap", "drop"]


class QuestionCoverage(BaseModel):
    question: str
    status: Literal["supported", "partial", "unsupported"]
    claims: list[str] = Field(default_factory=list)
    note: str = ""


class ViewDecision(BaseModel):
    view_id: str
    decision: Decision
    reason: str
    coverage: list[QuestionCoverage] = Field(default_factory=list)
    unsupported_questions: list[str] = Field(default_factory=list)


def _drawn_claims(view: ArchitectureView, aem: EvidenceModel) -> set[str]:
    ids = {e.id for e in view.elements} | {m for e in view.elements for m in e.realized_by}
    drawn: set[str] = set()
    for eid in ids:
        el = aem.elements.get(eid)
        if el is not None:
            drawn.update(el.claims)
    for r in view.relations:
        rel = aem.relations.get(r.id)
        if rel is not None:
            drawn.update(rel.claims)
    for scenario in aem.scenarios.values():
        if scenario.name == view.scenario:
            for st in scenario.steps:
                drawn.update(st.claims)
    return drawn


def coverage(view: ArchitectureView, questions: list[Question], aem: EvidenceModel) -> list[QuestionCoverage]:
    drawn = _drawn_claims(view, aem)
    has_content = bool(view.content_elements())
    out = []
    for q in questions:
        if q.view_id != view.id:
            continue
        claims = [c.id for c in aem.claims.values() if q.id in c.question_ids]
        shown = [c for c in claims if c in drawn]
        if shown:
            out.append(QuestionCoverage(question=q.id, status="supported", claims=shown))
        elif claims:
            out.append(QuestionCoverage(question=q.id, status="partial", claims=claims,
                                        note="evidence exists but is not drawn in this view"))
        elif has_content:
            out.append(QuestionCoverage(question=q.id, status="partial",
                                        note="view built from repository facts; no claim answers the question directly"))
        else:
            out.append(QuestionCoverage(question=q.id, status="unsupported"))
    return out


def decide(
    view: ArchitectureView,
    planned: PlannedView,
    questions: list[Question],
    aem: EvidenceModel,
    *,
    evidence_rounds_left: int,
    already_simplified: bool = False,
) -> ViewDecision:
    cov = coverage(view, questions, aem)
    unsupported = [c.question for c in cov if c.status == "unsupported"]
    base = dict(view_id=view.id, coverage=cov, unsupported_questions=unsupported)
    if not view.content_elements():
        if planned.evidence_gap or view.gaps:
            return ViewDecision(decision="gap", reason="; ".join(view.gaps) or planned.evidence_gap or "", **base)
        if evidence_rounds_left > 0:
            return ViewDecision(decision="request_evidence", reason="nothing to draw yet", **base)
        return ViewDecision(decision="drop", reason="no evidence for this view after all rounds", **base)
    if unsupported and evidence_rounds_left > 0:
        return ViewDecision(decision="request_evidence",
                            reason=f"{len(unsupported)} question(s) without evidence: {', '.join(unsupported)}", **base)
    if view.overflow and not already_simplified and view.model_kind in {"uml-component", "uml-package"}:
        return ViewDecision(decision="simplify",
                            reason=f"{len(view.overflow)} element(s) over the {view.detail_level} cap", **base)
    if view.gaps or planned.evidence_gap:
        return ViewDecision(decision="gap", reason="; ".join(view.gaps) or planned.evidence_gap or "", **base)
    return ViewDecision(decision="confirm", reason="all assigned questions have evidence in the view"
                        if not unsupported else "evidence rounds exhausted; unanswered questions are reported", **base)
