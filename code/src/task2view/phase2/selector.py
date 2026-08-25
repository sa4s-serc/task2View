"""Phase 2: automate V&B 'Choosing the Views' (steps 1–3).

Step 1 — Candidate view list from Table 9.1.
Step 2 — Combine: drop documentation-beyond-views; union with the
          stakeholder profile's required viewpoints (task-specific
          additions such as scenario/control-flow, which Table 9.1
          does not list as columns).
Step 3 — Prioritize: rank by V&B detail, profile requirement, and
          inspectable task cues. Cap at preferences.max_views.

No repository is read. Conditional applicability is recorded, not evaluated.
"""

from __future__ import annotations

import re
from typing import Any

from task2view.contracts.models import (
    ALLOWED_VIEW_TYPES,
    NormalizedRequest,
    PipelineError,
    RankedCandidate,
    RequiredInformation,
    SelectedView,
    SelectionTrace,
    ViewSpecification,
)
from task2view.contracts.validate import validate_artifact
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_STOP = {
    "a",
    "an",
    "and",
    "be",
    "can",
    "design",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "need",
    "of",
    "on",
    "so",
    "that",
    "the",
    "to",
    "understand",
    "want",
    "with",
}

_GRANULARITY = {
    "high": "system_or_context_level",
    "medium": "component_or_service_level",
    "low": "class_or_code_level",
}

_NOTATION_LABEL = {
    "sequence_view": "UML Sequence Diagram",
    "component_view": "Component Diagram",
    "deployment_view": "Deployment Diagram",
    "class_view": "Class Diagram",
    "state_view": "State Diagram",
    "dataflow_view": "Data Flow Diagram",
    "context_view": "System Context Diagram",
}


def _tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in _TOKEN.finditer(text)]


def match_task_cues(task: str, knowledge: KnowledgeBase) -> tuple[list[str], list[str], list[str]]:
    lowered = task.lower()
    concerns: list[str] = []
    preferred: list[str] = []
    phrases: list[str] = []
    for cue in knowledge.task_cues:
        hits = [p for p in cue["phrases"] if p in lowered]
        if not hits:
            continue
        phrases.extend(hits)
        for concern in cue["concerns"]:
            if concern not in concerns:
                concerns.append(concern)
        for viewpoint in cue["prefer_viewpoints"]:
            if viewpoint not in preferred:
                preferred.append(viewpoint)
    return concerns, preferred, phrases


_GENERIC_FOCUS = {
    "processed",
    "processing",
    "sequence",
    "control flow",
    "call chain",
    "runtime interaction",
    "execution order",
    "how a request",
    "how a user",
}


def task_focus(task: str, matched_phrases: list[str]) -> str:
    tokens = _tokens(task)
    subject = re.split(r"\bso (?:that )?i can\b", task, flags=re.I, maxsplit=1)[0]
    subject_l = subject.lower()
    if matched_phrases:
        in_subject = [p for p in matched_phrases if p in subject_l and p not in _GENERIC_FOCUS]
        pool = in_subject or [p for p in matched_phrases if p not in _GENERIC_FOCUS] or matched_phrases
        phrase = min(pool, key=lambda p: subject_l.find(p) if p in subject_l else task.lower().find(p))
        phrase_tokens = _tokens(phrase)
        if phrase_tokens:
            try:
                idx = next(i for i, tok in enumerate(tokens) if tokens[i : i + len(phrase_tokens)] == phrase_tokens)
            except StopIteration:
                idx = -1
            if idx >= 0:
                start = idx
                if start > 0 and tokens[start - 1] not in _STOP:
                    start -= 1
                end = idx + len(phrase_tokens)
                window = [t for t in tokens[start:end] if t not in _STOP]
                if window:
                    return " ".join(window)
    content = [t for t in tokens if t not in _STOP]
    return " ".join(content[:6]) or "the stated task"


def _task_summary(task: str) -> str:
    first = re.split(r"[.!?]", task.strip(), maxsplit=1)[0].strip()
    if first.endswith(","):
        first = first[:-1]
    if len(first) > 160:
        return first[:157].rstrip() + "..."
    return first


def _vb_candidates(role_id: str, knowledge: KnowledgeBase) -> tuple[list[dict[str, Any]], list[str]]:
    table = knowledge.vb_table
    row = table["rows"].get(role_id)
    if not row:
        return [], []
    levels: dict[str, Any] = table["levels"]
    candidates: list[dict[str, Any]] = []
    dropped: list[str] = []
    for column in table["columns"]:
        level = row.get(column["id"])
        if not level:
            continue
        entry = {
            "column": column["id"],
            "vb_name": column["vb_name"],
            "viewpoint_id": column.get("viewpoint"),
            "level": level,
            "rank": levels[level]["rank"],
            "beyond_views": bool(column.get("beyond_views")),
        }
        if entry["beyond_views"] or not entry["viewpoint_id"]:
            dropped.append(column["id"])
            continue
        candidates.append(entry)
    return candidates, dropped


