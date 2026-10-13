"""Deterministic viewpoint selection by covering information needs.

Design: docs/redesign/01-knowledge-model.md §6.

1. Applicable viewpoints: generic ones, plus style viewpoints whose
   ``applies_when`` signal is present in the repository facts.
2. Choose the smallest set (cap ``max_views``) that covers the most PRIMARY
   needs. Secondary needs never add a view: among equally small sets, the one
   that also covers more secondary needs wins, and the rest are reported as not
   shown. ``layering`` may be covered by a layered overlay on a host view instead
   of a view of its own. Further ties: more needs framed (not just covered),
   then role prior, then catalog order.
3. Specialise a selected ``cnc-generic`` view to the first applicable C&C style.
4. Apply overlays (``combine_with``) that apply to this repository.
5. A view whose ``evidence`` signals are all absent stays selected and carries a
   declared gap.
6. Assign each goal subject to every view that frames one of its needs.

No LLM is involved: the same needs and facts always give the same plan.
"""

from __future__ import annotations

from itertools import combinations

from pydantic import BaseModel, Field

from task2view.knowledge.catalog import Catalog, Viewpoint

MAX_VIEWS = 3


class RepoFacts(BaseModel):
    """Repository signals (catalog `signals`). Built by the Phase 0 card; hand-written in tests."""

    signals: set[str] = Field(default_factory=set)


class GoalSubject(BaseModel):
    text: str
    needs: list[str] = Field(default_factory=list)


class SelectionInput(BaseModel):
    needs: list[str]  # primary: what the request is centrally about
    secondary_needs: list[str] = Field(default_factory=list)  # mentioned in passing; never adds a view
    subjects: list[GoalSubject] = Field(default_factory=list)
    role: str | None = None
    detail_level: str = "feature"


class PlannedView(BaseModel):
    viewpoint_id: str
    family: str
    model_kind: str
    needs: list[str]
    subjects: list[str] = Field(default_factory=list)
    overlays: list[str] = Field(default_factory=list)
    specialised_from: str | None = None
    detail_level: str
    granularity: dict = Field(default_factory=dict)
    evidence_gap: str | None = None
    rationale: str = ""


class ViewPlan(BaseModel):
    views: list[PlannedView]
    needs: list[str]
    secondary_needs: list[str] = Field(default_factory=list)
    needs_from_role: bool = False
    uncovered_needs: list[str] = Field(default_factory=list)  # primary needs no view answers
    secondary_not_shown: list[str] = Field(default_factory=list)
    detail_level: str
    notes: list[str] = Field(default_factory=list)


def applicable(vp: Viewpoint, facts: RepoFacts) -> bool:
    return vp.generic or any(sig in facts.signals for sig in vp.applies_when)


def select_views(
    request: SelectionInput,
    catalog: Catalog,
    facts: RepoFacts,
    *,
    max_views: int = MAX_VIEWS,
) -> ViewPlan:
    notes: list[str] = []
    needs = [n for n in dict.fromkeys(request.needs) if n in catalog.needs]
    secondary = [n for n in dict.fromkeys(request.secondary_needs) if n in catalog.needs and n not in needs]
    unknown = [n for n in request.needs + request.secondary_needs if n not in catalog.needs]
    if unknown:
        notes.append(f"ignored unknown needs: {', '.join(unknown)}")
    if not needs and secondary:
        needs, secondary = secondary, []
        notes.append("no need was marked primary; all stated needs are treated as primary")
    needs_from_role = False
    priors = catalog.roles[request.role].priors if request.role in catalog.roles else {}
    if not needs and priors:
        top = max(priors.values())
        needs = [n for n in catalog.needs if priors.get(n) == top]
        needs_from_role = True
        notes.append(
            f"goal states no need; used the needs role {request.role!r} has at the highest prior "
            f"({catalog.roles[request.role].prior_source}): {', '.join(needs)}"
        )

    layered = catalog.viewpoints.get("layered")
    layered_overlay_ok = layered is not None and applicable(layered, facts)
    candidates = [
        vp for vp in catalog.viewpoints.values()
        if applicable(vp, facts) and vp.covers() & set(needs) and vp.style_of is None
    ]

    def covered(views: tuple[Viewpoint, ...], wanted: list[str] = needs) -> set[str]:
        got = set().union(*(vp.covers() for vp in views)) & set(wanted)
        if "layering" in wanted and layered_overlay_ok and any("layered" in vp.combine_with for vp in views):
            got.add("layering")
        return got

    def score(views: tuple[Viewpoint, ...]):
        framed = sum(len(set(vp.frames) & set(needs)) for vp in views)
        prior = sum(max((priors.get(n, 0.0) for n in vp.covers() & set(needs)), default=0.0) for vp in views)
        order = sum(catalog.order(vp.id) for vp in views)
        return (len(covered(views)), -len(views), len(covered(views, secondary)), framed, prior, -order)

    best: tuple[Viewpoint, ...] = ()
    for size in range(1, max_views + 1):
        for combo in combinations(candidates, size):
            if not best or score(combo) > score(best):
                best = combo
    chosen = sorted(best, key=lambda vp: needs.index(_first_need(vp, needs, covered((vp,)))))
    uncovered = [n for n in needs if n not in covered(tuple(chosen))]
    if uncovered:
        notes.append(f"needs not covered within {max_views} views: {', '.join(uncovered)}")
    not_shown = [n for n in secondary if n not in covered(tuple(chosen), secondary)]

    views: list[PlannedView] = []
    for vp in chosen:
        own = [n for n in needs if n in covered((vp,))] + [n for n in secondary if n in covered((vp,), secondary)]
        final, specialised_from = _specialise(vp, catalog, facts)
        overlays = [o for o in final.combine_with if applicable(catalog.viewpoint(o), facts)]
        gap = None
        if final.evidence and not any(sig in facts.signals for sig in final.evidence):
            gap = f"no repository evidence of: {', '.join(final.evidence)}"
        views.append(
            PlannedView(
                viewpoint_id=final.id,
                family=final.family,
                model_kind=final.model_kind,
                needs=own,
                overlays=overlays,
                specialised_from=specialised_from,
                detail_level=request.detail_level,
                granularity=catalog.granularity(final.id, request.detail_level),
                evidence_gap=gap,
                rationale=_rationale(final, own, specialised_from, overlays),
            )
        )
    _assign_subjects(views, request.subjects, needs)
    return ViewPlan(
        views=views,
        needs=needs,
        secondary_needs=secondary,
        needs_from_role=needs_from_role,
        uncovered_needs=uncovered,
        secondary_not_shown=not_shown,
        detail_level=request.detail_level,
        notes=notes,
    )


