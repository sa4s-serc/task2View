"""Phase 5 driver: run each investigation task, verify its claims, consolidate the AEM.

Rejected claims are kept in the model with their reason, so a run shows what an
agent said that the repository did not support.
"""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import Claim, EvidenceModel, InvestigationTask, Question
from task2view.contracts.card import RepositoryCard
from task2view.contracts.models import PipelineError
from task2view.knowledge.catalog import Catalog
from task2view.phase4.investigate import pipeline_config
from task2view.phase5.agent import run_evidence_task
from task2view.phase5.consolidate import build_evidence_model
from task2view.phase5.verify import ClaimVerifier


def collect_evidence(
    tasks: list[InvestigationTask],
    questions: list[Question],
    card: RepositoryCard,
    runtime: AgentRuntime,
    catalog: Catalog,
    *,
    card_text: str,
    previous: EvidenceModel | None = None,
    grain: str = "class",
) -> EvidenceModel:
    """``grain``: "package" (overview goals) or "class" component boundaries; see consolidate.py."""
    cfg = pipeline_config()
    ev = cfg["evidence"]
    verifier = ClaimVerifier(card, slack=ev["excerpt_line_slack"], min_confidence=ev["min_confidence"])
    claims: list[Claim] = list(previous.claims.values()) if previous else []
    rejected: list[dict] = list(previous.rejected_claims) if previous else []
    notes: list[str] = list(previous.notes) if previous else []
    for task in tasks:
        try:
            raw_claims, opened, calls = run_evidence_task(
                task, questions, card, runtime, card_text=card_text,
                viewpoint_name=catalog.viewpoint(task.viewpoint_id).name,
                max_read_lines=ev["max_read_lines"], max_hits=ev["max_search_hits"], keep_results=ev["keep_results"],
            )
        except PipelineError as exc:
            notes.append(f"{task.id} failed: {exc}")
            continue
        used = ", ".join(f"{k} {v}" for k, v in sorted(calls.items())) or "no tools"
        notes.append(f"{task.id}: {len(raw_claims)} claims, read {len(opened)} files; {used}")
        for raw in raw_claims:
            claim, reason = verifier.verify(raw, claim_id=f"C{len(claims) + 1}", task_id=task.id,
                                            question_ids=task.question_ids)
            if claim is None:
                rejected.append({"task": task.id, "claim": raw, "reason": reason})
            else:
                claims.append(claim)
    model = build_evidence_model(claims, card, cfg["consolidation"], grain=grain)
    model.rejected_claims = rejected
    model.notes = notes
    return model
