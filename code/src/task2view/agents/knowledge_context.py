"""Compact knowledge-base text for viewpoint-planning agents."""

from __future__ import annotations

from task2view.knowledge.loader import KnowledgeBase


# What each concern id means for the view. Ids with no entry still appear,
# marked as undefined, so the model is not choosing a bare label.
CONCERN_MEANING = {
    "maintainability": "where a change lives: the modules or types that own the feature and how they are arranged",
    "control-flow": "the order of a request: which part calls which when the feature runs",
    "functional-suitability": "whether the feature does the job the stakeholder must test or check",
    "connectivity": "which parts communicate, and the connectors between them",
    "performance": "where time or load is spent while the feature runs",
    "deployment": "where the system runs: artifacts, hosts, and environments",
    "reliability": "what must keep working, and what fails if a host or dependency fails",
    "security": "trust boundaries, and where authentication or authorization happens",
    "data-protection": "where personal or sensitive data is stored or passed",
    "compatibility": "interfaces and contracts that other systems depend on",
    "flexibility": "where the design can still change, and which decisions lock it",
    "traceability": "which source types implement an architectural part",
    "general": "a broad picture of the system, not one mechanism",
    "interaction-capability": "who uses the system and what they can do with it",
}


def concern_meanings(knowledge: KnowledgeBase) -> str:
    """Concern ids and meanings only. Viewpoint names are withheld until Phase 3."""
    lines = [
        "Closed catalog. Return only these ids.",
        "Each line is the fact that concern asks the repository to reveal.",
    ]
    for concern_id in sorted(knowledge.catalog_concerns()):
        meaning = CONCERN_MEANING.get(concern_id, "no definition in the catalog")
        lines.append(f"- {concern_id}: {meaning}")
    return "\n".join(lines)


def concern_catalog(knowledge: KnowledgeBase) -> str:
    """Every concern id the model may return, with its meaning and framing viewpoints."""
    framed_by: dict[str, list[str]] = {}
    for viewpoint_id, viewpoint in knowledge.viewpoints.items():
        for concern_id in viewpoint.get("frames_concerns") or []:
            framed_by.setdefault(str(concern_id), []).append(viewpoint_id)
    lines = [
        "Concern ids. Choose only these. Each line is what the id means.",
        "A concern with no viewpoint is still valid; a later step marks it uncovered.",
    ]
    for concern_id in sorted(knowledge.catalog_concerns()):
        meaning = CONCERN_MEANING.get(concern_id, "no definition in the catalog")
        framed = ", ".join(framed_by.get(concern_id) or [])
        if framed:
            lines.append(f"- {concern_id}: {meaning}. A view that can show it: {framed}.")
        else:
            lines.append(f"- {concern_id}: {meaning}. No current viewpoint frames this.")
    return "\n".join(lines)


def role_catalog(knowledge: KnowledgeBase) -> str:
    aliases_for: dict[str, list[str]] = {}
    for alias, role_id in knowledge.aliases.items():
        aliases_for.setdefault(role_id, []).append(alias)
    lines = ["Canonical roles. canonical_role must be one of these ids."]
    for role_id, profile in knowledge.stakeholders.items():
        tasks = profile.get("tasks") or []
        duty = ""
        if tasks and isinstance(tasks[0], dict):
            duty = " ".join(str(tasks[0].get("description") or "").split())
        aliases = ", ".join(sorted(aliases_for.get(role_id) or []))
        line = f"- {role_id}: {profile.get('name')}"
        if duty:
            line += f". Typical work: {duty}"
        if aliases:
            line += f". The user may say: {aliases}"
        lines.append(line)
    return "\n".join(lines)


def task_cue_block(concerns: list[str], preferred: list[str], phrases: list[str]) -> str:
    if not phrases and not preferred:
        return "No catalog phrase matched the text. Do not invent a viewpoint from a missing phrase."
    return (
        f"Phrases found in the text: {phrases}\n"
        f"Concerns those phrases suggest: {concerns}\n"
        f"Viewpoints those phrases mention: {preferred}\n"
        "These are hints from wording. The concerns chosen for this goal outrank them."
    )


