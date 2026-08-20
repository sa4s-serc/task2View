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


def viewpoint_catalog(knowledge: KnowledgeBase) -> str:
    lines = ["Viewpoint catalog (id | view_type | granularity | concerns):"]
    for vid, vp in knowledge.viewpoints.items():
        concerns = ", ".join(vp.get("frames_concerns") or [])
        lines.append(
            f"- {vid}: view_type={vp.get('view_type')} "
            f"granularity={vp.get('default_granularity')} "
            f"diagram={vp.get('default_diagram_language')} concerns=[{concerns}]"
        )
    return "\n".join(lines)


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
