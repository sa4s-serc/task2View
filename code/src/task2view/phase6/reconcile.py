"""Phase 6. Need–evidence reconciliation.

Compares each architectural question with the claims. Does not add boxes
and does not change the viewpoint. The view generator reads this plan.
"""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import (
    ArchitectureEvidenceModel,
    EvidenceAwarePlan,
    RepositoryAnalysisPlan,
)
from task2view.contracts.models import ViewModel, ViewSpecification

_SUPPORT = {"supported", "partial", "unsupported"}

PROMPT = """You are the Need-Evidence Reconciliation Agent.

GOAL
Compare each architectural question with the evidence already extracted.
Record whether the evidence supports it, what is unanswered, and the limitations.
Do not add boxes. Do not change the viewpoint. Do not choose a diagram language.

INPUTS
1. QUESTIONS — the facts the view was supposed to show, in order.
2. EVIDENCE — claims that cite a file. A question with no claim is not supported.
3. ANALYSIS GAPS — tasks that named no file, or whose files showed nothing.
4. GRAIN — what this view is allowed to show.
5. DIAGRAM LANGUAGE — already chosen. This step records it. It does not pick another one.

QUESTIONS
{questions}

EVIDENCE
{evidence}

ANALYSIS GAPS
{gaps}

GRAIN
{grain}

DIAGRAM LANGUAGE
{language}

DECISION
1. For each question, set support to supported, partial, or unsupported.
   supported: a claim cites a file and states the fact the question asks.
   partial: a claim touches the question but does not show the connection or the part it asks for.
   unsupported: no claim addresses the question.
   Reason: support is what a later reader checks. A supported question with no file citation is not supported.
2. unanswered lists the ids whose support is unsupported.
   Reason: those questions stay visible as gaps instead of being drawn.
3. limitations are the analysis gaps, the grain's do-not line, and any fact the evidence cannot show.
   Reason: a limitation is a bound on this view, not a new task.
4. rationale is one sentence: what this evidence can carry for the chosen viewpoint, and the diagram language already chosen.
   Reason: the sentence is stored with the run so the language and the support can be read together.

OUTPUT
Return only this JSON. One entry per question, in the same order.
{{
  "questions": [
    {{"id": "AQ1", "support": "supported", "rationale": "which claim shows it"}}
  ],
  "unanswered": ["AQ2"],
  "limitations": ["limit"],
  "rationale": "what this evidence can carry"
}}
"""


def _evidence_lines(evidence: ArchitectureEvidenceModel | None, view: ViewModel) -> str:
    if evidence is not None and evidence.claims:
        lines = []
        for claim in evidence.claims:
            path = claim.evidence[0].get("file") if claim.evidence else ""
            ids = ", ".join(claim.question_ids) or claim.analysis_task or ""
            lines.append(f"- [{ids}] {claim.claim} ({claim.source_element}; {path})")
        return "\n".join(lines)
    if not view.elements:
        return "(none)"
    return "\n".join(
        f"- {el.name}: {el.role or el.name} ({el.evidence.file if el.evidence else ''})"
        for el in view.elements
    )


def reconcile_evidence(
    spec: ViewSpecification,
    plan: RepositoryAnalysisPlan | None,
    evidence: ArchitectureEvidenceModel | None,
    view: ViewModel,
    runtime: AgentRuntime,
) -> EvidenceAwarePlan:
    questions = list(spec.architectural_questions)
    qtext = "\n".join(f"- {q.id}: {q.text}" for q in questions) or "(none)"
    gaps = []
    if evidence is not None:
        gaps.extend(evidence.notes)
    if plan is not None:
        for task in plan.analysis_tasks:
            if not task.candidate_locations and not task.starting_points:
                gaps.append(f"{task.id} named no file for {', '.join(task.addresses)}")
    language = spec.selected_view.diagram_language
    rule = spec.selected_view.diagram_language_rule or ""
    language_line = f"{language}" + (f" — {rule}" if rule else "")
    raw = runtime.complete_json(
        PROMPT.format(
            questions=qtext,
            evidence=_evidence_lines(evidence, view),
            gaps="\n".join(f"- {gap}" for gap in gaps) or "(none)",
            grain=f"unit={spec.selected_view.grain_unit or spec.selected_view.granularity}",
            language=language_line,
        )
    )
    by_id = {q.id: q.text for q in questions}
    recorded: list[dict] = []
    seen: set[str] = set()
    for item in raw.get("questions") or []:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("id") or "").strip()
        if qid not in by_id or qid in seen:
            continue
        support = str(item.get("support") or "unsupported").strip().lower()
        if support not in _SUPPORT:
            support = "unsupported"
        seen.add(qid)
        recorded.append(
            {
                "id": qid,
                "text": by_id[qid],
                "support": support,
                "rationale": str(item.get("rationale") or "").strip(),
            }
        )
    for qid, text in by_id.items():
        if qid in seen:
            continue
        recorded.append(
            {
                "id": qid,
                "text": text,
                "support": "unsupported",
                "rationale": "The reconciliation returned no judgment for this question.",
            }
        )
    unanswered = [row["id"] for row in recorded if row["support"] == "unsupported"]
    limitations = [str(x) for x in raw.get("limitations") or [] if str(x).strip()]
    for gap in gaps:
        if gap not in limitations:
            limitations.append(gap)
    return EvidenceAwarePlan(
        viewpoint_id=spec.selected_view.viewpoint_id,
        diagram_language=language,
        diagram_language_rule=rule,
        questions=recorded,
        unanswered=unanswered,
        limitations=limitations,
        rationale=str(raw.get("rationale") or "").strip(),
    )
