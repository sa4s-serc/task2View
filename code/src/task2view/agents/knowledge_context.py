"""Compact knowledge-base text for viewpoint-planning agents."""

from __future__ import annotations

from task2view.knowledge.loader import KnowledgeBase


def role_catalog(knowledge: KnowledgeBase) -> str:
    lines = ["Known canonical roles and aliases:"]
    for role_id, profile in knowledge.stakeholders.items():
        lines.append(f"- {role_id}: {profile.get('name')}")
    lines.append("Aliases:")
    for alias, role_id in knowledge.aliases.items():
        lines.append(f"- {alias} -> {role_id}")
    return "\n".join(lines)


def task_cue_block(concerns: list[str], preferred: list[str], phrases: list[str]) -> str:
    if not phrases and not preferred:
        return "No phrases from task_cues.yaml matched the profile text."
    return (
        f"matched phrases: {phrases}\n"
        f"concerns: {concerns}\n"
        f"prefer_viewpoints: {preferred}\n"
        "If prefer_viewpoints is non-empty, pick from that list unless the "
        "questions cannot be answered by those viewpoints."
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
    lines = ["Published grain for this stakeholder's catalog viewpoints:"]
    for vid in viewpoint_ids:
        lines.append(knowledge.grain_prompt(vid, None))
        lines.append("")
    return "\n".join(lines).rstrip()


def stakeholder_view_hints(knowledge: KnowledgeBase, role_id: str | None) -> str:
    if not role_id or role_id not in knowledge.stakeholders:
        return "No stakeholder profile matched yet."
    profile = knowledge.stakeholders[role_id]
    vp = profile.get("viewpoints") or {}
    concerns = ", ".join(c["id"] for c in profile.get("concerns") or [])
    return (
        f"Profile {role_id} ({profile.get('name')})\n"
        f"concerns: {concerns}\n"
        f"required viewpoints: {vp.get('required')}\n"
        f"optional viewpoints: {vp.get('optional')}\n"
        f"Table 9.1 row: {knowledge.vb_table.get('rows', {}).get(role_id)}"
    )


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
    lines = ["Required-information templates (seed questions, not a closed list):"]
    for vid in viewpoint_ids:
        templates = knowledge.required_information.get(vid) or []
        if not templates:
            continue
        lines.append(f"[{vid}]")
        for item in templates:
            lines.append("- " + item["need"].format(task_focus=focus or "the task"))
    return "\n".join(lines)
