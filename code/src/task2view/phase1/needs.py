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

PROMPT = """You are the Stakeholder-Task Interpretation Agent.

GOAL
Say what this stakeholder must SEE to do their task, using a closed vocabulary of information needs.
A later, deterministic step picks the architecture views from these needs, so every need you list becomes part of a diagram.

INPUTS
1. USER DESCRIPTION: the only text you may interpret.
2. INFORMATION NEEDS: the only legal need ids, each with what it means and words people use for it.
3. ROLES: the only legal role ids.
4. QUALITY ATTRIBUTES: the only legal quality ids.

INFORMATION NEEDS
{needs}

ROLES
{roles}

QUALITY ATTRIBUTES
{qualities}

USER DESCRIPTION
{goal}

DECISION
- role_label: the words they used for themselves. role: one role id, or null when no id fits.
- needs: every information need the description asks for, each with "evidence": the exact words from the description that ask for it.
  Reason: every need becomes part of a diagram, so a need nobody asked for adds a diagram nobody wanted. Copy the words exactly.
  Use the meanings in INFORMATION NEEDS, not word matching:
  - A need is information the person asks to SEE. Words that only name the thing they will work on, or describe their situation, are not a need.
  - Structural needs are about which parts exist and how they relate. Behavioural needs (interaction-order, process-flow, lifecycle, actors-goals) are about what happens:
    the order of steps, the flow of a process, the states something goes through, or who uses the system for what.
    List a behavioural need only when the description asks about that dynamic aspect.
  - People who use the system are actors (actors-goals); software parts that work together are collaboration.
  Give each need a "salience":
  - "primary": the request is about this. It states it as something they need to understand, identify, or see.
  - "secondary": it is mentioned in passing, gives context, or is only implied by a primary need.
  Reason: only primary needs may add a diagram. A secondary need is answered only if a diagram chosen for a primary need already shows it.
- subjects: the items the description enumerates as part of what they want to understand (for example a list of sub-functions, data items, or cases), copied exactly, each with the need ids it belongs to.
  Reason: each subject must appear in a view, so the details of a long description are not lost.
  The system, the feature being changed, and the stakeholder are not subjects. A description that enumerates nothing has no subjects.
- quality_attributes: quality ids the description stresses, or an empty list. They do not choose diagrams.

OUTPUT
Return only this JSON.
{{
  "role_label": "label as the user said it",
  "role": "one role id, or null",
  "needs": [{{"need": "need id", "evidence": "exact words", "salience": "primary or secondary"}}],
  "subjects": [{{"text": "exact words", "needs": ["need id"]}}],
  "quality_attributes": []
}}
"""


class NeedEvidence(BaseModel):
    need: str
    evidence: str
    salience: Literal["primary", "secondary"] = "primary"


class NeedProfile(BaseModel):
    goal: str
    role_label: str = ""
    role: str | None = None
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
    raw = runtime.complete_json(
        PROMPT.format(
            needs=_render_needs(catalog),
            roles=_render_roles(catalog),
            qualities=", ".join(catalog.quality_attributes),
            goal=goal,
        )
    )
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

    label = str(raw.get("role_label") or "").strip()
    role = raw.get("role")
    role = role if role in catalog.roles else catalog.resolve_role(label)
    qualities = [q for q in raw.get("quality_attributes") or [] if q in catalog.quality_attributes]
    return NeedProfile(
        goal=goal,
        role_label=label,
        role=role,
        needs=needs,
        subjects=subjects,
        quality_attributes=qualities,
        detail_level=detail_level(sum(n.salience == "primary" for n in needs), len(subjects), catalog.detail_rule),
        dropped=dropped,
    )
