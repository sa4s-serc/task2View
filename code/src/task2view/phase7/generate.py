"""Phase 7. One view-generation agent.

It may publish only names and connections already present in the evidence
or in the extracted view. The notation adapter then writes the diagram text.
The agent does not choose the diagram language.
"""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import ArchitectureEvidenceModel, RepositoryAnalysisPlan, StakeholderTaskProfile
from task2view.contracts.models import (
    Evidence,
    ViewElement,
    ViewModel,
    ViewRelation,
    ViewSpecification,
    canonical_relation_kind,
)
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

PROMPT = """You are the View Generation Agent.

GOAL
Publish one architectural view for the viewpoint already chosen.
Use only the evidence and the decisions from the previous stages.
The same evidence must produce the same boxes and the same connections.
Do not choose a diagram language. A later step renders the language already selected.

INPUTS
1. PROFILE — who the view is for, the target, the goal, and the scope.
2. QUESTIONS — the facts the view must show, in the order they were written.
3. VIEWPOINT — the id, the purpose, and the grain. The grain says what a box is and what must not be drawn.
4. ANALYSIS TASKS — where each question was looked up, and which questions had no file.
5. EVIDENCE — the only architectural names and connections you may publish. Each line cites a file.
6. RECONCILIATION NOTES — what the previous step said was answered or missing. Notes do not add boxes.

PROFILE
{profile}

QUESTIONS
{questions}

VIEWPOINT
{viewpoint}

ANALYSIS TASKS
{tasks}

EVIDENCE
{evidence}

RECONCILIATION NOTES
{notes}

DECISION
1. Publish one element only when its name appears in EVIDENCE.
   Reason: a box that evidence did not record is an invention. The run cannot be checked against the code.
2. Name the element as the evidence names it. Do not rename it to a folder, a package, or a file.
   Reason: the grain decides the name. The generator does not get a second chance to change the grain.
3. Publish a connection only when EVIDENCE lists that source, that target, and that relationship.
   Reason: a new arrow is a new claim. Claims are made in Phase 5, not here.
4. Leave out an evidence name when a reconciliation note says that question is unanswered, or when the grain's do-not line forbids that kind of box.
   Reason: the view shows the supported part of the viewpoint. Unsupported facts stay in the notes.
5. notes says, in one sentence, which evidence names were left out and why.
   Reason: the sentence is the rationale stored with the run.

OUTPUT
Return only this JSON. One view.
{{
  "elements": [
    {{"name": "name copied from EVIDENCE", "kind": "component", "role": "the claim"}}
  ],
  "relations": [
    {{"from": "source name", "to": "target name", "kind": "uses"}}
  ],
  "notes": ["which evidence names were left out and why"]
}}
"""


def _names_from_evidence(evidence: ArchitectureEvidenceModel | None, current: ViewModel) -> list[str]:
    if evidence is not None and evidence.elements:
        return list(evidence.elements)
    return [el.name for el in current.elements if el.name]


def _legal_relations(
    evidence: ArchitectureEvidenceModel | None,
    current: ViewModel,
) -> set[tuple[str, str, str]]:
    legal: set[tuple[str, str, str]] = set()
    if evidence is not None:
        for claim in evidence.claims:
            if claim.target_element and claim.relationship:
                legal.add(
                    (
                        claim.source_element.casefold(),
                        claim.target_element.casefold(),
                        canonical_relation_kind(claim.relationship),
                    )
                )
        if legal:
            return legal
    id_to_name = {el.id: el.name for el in current.elements}
    for rel in current.relations:
        frm = id_to_name.get(rel.frm, rel.frm)
        to = id_to_name.get(rel.to, rel.to)
        legal.add((frm.casefold(), to.casefold(), canonical_relation_kind(rel.kind)))
    return legal


