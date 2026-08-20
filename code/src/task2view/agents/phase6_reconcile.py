"""PDF Phase 6 — Need–Evidence Reconciliation (deterministic over claims)."""

from __future__ import annotations

from task2view.agents.schemas import (
    ArchitectureEvidenceModel,
    EvidenceAwarePlan,
    QuestionSet,
    ViewpointPlan,
)


def reconcile(
    questions: QuestionSet,
    viewpoint_plan: ViewpointPlan,
    evidence: ArchitectureEvidenceModel,
) -> EvidenceAwarePlan:
    covered: set[str] = set()
    for claim in evidence.claims:
        covered.update(claim.question_ids)
    q_rows = []
    unanswered: list[str] = []
    for q in questions.questions:
        status = "supported" if q.id in covered else "unsupported"
        if status == "unsupported":
            unanswered.append(q.id)
        q_rows.append({"id": q.id, "text": q.text, "status": status})
    views = []
    limitations: list[str] = []
    for view in viewpoint_plan.views:
        if view.deferred:
            views.append({"id": view.id, "status": "deferred", "viewpoint_id": view.viewpoint_id})
            continue
        needed = view.addresses or [q.id for q in questions.questions]
        hit = [qid for qid in needed if qid in covered]
        if not needed:
            status = "partial" if evidence.claims else "unsupported"
        elif len(hit) == len(needed):
            status = "supported"
        elif hit:
            status = "partial"
        else:
            status = "unsupported"
        if status != "supported":
            missing = [qid for qid in needed if qid not in covered]
            limitations.append(f"{view.id}: {status}; missing {missing}")
        views.append(
            {
                "id": view.id,
                "viewpoint_id": view.viewpoint_id,
                "view_type": view.view_type,
                "status": status,
                "supported_questions": hit,
            }
        )
    if not evidence.claims:
        limitations.append("No grounded claims were extracted.")
    return EvidenceAwarePlan(
        views=views,
        questions=q_rows,
        limitations=limitations,
        unanswered=unanswered,
    )
