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


SPEC_VALUES = {"scope": ("system", "feature"), "granularity": ("coarse", "medium", "fine"),
               "behaviour": ("structure", "interaction", "both")}


class ViewSpec(BaseModel):
    """ADR-007 D1: how the views should be drawn. scope: whole system or one feature; granularity: layers
    (coarse), the main parts (medium) or classes (fine); behaviour: parts, order of calls, or both."""
    scope: Literal["system", "feature"] = "system"
    granularity: Literal["coarse", "medium", "fine"] = "medium"
    behaviour: Literal["structure", "interaction", "both"] = "structure"


class Clarification(BaseModel):
    field: Literal["scope", "granularity", "behaviour"]
    question: str
    default: str
    answer: str = ""  # the person's answer; empty when the run used the default


class NeedProfile(BaseModel):
    goal: str
    role_label: str = ""
    role: str | None = None
    target: str = ""
    needs: list[NeedEvidence] = Field(default_factory=list)
    subjects: list[GoalSubject] = Field(default_factory=list)
    quality_attributes: list[str] = Field(default_factory=list)
    detail_level: str = "feature"
    spec: ViewSpec = Field(default_factory=ViewSpec)
    clarifications: list[Clarification] = Field(default_factory=list)
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
        row = row if isinstance(row, dict) else {"need": row}
        need = str(row.get("need") or "").strip()
        evidence = str(row.get("evidence") or "").strip()
        if need not in catalog.needs:
            dropped.append(f"need {need!r}: not in the catalog")
        elif not evidence or _norm(evidence) not in norm_goal:
            dropped.append(f"need {need!r}: evidence {evidence!r} is not in the goal")
        elif need not in {n.need for n in needs}:
            salience = str(row.get("salience") or "primary").strip().lower()
            if salience not in {"primary", "secondary"}:
                dropped.append(f"need {need!r}: salience {salience!r} unknown, treated as primary")
                salience = "primary"
            needs.append(NeedEvidence(need=need, evidence=evidence, salience=salience))

    subjects: list[GoalSubject] = []
    for row in raw.get("subjects") or []:
        row = row if isinstance(row, dict) else {"text": row}
        text = str(row.get("text") or "").strip()
        if not text or _norm(text) not in norm_goal:
            dropped.append(f"subject {text!r}: not in the goal")
            continue
        if text in {s.text for s in subjects}:
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
    clarifications = []
    for row in raw.get("clarifications") or []:
        row = row if isinstance(row, dict) else {}
        field, default = str(row.get("field") or ""), str(row.get("default") or "")
        question = str(row.get("question") or "").strip()
        if field in SPEC_VALUES and default in SPEC_VALUES[field] and question and field not in {c.field for c in clarifications}:
            clarifications.append(Clarification(field=field, question=question[:200], default=default))
        else:
            dropped.append(f"clarification {row!r}: not one of the spec fields with an allowed default")
    level = detail_level(sum(n.salience == "primary" for n in needs), len(subjects), catalog.detail_rule)
    return NeedProfile(
        goal=goal,
        role_label=label,
        role=role,
        target=target,
        needs=needs,
        subjects=subjects,
        quality_attributes=qualities,
        detail_level=level,
        spec=default_spec(needs, target, level, catalog),
        clarifications=clarifications[:3],
        dropped=dropped,
    )


def default_spec(needs: list[NeedEvidence], target: str, level: str, catalog: Catalog) -> ViewSpec:
    """The spec the request implies: a feature slice when it names a target; layers only for a
    whole-system overview; behaviour from the categories of its primary needs."""
    kinds = {catalog.needs[n.need].category for n in needs if n.salience == "primary"}
    # asking how parts interact (or in which order, or the flow) is asking about behaviour as well
    dynamic = any(_DYNAMIC.search(n.evidence) for n in needs if n.salience == "primary")
    if "behavior" in kinds or dynamic:
        behaviour = "both" if kinds - {"behavior"} else "interaction"
    else:
        behaviour = "structure"
    return ViewSpec(scope="feature" if target else "system",
                    granularity="coarse" if level == "overview" and not target else "medium", behaviour=behaviour)


_DYNAMIC = re.compile(r"\binteract|\bin which order|\bsequence|\bflow\b|\bstep", re.I)


def apply_clarifications(profile: NeedProfile, catalog: Catalog, ask=None) -> list[str]:
    """Answer each clarification (``ask(question, options, default)`` for a person; the default
    otherwise) and update the spec. A default never takes away what the request states (a target, the
    behaviour it asks about); only a person's answer can. Returns one log line per clarification."""
    log = []
    for c in profile.clarifications:
        answer = c.default
        if ask is not None:
            given = str(ask(c.question, SPEC_VALUES[c.field], c.default) or "").strip().lower()
            if given in SPEC_VALUES[c.field]:
                answer = c.answer = given
        current = getattr(profile.spec, c.field)
        stated = (c.field == "scope" and current == "feature") or (c.field == "behaviour" and current != "structure")
        if not c.answer and stated and answer != current and answer != "both":
            log.append(f"clarification {c.field}: kept {current} (the request states it; default was {answer}) — {c.question}")
            continue
        setattr(profile.spec, c.field, answer)
        log.append(f"clarification {c.field}: {answer}{'' if c.answer else ' (default)'} — {c.question}")
    if profile.spec.scope == "system":
        profile.target = ""
    behavioural = {n for n, d in catalog.needs.items() if d.category == "behavior"}
    if profile.spec.behaviour in {"interaction", "both"} and not any(n.need in behavioural and n.salience == "primary"
                                                                   for n in profile.needs):
        profile.needs.append(NeedEvidence(need="interaction-order", evidence="(clarification)", salience="primary"))
    if profile.spec.behaviour == "structure" and any(c.answer for c in profile.clarifications if c.field == "behaviour"):
        for n in profile.needs:  # only a person's answer removes behaviour the request asked about
            if n.need in behavioural:
                n.salience = "secondary"
    return log