def _score(
    viewpoint_id: str,
    *,
    vb_rank: int,
    profile_required: set[str],
    profile_optional: set[str],
    preferred: list[str],
    task_concerns: list[str],
    frames: list[str],
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = float(vb_rank)
    if vb_rank:
        reasons.append(f"V&B detail rank {vb_rank}")
    if viewpoint_id in preferred:
        score += 5
        reasons.append("task-cue preferred viewpoint")
    if viewpoint_id in profile_required:
        score += 2
        reasons.append("stakeholder required viewpoint")
    elif viewpoint_id in profile_optional:
        score += 1
        reasons.append("stakeholder optional viewpoint")
    overlap = [c for c in frames if c in task_concerns]
    if overlap:
        score += len(overlap)
        reasons.append("frames task concerns: " + ", ".join(overlap))
    return score, reasons


def _granularity(viewpoint: dict[str, Any], profile: dict[str, Any]) -> str:
    raw = viewpoint.get("default_granularity") or profile.get("presentation", {}).get("granularity") or "medium"
    if raw in _GRANULARITY:
        return _GRANULARITY[raw]
    return str(raw)


def _instantiate_required_information(
    viewpoint_id: str,
    focus: str,
    knowledge: KnowledgeBase,
) -> list[RequiredInformation]:
    templates = knowledge.required_information.get(viewpoint_id)
    if not templates:
        raise PipelineError(f"No required_information template for viewpoint {viewpoint_id}")
    items: list[RequiredInformation] = []
    for template in templates:
        items.append(
            RequiredInformation(
                id=f"RI-{template['id_suffix']}",
                need=template["need"].format(task_focus=focus),
            )
        )
    return items


def identify_view(
    request: NormalizedRequest,
    *,
    knowledge: KnowledgeBase | None = None,
) -> ViewSpecification:
    knowledge = knowledge or load_knowledge()
    role_id = request.stakeholder.role
    profile = knowledge.stakeholder(role_id)
    task = request.task.description
    task_concerns, preferred, phrases = match_task_cues(task, knowledge)
    if not task_concerns:
        task_concerns = [c["id"] for c in profile.get("concerns", [])]
    focus = task_focus(task, phrases)

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

    winner = ranked[0]
    viewpoint = knowledge.viewpoint(winner.viewpoint_id)
    view_type = viewpoint["view_type"]
    if view_type not in ALLOWED_VIEW_TYPES:
        raise PipelineError(f"Viewpoint {winner.viewpoint_id} has unknown view_type {view_type}")

    formality = profile.get("presentation", {}).get("notation") or viewpoint.get("default_notation") or "semi-formal"
    from_goal = knowledge.detect_language(request.goal)
    language = knowledge.choose_language(
        view_type,
        preferred=request.preferences.diagram_language or from_goal,
        formality=formality,
        viewpoint_default=viewpoint.get("default_diagram_language"),
    )
    granularity = _granularity(viewpoint, profile)
    purpose = (
        f"{viewpoint['name']}: show the information the {profile['name']} needs "
        f"about {focus}."
    )
    concerns = []
    for item in profile.get("concerns", []):
        if item["id"] not in concerns:
            concerns.append(item["id"])
    for concern in task_concerns:
        if concern not in concerns:
            concerns.append(concern)

    framed = set(viewpoint.get("frames_concerns") or [])
    unanswered_concerns = [c for c in concerns if c not in framed and c != "general"]

    spec = ViewSpecification(
        request_id=request.request_id,
        stakeholder=role_id,
        task_summary=_task_summary(task),
        architectural_concerns=concerns,
        selected_view=SelectedView(
            view_type=view_type,
            notation=_NOTATION_LABEL.get(view_type, viewpoint["name"]),
            diagram_language=language,
            granularity=granularity,
            purpose=purpose,
            viewpoint_id=winner.viewpoint_id,
        ),
        required_information=_instantiate_required_information(winner.viewpoint_id, focus, knowledge),
        unanswered_concerns=unanswered_concerns,
        declared_gaps=list(unanswered_concerns),
        selection_trace=SelectionTrace(
            vb_candidates=vb_rows,
            task_concerns=task_concerns,
            preferred_viewpoints=preferred,
            ranked=ranked,
            dropped_beyond_views=dropped,
        ),
    )
    validate_artifact("view_specification", spec)
    if not knowledge.notation_supports(spec.selected_view.diagram_language, spec.selected_view.view_type):
        raise PipelineError("selected diagram_language does not support view_type")
    return spec
