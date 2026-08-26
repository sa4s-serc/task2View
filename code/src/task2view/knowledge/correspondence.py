"""ISO 42010 correspondence kernel.

stakeholder × concerns × task → catalog viewpoint → published grain.

No LLM. No repository. Both the legacy selector and the agentic path call
this so grain cannot drift between them.
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
from task2view.phase2.selector import (
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
    granularity: str
    purpose: str
    grain: Grain
    ranked: list[RankedCandidate]
    vb_candidates: list[dict[str, Any]]
    dropped_beyond_views: list[str]
    unanswered_concerns: list[str]

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
            "unanswered_concerns": list(self.unanswered_concerns),
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


def _rank(
    role_id: str,
    task: str,
    knowledge: KnowledgeBase,
) -> tuple[list[RankedCandidate], list[str], list[str], list[str], list[dict[str, Any]], list[str]]:
    profile = knowledge.stakeholder(role_id)
    task_concerns, preferred, phrases = match_task_cues(task, knowledge)
    weights = cue_preference_weights(task, knowledge)
    if not task_concerns:
        task_concerns = [c["id"] for c in profile.get("concerns", [])]
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
    """Rank catalog viewpoints and bind the winner's published grain."""
    profile = knowledge.stakeholder(role_id)
    ranked, task_concerns, preferred, phrases, vb_rows, dropped = _rank(role_id, task, knowledge)
    allowed = {row.viewpoint_id for row in ranked}
    winner_id = ranked[0].viewpoint_id
    if viewpoint_id and viewpoint_id in allowed:
        winner_id = viewpoint_id
    viewpoint = knowledge.viewpoint(winner_id)
    view_type = viewpoint["view_type"]
    if view_type not in ALLOWED_VIEW_TYPES:
        raise PipelineError(f"Viewpoint {winner_id} has unknown view_type {view_type}")
    formality = (
        profile.get("presentation", {}).get("notation")
        or viewpoint.get("default_notation")
        or "semi-formal"
    )
    from_goal = knowledge.detect_language(goal or task)
    language = knowledge.choose_language(
        view_type,
        preferred=preferred_language or from_goal,
        formality=formality,
        viewpoint_default=viewpoint.get("default_diagram_language"),
    )
    focus = task_focus(task, phrases)
    grain = bind_grain(knowledge, winner_id, view_type)
    concerns: list[str] = []
    for item in profile.get("concerns", []):
        cid = item["id"] if isinstance(item, dict) else str(item)
        if cid not in concerns:
            concerns.append(cid)
    for concern in list(task_concerns) + list(extra_concerns or []):
        if concern not in concerns:
            concerns.append(concern)
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
        granularity=_granularity(viewpoint, profile),
        purpose=_purpose(viewpoint, grain, focus),
        grain=grain,
        ranked=ranked,
        vb_candidates=vb_rows,
        dropped_beyond_views=dropped,
        unanswered_concerns=unanswered,
    )


def with_viewpoint(
    correspondence: Correspondence,
    viewpoint_id: str,
    knowledge: KnowledgeBase,
    *,
    preferred_language: str | None = None,
    goal: str | None = None,
) -> Correspondence:
    """Keep the ranked pool; switch grain if viewpoint_id is a ranked candidate."""
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
            granularity=correspondence.granularity,
            purpose=correspondence.purpose,
            viewpoint_id=correspondence.viewpoint_id,
            grain_unit=correspondence.grain.unit,
        ),
        required_information=required,
        unanswered_concerns=correspondence.unanswered_concerns,
        declared_gaps=list(correspondence.unanswered_concerns),
        selection_trace=SelectionTrace(
            method="iso-42010-correspondence",
            vb_candidates=correspondence.vb_candidates,
            task_concerns=correspondence.task_concerns,
            preferred_viewpoints=correspondence.preferred_viewpoints,
            ranked=correspondence.ranked,
            dropped_beyond_views=correspondence.dropped_beyond_views,
        ),
    )