def _evidence_text(evidence: ArchitectureEvidenceModel | None, current: ViewModel) -> str:
    if evidence is not None and evidence.claims:
        lines = []
        for claim in evidence.claims:
            path = ""
            if claim.evidence:
                path = str(claim.evidence[0].get("file") or "")
            link = ""
            if claim.target_element and claim.relationship:
                link = f" -{claim.relationship}-> {claim.target_element}"
            lines.append(f"- {claim.source_element}{link}: {claim.claim} ({path})")
        return "\n".join(lines)
    if not current.elements:
        return "(none)"
    lines = []
    id_to_name = {el.id: el.name for el in current.elements}
    for el in current.elements:
        path = el.evidence.file if el.evidence and el.evidence.file else ""
        lines.append(f"- {el.name}: {el.role or el.name} ({path})")
    for rel in current.relations:
        frm = id_to_name.get(rel.frm, rel.frm)
        to = id_to_name.get(rel.to, rel.to)
        lines.append(f"- {frm} -{rel.kind}-> {to}")
    return "\n".join(lines)


def generate_view(
    profile: StakeholderTaskProfile,
    spec: ViewSpecification,
    plan: RepositoryAnalysisPlan | None,
    evidence: ArchitectureEvidenceModel | None,
    current: ViewModel,
    critic_notes: list[str],
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
) -> ViewModel:
    knowledge = knowledge or load_knowledge()
    viewpoint_id = spec.selected_view.viewpoint_id or ""
    questions = "\n".join(f"- {q.id}: {q.text}" for q in spec.architectural_questions) or "(none)"
    if plan is not None and plan.analysis_tasks:
        tasks = "\n".join(
            f"- {task.id} {', '.join(task.addresses)}: {task.goal}; files: {', '.join(task.candidate_locations) or '(none)'}"
            for task in plan.analysis_tasks
        )
    else:
        tasks = "(none)"
    profile_text = "\n".join(
        [
            f"stakeholder: {profile.stakeholder}",
            f"target: {profile.target}",
            f"goal: {profile.goal}",
            f"scope: {profile.scope or '(none)'}",
        ]
    )
    viewpoint_text = "\n".join(
        [
            f"id: {viewpoint_id}",
            f"purpose: {spec.selected_view.purpose}",
            knowledge.grain_prompt(viewpoint_id, spec.selected_view.view_type),
        ]
    )
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile_text,
            questions=questions,
            viewpoint=viewpoint_text,
            tasks=tasks,
            evidence=_evidence_text(evidence, current),
            notes="\n".join(f"- {note}" for note in critic_notes) or "(none)",
        )
    )
    allowed = {name.casefold(): name for name in _names_from_evidence(evidence, current)}
    prior = {el.name.casefold(): el for el in current.elements}
    legal = _legal_relations(evidence, current)
    elements: list[ViewElement] = []
    ids: dict[str, str] = {}
    for item in raw.get("elements") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        key = name.casefold()
        if key not in allowed or key in ids:
            continue
        published = allowed[key]
        previous = prior.get(key)
        evidence_obj = previous.evidence if previous is not None else None
        if evidence_obj is None and evidence is not None:
            for claim in evidence.claims:
                if claim.source_element.casefold() == key and claim.evidence:
                    ev = claim.evidence[0]
                    evidence_obj = Evidence(
                        file=ev.get("file"),
                        symbol=ev.get("symbol"),
                        excerpt=ev.get("excerpt"),
                    )
                    break
        eid = f"E{len(elements) + 1}"
        ids[key] = eid
        elements.append(
            ViewElement(
                id=eid,
                name=published,
                kind=previous.kind if previous is not None else "component",
                role=str(item.get("role") or (previous.role if previous is not None else "") or ""),
                external=previous.external if previous is not None else False,
                evidence=evidence_obj,
                support=previous.support if previous is not None else "observed",
            )
        )
    if not elements:
        return current
    relations: list[ViewRelation] = []
    for item in raw.get("relations") or []:
        if not isinstance(item, dict):
            continue
        frm = str(item.get("from") or "").strip().casefold()
        to = str(item.get("to") or "").strip().casefold()
        kind = canonical_relation_kind(str(item.get("kind") or "uses"))
        if (frm, to, kind) not in legal:
            continue
        if frm not in ids or to not in ids:
            continue
        relations.append(
            ViewRelation(
                id=f"R{len(relations) + 1}",
                frm=ids[frm],
                to=ids[to],
                kind=kind,
                label=item.get("label"),
                support="observed",
            )
        )
    notes = [str(x) for x in raw.get("notes") or [] if str(x).strip()]
    return current.model_copy(
        update={
            "elements": elements,
            "relations": relations,
            "groups": [],
            "notes": notes or list(current.notes),
        }
    )
