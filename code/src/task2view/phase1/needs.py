"""Phase 1 — information needs, subjects and detail level (ADR-006 D1).

The agent reads only the goal. It types what the stakeholder must see with the
closed needs vocabulary and copies the enumerated subjects verbatim. Everything
it returns is checked against the goal text: a need whose evidence is not in the
goal, or a subject the goal does not contain, is dropped and recorded. The
detail level is computed from the goal text, not chosen by the model, so
L1/L2/L3 goals map to the same granularity on every run.
"""

from __future__ import annotations

import re

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
- role_label: the words they used for themselves. role: one role id, or null.
- needs: every information need the description asks for, each with "evidence": the exact words from the description that ask for it.
  Reason: every need becomes part of a diagram, so a need the person did not ask for adds a diagram nobody wanted. Copy the words exactly.
  List a need only when the person asks to SEE that information. A word that merely names a thing is not a need:
  "the persistence layer" names what they will change, it does not ask how the system is layered; "the lifecycle of a report" in a question about stored data asks what is stored, not for the report's states;
  "runtime dependencies" or "technologies" in a deployment question are deployment facts, not dependencies between parts of the code.

  Pairs that are easy to confuse:
  - collaboration vs decomposition. "the components involved in <a feature>, their responsibilities" is collaboration: the parts that work together for that feature, each shown with what it does.
    decomposition is only for how the WHOLE system is split into subsystems or modules ("overall organization", "how the system is decomposed").
  - collaboration vs interaction-order. collaboration is which parts work together and through which interfaces. interaction-order is the order of the calls in a scenario.
    "how they interact" in a short request that asks nothing else is collaboration only. "how they interact with each other" asked together with responsibilities, or "how they interact when <something happens>", or "what happens when <invalid or failing case>", is interaction-order as well.
  - collaboration vs actors-goals. People or user roles that use the system ("users that interact with the system", "what each user can do", "how the functionalities are related") are actors-goals, not collaboration.
  - dependencies vs change-impact. "dependencies among them" is dependencies. "which parts may be affected by the change" or "which parts depend on <what I will change>" is change-impact.
  - "integration points" or "interfaces between them" is interface-contract.

  Examples from other systems:
  - "I am a developer. I need to change the checkout feature and understand the components involved, their responsibilities, and how they interact with each other."
    needs: collaboration ("the components involved, their responsibilities"), interaction-order ("how they interact with each other").
  - "I am an operations engineer. I need to move the clinic booking system to a new server and know which artifacts are deployed where and which database drivers it needs."
    needs: deployment ("which artifacts are deployed where"), build-packaging ("artifacts"). The drivers are deployment facts, not dependencies.
  - "I am a product owner. I want to know which kinds of users use the ticketing portal and what each of them can do."
    needs: actors-goals ("which kinds of users use the ticketing portal and what each of them can do").
- subjects: the specific things the description enumerates (for example "refund handling", "payment provider"), copied exactly, each with the need ids it belongs to.
  Reason: each subject must appear in a view, so the details of a long description are not lost.
  Do not list the system, the feature being changed, or the need wording itself as a subject. A short request usually has no subjects.
- quality_attributes: quality ids the description stresses, or an empty list. They do not choose diagrams.

OUTPUT
Return only this JSON.
{{
  "role_label": "label as the user said it",
  "role": "one role id, or null",
  "needs": [{{"need": "need id", "evidence": "exact words"}}],
  "subjects": [{{"text": "exact words", "needs": ["need id"]}}],
  "quality_attributes": []
}}
"""


class NeedEvidence(BaseModel):
    need: str
    evidence: str


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
            needs=[n.need for n in self.needs],
            subjects=self.subjects,
            role=self.role,
            detail_level=self.detail_level,
        )


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s/-]", " ", text.casefold()).split())


_DETAIL_CUES = ("in particular", "specifically", "in detail")


def detail_level(goal: str) -> str:
    """overview / feature / detailed from the goal text alone (L1 / L2 / L3).

    Computed from the text, not from the model's subject list, so the same goal
    always gets the same granularity.
    """
    words = len(goal.split())
    if words >= 110 or any(cue in goal.casefold() for cue in _DETAIL_CUES):
        return "detailed"
    if words >= 45:
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
            needs.append(NeedEvidence(need=need, evidence=evidence))

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
        detail_level=detail_level(goal),
        dropped=dropped,
    )
