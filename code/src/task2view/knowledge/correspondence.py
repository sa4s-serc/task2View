"""ISO 42010 correspondence kernel.

stakeholder × concerns × task → catalog viewpoint → published grain.

No LLM. No repository. The agentic path calls this so grain is looked up
from the catalog after a viewpoint is chosen. With no viewpoint id, the
same rank chooses.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from task2view.contracts.models import (
    ALLOWED_VIEW_TYPES,
    NormalizedRequest,
    PipelineError,
    RankedCandidate,
    SelectedView,
    SelectionTrace,
    ViewSpecification,
)
from task2view.knowledge.loader import KnowledgeBase
from task2view.knowledge.selector import (
    _NOTATION_LABEL,
    _granularity,
    _instantiate_required_information,
    _score,
    _task_summary,
    _vb_candidates,
    cue_preference_weights,
    match_task_cues,
    task_focus,
)


@dataclass(frozen=True)
class Grain:
    viewpoint_id: str
    unit: str
    nodes: str
    relations: str
    forbid: str

    def prompt(self) -> str:
        return (
            f"VIEWPOINT GRAIN ({self.viewpoint_id}), unit={self.unit}:\n"
            f"- nodes: {self.nodes}\n"
            f"- relations: {self.relations}\n"
            f"- do not: {self.forbid}"
        )


@dataclass(frozen=True)
class Correspondence:
    role_id: str
    stakeholder_name: str
    concerns: list[str]
    task_concerns: list[str]
    preferred_viewpoints: list[str]
    phrases: list[str]
    task: str
    task_focus: str
    viewpoint_id: str
    view_type: str
    notation: str
    diagram_language: str
    diagram_language_rule: str
    granularity: str
    purpose: str
    grain: Grain
    ranked: list[RankedCandidate]
    vb_candidates: list[dict[str, Any]]
    dropped_beyond_views: list[str]
    unanswered_concerns: list[str]
    decided_by: str = "catalog"

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "role_id": self.role_id,
            "stakeholder_name": self.stakeholder_name,
            "viewpoint_id": self.viewpoint_id,
            "view_type": self.view_type,
            "task_focus": self.task_focus,
            "concerns": list(self.concerns),
            "task_concerns": list(self.task_concerns),
            "preferred_viewpoints": list(self.preferred_viewpoints),
            "phrases": list(self.phrases),
            "task": self.task,
            "purpose": self.purpose,
            "diagram_language": self.diagram_language,
            "diagram_language_rule": self.diagram_language_rule,
            "unanswered_concerns": list(self.unanswered_concerns),
            "decided_by": self.decided_by,
            "grain": asdict(self.grain),
            "ranked": [row.model_dump(mode="json") for row in self.ranked[:12]],
        }
        return payload

    def candidate_ids(self, limit: int = 8) -> list[str]:
        ids: list[str] = []
        for row in self.ranked:
            if row.viewpoint_id not in ids:
                ids.append(row.viewpoint_id)
            if len(ids) >= limit:
                break
        return ids


def bind_grain(
    knowledge: KnowledgeBase,
    viewpoint_id: str | None,
    view_type: str | None = None,
) -> Grain:
    raw = knowledge.published_grain(viewpoint_id, view_type)
    label = viewpoint_id or view_type or "default"
    return Grain(
        viewpoint_id=str(label),
        unit=str(raw.get("unit") or "component"),
        nodes=str(raw.get("nodes") or ""),
        relations=str(raw.get("relations") or ""),
        forbid=str(raw.get("forbid") or ""),
    )


def _purpose(viewpoint: dict[str, Any], grain: Grain, focus: str) -> str:
    name = str(viewpoint.get("name") or grain.viewpoint_id)
    return (
        f"{name} for {focus}: {grain.nodes}. "
        f"Relations: {grain.relations}. Do not: {grain.forbid}."
    )


def viewpoints_for_concerns(
    knowledge: KnowledgeBase,
    concerns: list[str],
) -> tuple[list[str], bool]:
    """Viewpoints that frame the concerns the model chose.

    Sorted by how many of those concerns they frame, then by how tightly
    they match, then by catalog order. Phrase cues are not consulted.
    The second value is False when no viewpoint frames any chosen concern;
    the full catalog is returned in that case.
    """
    chosen = [concern for concern in concerns if concern and concern != "general"]
    if not chosen:
        chosen = [concern for concern in concerns if concern]
    order = {viewpoint_id: index for index, viewpoint_id in enumerate(knowledge.viewpoints)}
    scored: list[tuple[int, int, int, str]] = []
    for viewpoint_id, viewpoint in knowledge.viewpoints.items():
        frames = [str(item) for item in viewpoint.get("frames_concerns") or []]
        overlap = [concern for concern in chosen if concern in frames]
        if not overlap:
            continue
        extra = len(set(frames) - set(chosen))
        scored.append((len(overlap), -extra, -order[viewpoint_id], viewpoint_id))
    if not scored:
        return list(knowledge.viewpoints), False
    scored.sort(reverse=True)
    return [viewpoint_id for _, _, _, viewpoint_id in scored], True


def _rank(
    role_id: str,
    task: str,
    knowledge: KnowledgeBase,
) -> tuple[list[RankedCandidate], list[str], list[str], list[str], list[dict[str, Any]], list[str]]:
    profile = knowledge.stakeholder(role_id)
    task_concerns, preferred, phrases = match_task_cues(task, knowledge)
    weights = cue_preference_weights(task, knowledge)
    if not task_concerns:
        task_concerns = knowledge.primary_concern(role_id)
    vb_rows, dropped = _vb_candidates(role_id, knowledge)
    vb_by_viewpoint = {row["viewpoint_id"]: row for row in vb_rows if row["viewpoint_id"]}
    required = set(profile.get("viewpoints", {}).get("required", []))
    optional = set(profile.get("viewpoints", {}).get("optional", []))
    pool = set(vb_by_viewpoint) | required | optional | set(preferred)
    ranked: list[RankedCandidate] = []
    for viewpoint_id in pool:
        viewpoint = knowledge.viewpoint(viewpoint_id)
        vb = vb_by_viewpoint.get(viewpoint_id)
        score, reasons = _score(
            viewpoint_id,
            vb_rank=int(vb["rank"]) if vb else 0,
            profile_required=required,
            profile_optional=optional,
            preferred=preferred,
            task_concerns=task_concerns,
            frames=list(viewpoint.get("frames_concerns") or []),
            preferred_weights=weights,
        )
        ranked.append(
            RankedCandidate(
                viewpoint_id=viewpoint_id,
                view_type=viewpoint["view_type"],
                vb_column=vb["column"] if vb else None,
                vb_level=vb["level"] if vb else None,
                score=score,
                reasons=reasons,
            )
        )
    ranked.sort(
        key=lambda item: (
            -item.score,
            preferred.index(item.viewpoint_id) if item.viewpoint_id in preferred else 99,
            item.viewpoint_id,
        )
    )
    blob = " ".join(phrases).casefold()
    if "integration test" in blob:
        for row in ranked:
            if row.viewpoint_id == "cnc-runtime":
                row.score += 4.0
                row.reasons.append("integration-test task keeps a C&C runtime view")
        ranked.sort(
            key=lambda item: (
                -item.score,
                preferred.index(item.viewpoint_id) if item.viewpoint_id in preferred else 99,
                item.viewpoint_id,
            )
        )
    if not ranked:
        raise PipelineError(f"No candidate viewpoints for stakeholder {role_id}")
    return ranked, task_concerns, preferred, phrases, vb_rows, dropped


def select_correspondence(
    role_id: str,
    task: str,
    knowledge: KnowledgeBase,
    *,
    goal: str | None = None,
    extra_concerns: list[str] | None = None,
    preferred_language: str | None = None,
    viewpoint_id: str | None = None,
) -> Correspondence:
    """Bind a viewpoint's published grain.

    With no viewpoint_id, the catalog rank chooses.
    A viewpoint_id that exists in the catalog is the caller's choice and wins
    even when that id was not the rank winner.
    When `extra_concerns` is given, that list is the concern set (the
    interpretation agent's choice). Cue phrases are not added on top.
    With no `extra_concerns`, cue matches on `task` are the concern set.
    """
    profile = knowledge.stakeholder(role_id)
    ranked, task_concerns, preferred, phrases, vb_rows, dropped = _rank(role_id, task, knowledge)
    winner_id = ranked[0].viewpoint_id
    decided_by = "catalog"
    if viewpoint_id and viewpoint_id in knowledge.viewpoints:
        winner_id = viewpoint_id
        decided_by = "model"
    viewpoint = knowledge.viewpoint(winner_id)
    view_type = viewpoint["view_type"]
    if view_type not in ALLOWED_VIEW_TYPES:
        raise PipelineError(f"Viewpoint {winner_id} has unknown view_type {view_type}")
    formality = (
        profile.get("presentation", {}).get("notation")
        or viewpoint.get("default_notation")
        or "semi-formal"
    )
    if preferred_language:
        preferred_name, preferred_source = preferred_language, "request"
    else:
        preferred_name, preferred_source = None, None
    language_decision = knowledge.explain_language(
        view_type,
        preferred=preferred_name,
        preferred_source=preferred_source,
        formality=formality,
        viewpoint_default=viewpoint.get("default_diagram_language"),
    )
    language = language_decision["language"]
    focus = task_focus(task, phrases)
    grain = bind_grain(knowledge, winner_id, view_type)
    catalog = knowledge.catalog_concerns()
    if extra_concerns is not None:
        concerns = []
        for concern in extra_concerns:
            if concern in catalog and concern not in concerns:
                concerns.append(concern)
        task_concerns = list(concerns)
    else:
        concerns = [concern for concern in task_concerns if concern in catalog]
    if not concerns:
        concerns = knowledge.primary_concern(role_id)
        task_concerns = list(concerns)
    framed = set(viewpoint.get("frames_concerns") or [])
    unanswered = [c for c in concerns if c not in framed and c != "general"]
    return Correspondence(
        role_id=role_id,
        stakeholder_name=str(profile.get("name") or role_id),
        concerns=concerns,
        task_concerns=task_concerns,
        preferred_viewpoints=preferred,
        phrases=phrases,
        task=task,
        task_focus=focus,
        viewpoint_id=winner_id,
        view_type=view_type,
        notation=_NOTATION_LABEL.get(view_type, str(viewpoint["name"])),
        diagram_language=language,
        diagram_language_rule=language_decision["rule"],
        granularity=_granularity(viewpoint, profile),
        purpose=_purpose(viewpoint, grain, focus),
        grain=grain,
        ranked=ranked,
        vb_candidates=vb_rows,
        dropped_beyond_views=dropped,
        unanswered_concerns=unanswered,
        decided_by=decided_by,
    )


def with_viewpoint(
    correspondence: Correspondence,
    viewpoint_id: str,
    knowledge: KnowledgeBase,
    *,
    preferred_language: str | None = None,
    goal: str | None = None,
) -> Correspondence:
    """Switch to viewpoint_id when it is a catalog id. Unknown ids stay put."""
    if viewpoint_id == correspondence.viewpoint_id:
        return correspondence
    return select_correspondence(
        correspondence.role_id,
        correspondence.task,
        knowledge,
        goal=goal,
        extra_concerns=correspondence.concerns,
        preferred_language=preferred_language or correspondence.diagram_language,
        viewpoint_id=viewpoint_id,
    )


def spec_from_correspondence(
    request: NormalizedRequest,
    correspondence: Correspondence,
    knowledge: KnowledgeBase,
) -> ViewSpecification:
    required = _instantiate_required_information(
        correspondence.viewpoint_id,
        correspondence.task_focus,
        knowledge,
    )
    return ViewSpecification(
        request_id=request.request_id,
        stakeholder=correspondence.role_id,
        task_summary=_task_summary(request.task.description),
        architectural_concerns=correspondence.concerns,
        selected_view=SelectedView(
            view_type=correspondence.view_type,
            notation=correspondence.notation,
            diagram_language=correspondence.diagram_language,
            diagram_language_rule=correspondence.diagram_language_rule,
            granularity=correspondence.granularity,
            purpose=correspondence.purpose,
            viewpoint_id=correspondence.viewpoint_id,
            grain_unit=correspondence.grain.unit,
        ),
        required_information=required,
        unanswered_concerns=correspondence.unanswered_concerns,
        declared_gaps=list(correspondence.unanswered_concerns),
        selection_trace=SelectionTrace(
            method=(
                "model-viewpoint"
                if correspondence.decided_by == "model"
                else "iso-42010-correspondence"
            ),
            vb_candidates=correspondence.vb_candidates,
            task_concerns=correspondence.task_concerns,
            preferred_viewpoints=correspondence.preferred_viewpoints,
            ranked=correspondence.ranked,
            dropped_beyond_views=correspondence.dropped_beyond_views,
        ),
    )