def _first_need(vp: Viewpoint, needs: list[str], got: set[str]) -> str:
    return next(n for n in needs if n in got)


def _specialise(vp: Viewpoint, catalog: Catalog, facts: RepoFacts) -> tuple[Viewpoint, str | None]:
    if vp.id != "cnc-generic":
        return vp, None
    for style_id in catalog.cnc_style_priority:
        style = catalog.viewpoint(style_id)
        if applicable(style, facts):
            return style, vp.id
    return vp, None


def _rationale(vp: Viewpoint, needs: list[str], specialised_from: str | None, overlays: list[str]) -> str:
    parts = [f"{vp.name} ({vp.vb_ref}) covers {', '.join(needs)}"]
    if specialised_from:
        parts.append(f"specialised from {specialised_from} because the repository shows {', '.join(vp.applies_when)}")
    if overlays:
        parts.append(f"combined with {', '.join(overlays)} (V&B 6.6)")
    return "; ".join(parts)


def _assign_subjects(views: list[PlannedView], subjects: list[GoalSubject], needs: list[str]) -> None:
    if not views:
        return
    for subject in subjects:
        targets = [v for v in views if set(subject.needs) & set(v.needs)] or [views[0]]
        for view in targets:
            view.subjects.append(subject.text)


def select_views_for_spec(request: SelectionInput, catalog: Catalog, facts: RepoFacts, *, max_views: int = MAX_VIEWS,
                          behaviour: str = "structure", compact_catalog: Catalog | None = None) -> ViewPlan:
    """ADR-007: when the view spec says the request is about behaviour too, one view slot is kept for a
    behavioural view, instead of letting structural views fill the budget and leave behaviour uncovered.
    The remaining structural budget is chosen with ``compact_catalog`` when given: a catalog in which
    part-level component views also cover decomposition (they show responsibilities inside layers)."""
    plan = select_views(request, catalog, facts, max_views=max_views)
    behavioural = [n for n in request.needs if catalog.needs[n].category == "behavior"]
    if behaviour not in {"both", "interaction"} or not set(plan.uncovered_needs) & set(behavioural) or max_views < 2:
        return plan
    rest = request.model_copy(update={"needs": [n for n in request.needs if n not in behavioural]})
    structural = select_views(rest, compact_catalog or catalog, facts, max_views=max_views - 1) if rest.needs else None
    dynamic = select_views(request.model_copy(update={"needs": behavioural, "secondary_needs": []}), catalog, facts,
                           max_views=1)
    base = structural or dynamic
    taken = {v.viewpoint_id for v in base.views}
    return base.model_copy(update={
        "views": base.views + ([v for v in dynamic.views if v.viewpoint_id not in taken] if structural else []),
        "needs": request.needs,
        "uncovered_needs": (structural.uncovered_needs if structural else []) + dynamic.uncovered_needs,
        "notes": base.notes + [f"one view kept for the behaviour the request asks about ({', '.join(behavioural)})"],
    })
