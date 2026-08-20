"""Merge parallel extraction claims into one Architecture Evidence Model."""

from __future__ import annotations

from task2view.agents.schemas import ArchitectureEvidenceModel, GroundedClaim


def merge_claims(claims: list[GroundedClaim]) -> ArchitectureEvidenceModel:
    by_key: dict[tuple, GroundedClaim] = {}
    for claim in claims:
        key = (
            claim.source_element.casefold(),
            (claim.target_element or "").casefold(),
            (claim.relationship or "").casefold(),
            (claim.claim or "").casefold(),
        )
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = claim
            continue
        prev.question_ids = sorted(set(prev.question_ids) | set(claim.question_ids))
        prev.evidence = list(prev.evidence) + [e for e in claim.evidence if e not in prev.evidence]
        if prev.order is None:
            prev.order = claim.order
    merged = list(by_key.values())
    elements: list[str] = []
    for claim in merged:
        for name in (claim.source_element, claim.target_element):
            if name and name not in elements:
                elements.append(name)
    return ArchitectureEvidenceModel(claims=merged, elements=elements)
