"""Phase 8 layer 5 — task-fit judge (Track 2; ADR-006 D3: different model, soft until validated).

An LLM scores how well a view serves the stakeholder's request. Its scores are
reported, never used to pass or fail a view, until a human-rated validation set
shows they agree with people. Design follows the LLM-as-judge literature:
- one theme per call, so scores of different themes do not echo each other;
- each theme has anchored levels (1, 3, 5), and the reason comes before the score;
- the judge reads the diagram source and the view's facts, not a rendered image;
- notation, names and grain are not judged: rule layers check them (compile and
  model kind, faithfulness to the evidence model, the detail-level cap and grain);
- the judge must be a different model family from every generator; the report
  records whether the spec differs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import Question
from task2view.contracts.views import ArchitectureView
from task2view.prompts import load_prompt

# theme -> (what it asks, anchors for 5 / 3 / 1); frozen as rubric v1 before any experiment output is seen
RUBRIC_VERSION = "v1"
THEMES = {
    "answers-questions": (
        "the view answers the questions it was made for (and the expected facts, when given)",
        "every question is answered by marks in the view",
        "some questions are answered, or answered only partly",
        "the view does not answer its questions"),
    "second-view": (
        "structure and behaviour are not mixed in one picture; the view shows one kind of information",
        "one kind of information, and another view holds the rest",
        "mostly one kind, with some mixing that a reader must untangle",
        "structure and behaviour are mixed so that neither can be read"),
    "layers": (
        "elements are grouped into layers or packages where that helps the request",
        "grouping makes the organisation clear, or none is needed",
        "grouping exists but hides or misplaces some elements",
        "a grouping the request needs is missing or wrong"),
    "placement": (
        "each fact sits on the right mark (responsibilities in elements, attributes in entities, messages on calls)",
        "every fact is on the right kind of mark",
        "a few facts are on the wrong kind of mark",
        "facts are mostly on the wrong marks (e.g. responsibilities as element names)"),
    "layout": (
        "the arrangement and arrows can be followed",
        "a reader follows every arrow without effort",
        "some crossings or clutter slow the reader",
        "the diagram cannot be followed"),
}


class JudgeReport(BaseModel):
    status: str  # scored | partial | not-run | failed
    model: str | None = None
    rubric: str = RUBRIC_VERSION
    independent: bool | None = None
    scores: dict[str, dict] = Field(default_factory=dict)  # theme -> {reason, score}
    summary: str = ""


def judge_view(view: ArchitectureView, questions: list[Question], goal: str, source: str, language: str,
               runtime: AgentRuntime | None, *, judge_spec: str | None, generator_spec: str | None,
               expected: list[str] | None = None) -> JudgeReport:
    if runtime is None:
        return JudgeReport(status="not-run", summary="no judge model configured (--judge-llm)")
    names = {e.id: e.name for e in view.elements}
    facts = dict(
        goal=goal,
        questions="\n".join(f"- {q.text}" for q in questions if q.view_id == view.id) or "- none",
        expected="\n".join(f"- {x}" for x in expected or []) or "- none given",
        kind=view.viewpoint_name, title=view.title,
        elements="\n".join(f"- {e.kind} {e.name}" + (f" ({'; '.join(e.responsibilities)})" if e.responsibilities else "")
                           for e in view.content_elements()) or "- none",
        relations="\n".join([f"- {names.get(r.source, r.source)} {r.kind} {names.get(r.target, r.target)}" for r in view.relations]
                            + [f"- {i.order}. {names.get(i.source, i.source)} -> {names.get(i.target, i.target)}: {i.message}"
                               for i in view.interactions]) or "- none",
        language=language, source=source[:8000],
    )
    scores, errors = {}, []
    for theme, (asks, five, three, one) in THEMES.items():
        prompt = load_prompt("phase8_judge").render(**facts, theme=theme, asks=asks, five=five, three=three, one=one)
        try:  # the judge is soft: a failure is reported, never fatal
            raw = runtime.complete_json(prompt, purpose=f"phase8-judge:{view.id}:{theme}")
        except Exception as exc:
            errors.append(f"{theme}: {str(exc)[:150]}")
            continue
        score = raw.get("score")
        if isinstance(score, int) and 1 <= score <= 5:
            scores[theme] = {"reason": str(raw.get("reason") or ""), "score": score}
        else:
            errors.append(f"{theme}: no score 1-5 in the reply")
    known = {judge_spec, generator_spec}.isdisjoint({None, "scripted"})  # scripted test models have no identity
    status = "failed" if not scores else "partial" if errors else "scored"
    return JudgeReport(status=status, model=judge_spec, independent=judge_spec != generator_spec if known else None,
                       scores=scores, summary="; ".join(errors))
