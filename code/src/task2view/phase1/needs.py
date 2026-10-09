"""Phase 1 — information needs, subjects and detail level (ADR-006 D1).

The agent reads only the goal. It types what the stakeholder must see with the
closed needs vocabulary and copies the enumerated subjects verbatim. Everything
it returns is checked against the goal text: a need whose evidence is not in the
goal, or a subject the goal does not contain, is dropped and recorded. The
detail level is computed from the verified needs and subjects, not chosen by
the model and not from the length of the text.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from task2view.agents.runtime import AgentRuntime
from task2view.knowledge.catalog import Catalog, load_catalog
from task2view.phase3.selection import GoalSubject, SelectionInput
from task2view.prompts import load_prompt


class NeedEvidence(BaseModel):
    need: str
    evidence: str
    salience: Literal["primary", "secondary"] = "primary"


class NeedProfile(BaseModel):
    goal: str
    role_label: str = ""
    role: str | None = None
    target: str = ""
    needs: list[NeedEvidence] = Field(default_factory=list)
    subjects: list[GoalSubject] = Field(default_factory=list)
    quality_attributes: list[str] = Field(default_factory=list)
    detail_level: str = "feature"
    dropped: list[str] = Field(default_factory=list)

    def selection_input(self) -> SelectionInput:
        return SelectionInput(
            needs=[n.need for n in self.needs if n.salience == "primary"],
            secondary_needs=[n.need for n in self.needs if n.salience == "secondary"],
            subjects=self.subjects,
            role=self.role,
            detail_level=self.detail_level,
        )


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s/-]", " ", text.casefold()).split())


def detail_level(need_count: int, subject_count: int, rule: dict) -> str:
    """overview / feature / detailed from the verified profile, not from wording or length.

    detailed: the request enumerates specific items (subjects) to understand.
    feature:  it asks for several kinds of information about the parts.
    overview: it asks for one kind of information and enumerates nothing.
    Thresholds come from the catalog (needs.yaml `detail_levels`).
    """
    if subject_count >= rule["detailed_min_subjects"]:
        return "detailed"
    if need_count >= rule["feature_min_needs"] or subject_count >= 1:
        return "feature"
    return "overview"


def _render_needs(catalog: Catalog) -> str:
    return "\n".join(
        f"- {n.id}: {n.description}. Words: {', '.join(n.cues)}" for n in catalog.needs.values()
    )


def _render_roles(catalog: Catalog) -> str:
    return "\n".join(f"- {r.id}: {r.label} (also called: {', '.join(r.aliases)})" for r in catalog.roles.values())


def extract_needs(goal: str, runtime: AgentRuntime, *, catalog: Catalog | None = None) -> NeedProfile:
    catalog = catalog or load_catalog()
    goal = goal.strip()
    raw = runtime.complete_json(load_prompt("phase1_interpret").render(
        goal=goal,
        needs=_render_needs(catalog),
        roles=_render_roles(catalog),
        qualities=", ".join(catalog.quality_attributes),
    ), purpose="phase1")
    return validate_needs(goal, raw, catalog)


def validate_needs(goal: str, raw: dict, catalog: Catalog) -> NeedProfile:
    """Keep only what the goal text supports; record everything dropped."""
    norm_goal = _norm(goal)
    dropped: list[str] = []

    needs: list[NeedEvidence] = []
    for row in raw.get("needs") or []:
        need = str((row or {}).get("need") or "").strip()
        evidence = str((row or {}).get("evidence") or "").strip()
        if need not in catalog.needs:
            dropped.append(f"need {need!r}: not in the catalog")
        elif not evidence or _norm(evidence) not in norm_goal:
            dropped.append(f"need {need!r}: evidence {evidence!r} is not in the goal")
        elif need not in {n.need for n in needs}:
            salience = str((row or {}).get("salience") or "primary").strip().lower()
            if salience not in {"primary", "secondary"}:
                dropped.append(f"need {need!r}: salience {salience!r} unknown, treated as primary")
                salience = "primary"
            needs.append(NeedEvidence(need=need, evidence=evidence, salience=salience))

    subjects: list[GoalSubject] = []
    for row in raw.get("subjects") or []:
        text = str((row or {}).get("text") or "").strip()
        if not text or _norm(text) not in norm_goal:
            dropped.append(f"subject {text!r}: not in the goal")
            continue
        subject_needs = [n for n in (row.get("needs") or []) if n in catalog.needs]
        subjects.append(GoalSubject(text=text, needs=subject_needs))

    target = str(raw.get("target") or "").strip()
    if target and _norm(target) not in norm_goal:
        dropped.append(f"target {target!r}: not in the goal")
        target = ""
    label = str(raw.get("role_label") or "").strip()
    role = raw.get("role")
    role = role if role in catalog.roles else catalog.resolve_role(label)
    qualities = [q for q in raw.get("quality_attributes") or [] if q in catalog.quality_attributes]
    return NeedProfile(
        goal=goal,
        role_label=label,
        role=role,
        target=target,
        needs=needs,
        subjects=subjects,
        quality_attributes=qualities,
        detail_level=detail_level(sum(n.salience == "primary" for n in needs), len(subjects), catalog.detail_rule),
        dropped=dropped,
    )
