"""Phase 2 — architectural questions per selected view (ADR-006 D1; ADR-005 order).

Questions are written after viewpoint selection, for each planned view, at that
view's grain: one question per (need, subject) assigned to the view, or one per
need when the view has no subjects. The wording comes from the catalog's need
definition, so the same profile always yields the same questions, and a
question can only ask for element and relation kinds its viewpoint can draw.
"""

from __future__ import annotations

from task2view.contracts.aem import Question
from task2view.knowledge.catalog import Catalog
from task2view.phase1.needs import NeedProfile
from task2view.phase3.selection import ViewPlan


def view_id(index: int, viewpoint_id: str) -> str:
    return f"V{index + 1}-{viewpoint_id}"


def derive_view_questions(profile: NeedProfile, plan: ViewPlan, catalog: Catalog) -> list[Question]:
    questions: list[Question] = []
    target = profile.target or "the system"
    subject_needs = {s.text: s.needs for s in profile.subjects}
    for index, view in enumerate(plan.views):
        vp = catalog.viewpoint(view.viewpoint_id)
        vid = view_id(index, vp.id)
        pairs = [(need_id, s) for need_id in view.needs
                 for s in [s for s in view.subjects if need_id in subject_needs.get(s, [])] or [None]]
        # a subject without needs of this view is still asked about, under the view's first need
        asked = {s for _, s in pairs}
        pairs += [(view.needs[0], s) for s in view.subjects if s not in asked and view.needs]
        for need_id, subject in pairs:
            questions.append(Question(
                id=f"AQ{len(questions) + 1}",
                view_id=vid,
                viewpoint_id=vp.id,
                need=need_id,
                subject=subject,
                element_kinds=list(vp.element_kinds),
                relation_kinds=list(vp.relation_kinds),
                fragments=list(vp.fragments),
                text=f"For {subject or target}: {catalog.needs[need_id].description}?",
            ))
    return questions