def viewpoint_catalog(knowledge: KnowledgeBase) -> str:
    lines = ["Viewpoint catalog (id | view_type | grain unit | concerns):"]
    for vid, vp in knowledge.viewpoints.items():
        concerns = ", ".join(vp.get("frames_concerns") or [])
        grain = knowledge.published_grain(vid, vp.get("view_type"))
        lines.append(
            f"- {vid}: view_type={vp.get('view_type')} "
            f"unit={grain.get('unit')} "
            f"nodes={grain.get('nodes')} "
            f"diagram={vp.get('default_diagram_language')} concerns=[{concerns}]"
        )
    return "\n".join(lines)


def grain_summaries(knowledge: KnowledgeBase, viewpoint_ids: list[str]) -> str:
    blocks = [knowledge.grain_prompt(vid, None) for vid in viewpoint_ids]
    return "\n\n".join(blocks)


def stakeholder_view_hints(
    knowledge: KnowledgeBase,
    role_id: str | None,
    selected_viewpoint_id: str | None = None,
    chosen: list[str] | None = None,
    allowed: list[str] | None = None,
) -> str:
    if not role_id or role_id not in knowledge.stakeholders:
        return "No stakeholder profile matched yet."
    profile = knowledge.stakeholders[role_id]
    background = ", ".join(
        item["id"] if isinstance(item, dict) else str(item) for item in profile.get("concerns") or []
    )
    chosen_line = ", ".join(chosen or []) or "(none yet)"
    if selected_viewpoint_id and selected_viewpoint_id in knowledge.viewpoints:
        framed = knowledge.viewpoint(selected_viewpoint_id).get("frames_concerns") or []
        return (
            f"Profile {role_id} ({profile.get('name')})\n"
            f"selected viewpoint: {selected_viewpoint_id}\n"
            f"this viewpoint frames: {framed}\n"
            f"concerns chosen for this goal: {chosen_line}\n"
            f"other concerns this role sometimes has, not automatically in scope: {background}\n"
            "Ask only about concerns this viewpoint frames. A question is one fact the view must show."
        )
    if allowed:
        return (
            f"Stakeholder: {role_id} ({profile.get('name')}).\n"
            f"Concerns already chosen: {chosen_line}.\n"
            "Choose the viewpoint that answers the questions. "
            "Do not choose the viewpoint this role usually receives."
        )
    vp = profile.get("viewpoints") or {}
    return (
        f"Profile {role_id} ({profile.get('name')})\n"
        f"concerns chosen for this goal: {chosen_line}\n"
        f"other concerns this role sometimes has, not automatically in scope: {background}\n"
        f"required viewpoints: {vp.get('required')}\n"
        f"optional viewpoints: {vp.get('optional')}\n"
        f"Table 9.1 row: {knowledge.vb_table.get('rows', {}).get(role_id)}"
    )


def ranked_catalog(knowledge: KnowledgeBase, viewpoint_ids: list[str]) -> str:
    lines = ["Ranked catalog (only these viewpoint ids are allowed):"]
    for vid in viewpoint_ids:
        if vid not in knowledge.viewpoints:
            continue
        vp = knowledge.viewpoints[vid]
        grain = knowledge.published_grain(vid, vp.get("view_type"))
        lines.append(
            f"- {vid}: view_type={vp.get('view_type')} "
            f"unit={grain.get('unit')} nodes={grain.get('nodes')}"
        )
    return "\n".join(lines)


def style_catalog(knowledge: KnowledgeBase) -> str:
    layers = (knowledge.architectural_styles or {}).get("layers") or []
    if not layers:
        return "No architectural style aliases loaded."
    lines = ["Architectural layer aliases (group names must match these packages):"]
    for layer in layers:
        aliases = ", ".join(layer.get("aliases") or [])
        lines.append(f"- {layer.get('name')}: aliases=[{aliases}]")
    return "\n".join(lines)


def question_templates(knowledge: KnowledgeBase, viewpoint_ids: list[str], focus: str) -> str:
    lines = [
        "Checklist this view already owes. Turn a line into a question only when it names this target.",
        "Do not paste a line unchanged, and do not add a question for a concern this viewpoint does not frame.",
    ]
    for vid in viewpoint_ids:
        templates = knowledge.required_information.get(vid) or []
        if not templates:
            continue
        lines.append(f"[{vid}]")
        for item in templates:
            lines.append("- " + item["need"].format(task_focus=focus or "the task"))
    return "\n".join(lines)
