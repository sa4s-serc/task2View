"""PDF Phase 7 — build a notation-neutral view model from the evidence model."""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import ArchitectureEvidenceModel, PlannedView
from task2view.contracts.models import (
    ALLOWED_ELEMENT_KINDS,
    ALLOWED_RELATION_KINDS,
    Evidence,
    ViewElement,
    ViewGroup,
    ViewModel,
    ViewRelation,
)

PROMPT = """You are a Specialized View Generation Agent.

Build a notation-neutral view model from grounded claims only.
Do not add elements or relations that are not in the claims.
view_type={view_type}. granularity={granularity}.

CLAIMS:
{claims}

Return JSON:
{{
  "groups": [{{"id":"G1","name":"layer-or-package","kind":"layer","contains":["E1"]}}],
  "elements": [{{"id":"E1","name":"...","kind":"component|class|service|datastore|actor","role":"...","external":false}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"call|depends","label":"...","order":1}}]
}}

Use claim source/target names unchanged. kind call if relationship is call/invokes, else depends.
"""

_REL = {
    "call": "call",
    "calls": "call",
    "invokes": "call",
    "invoke": "call",
    "uses": "depends",
    "depends": "depends",
    "dependency": "depends",
    "inherits": "inherits",
    "implements": "implements",
    "dataflow": "dataflow",
    "return": "return",
}


def _kind_for(name: str) -> str:
    lower = name.lower()
    if "gui" in lower or "boundary" in lower or "controller" in lower and "rest" in lower:
        return "component"
    if lower.endswith("service") or "manager" in lower:
        return "service"
    if "persist" in lower or "repository" in lower or "jpa" in lower:
        return "datastore"
    return "component"


def generate_view_model(
    request_id: str,
    view: PlannedView,
    evidence: ArchitectureEvidenceModel,
    runtime: AgentRuntime | None = None,
    unanswered: list[str] | None = None,
) -> ViewModel:
    if runtime is not None and evidence.claims:
        raw = runtime.complete_json(
            PROMPT.format(
                view_type=view.view_type,
                granularity=view.granularity,
                claims=evidence.model_dump_json(indent=2)[:24_000],
            )
        )
        elements = []
        for i, item in enumerate(raw.get("elements") or [], start=1):
            kind = str(item.get("kind") or "component")
            if kind not in ALLOWED_ELEMENT_KINDS:
                kind = "component"
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            elements.append(
                ViewElement(
                    id=str(item.get("id") or f"E{i}"),
                    name=name,
                    kind=kind,
                    role=item.get("role"),
                    external=bool(item.get("external")),
                )
            )
        id_ok = {e.id for e in elements}
        relations = []
        for i, item in enumerate(raw.get("relations") or [], start=1):
            kind = _REL.get(str(item.get("kind") or "depends").lower(), "depends")
            if kind not in ALLOWED_RELATION_KINDS:
                kind = "depends"
            rel = ViewRelation(
                id=str(item.get("id") or f"R{i}"),
                frm=str(item.get("from") or item.get("frm") or ""),
                to=str(item.get("to") or ""),
                kind=kind,
                label=item.get("label"),
                order=item.get("order"),
            )
            if rel.frm in id_ok and rel.to in id_ok:
                relations.append(rel)
        groups = []
        for i, item in enumerate(raw.get("groups") or [], start=1):
            groups.append(
                ViewGroup(
                    id=str(item.get("id") or f"G{i}"),
                    name=str(item.get("name") or ""),
                    kind=str(item.get("kind") or "layer"),
                    contains=[str(x) for x in item.get("contains") or [] if str(x) in id_ok],
                )
            )
        if elements:
            return ViewModel(
                request_id=request_id,
                view_type=view.view_type,
                granularity=view.granularity,
                groups=groups,
                elements=elements,
                relations=relations,
                unanswered=unanswered or [],
            )
    return _from_claims(request_id, view, evidence, unanswered or [])


def _from_claims(
    request_id: str,
    view: PlannedView,
    evidence: ArchitectureEvidenceModel,
    unanswered: list[str],
) -> ViewModel:
    names: list[str] = []
    for claim in evidence.claims:
        for name in (claim.source_element, claim.target_element):
            if name and name not in names:
                names.append(name)
    elements = [
        ViewElement(id=f"E{i}", name=name, kind=_kind_for(name))
        for i, name in enumerate(names, start=1)
    ]
    index = {e.name: e.id for e in elements}
    relations: list[ViewRelation] = []
    for i, claim in enumerate(evidence.claims, start=1):
        if not claim.target_element:
            continue
        frm = index.get(claim.source_element)
        to = index.get(claim.target_element)
        if not frm or not to:
            continue
        kind = _REL.get((claim.relationship or "depends").lower(), "depends")
        ev = None
        if claim.evidence:
            first = claim.evidence[0]
            ev = Evidence(
                file=first.get("file"),
                symbol=first.get("symbol"),
                excerpt=first.get("excerpt"),
            )
        relations.append(
            ViewRelation(
                id=f"R{i}",
                frm=frm,
                to=to,
                kind=kind if kind in ALLOWED_RELATION_KINDS else "depends",
                label=claim.relationship,
                order=claim.order,
                evidence=ev,
                support="inferred" if claim.support_type == "inferred" else "observed",
            )
        )
    return ViewModel(
        request_id=request_id,
        view_type=view.view_type,
        granularity=view.granularity,
        elements=elements,
        relations=relations,
        unanswered=unanswered,
        notes=["generated from Architecture Evidence Model claims"],
    )
