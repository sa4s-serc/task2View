"""Phase 8 layer 5 — task-fit judge (Track 2; ADR-006 D3: different model, soft until calibrated).

An LLM scores how well a rendered view serves the stakeholder's request on seven
general quality themes. Its scores are reported, never used to pass or fail a
view, until they are calibrated against human ratings. The judge should be a
different model from the generator; the report says when it is not.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import Question
from task2view.contracts.views import ArchitectureView
from task2view.prompts import load_prompt

THEMES = {
    "second-view": "structure and behaviour are not mixed in one picture; the view shows one kind of information",
    "grain": "the level of detail matches what the request asks for",
    "layers": "elements are grouped into layers or packages where that helps the request",
    "names": "every element is a real part of the system and in scope for the request",
    "notation": "the diagram is drawn as the kind of view it claims to be, with fitting symbols",
    "placement": "each fact sits on the right mark (responsibilities in elements, attributes in entities)",
    "layout": "the arrangement and arrows are easy to follow",
}

class JudgeReport(BaseModel):
    status: str  # scored | not-run | failed
    model: str | None = None
    independent: bool | None = None
    scores: dict[str, dict] = Field(default_factory=dict)
    overall: int | None = None
    summary: str = ""


def judge_view(view: ArchitectureView, questions: list[Question], goal: str, source: str, language: str,
               runtime: AgentRuntime | None, *, judge_spec: str | None, generator_spec: str | None) -> JudgeReport:
    if runtime is None:
        return JudgeReport(status="not-run", summary="no judge model configured (--judge-llm)")
    names = {e.id: e.name for e in view.elements}
    prompt = load_prompt("phase8_judge").render(
        goal=goal,
        questions="\n".join(f"- {q.text}" for q in questions if q.view_id == view.id) or "- none",
        kind=view.viewpoint_name, title=view.title,
        elements="\n".join(f"- {e.kind} {e.name}" + (f" ({'; '.join(e.responsibilities)})" if e.responsibilities else "")
                           for e in view.content_elements()) or "- none",
        relations="\n".join([f"- {names.get(r.source, r.source)} {r.kind} {names.get(r.target, r.target)}" for r in view.relations]
                            + [f"- {i.order}. {names.get(i.source, i.source)} -> {names.get(i.target, i.target)}: {i.message}"
                               for i in view.interactions]) or "- none",
        language=language, source=source[:8000],
        themes="\n".join(f"- {k}: {v}" for k, v in THEMES.items()),
    )
    try:
        raw = runtime.complete_json(prompt, purpose=f"phase8-judge:{view.id}")
    except Exception as exc:  # the judge is soft: a failure is reported, never fatal
        return JudgeReport(status="failed", model=judge_spec, summary=str(exc)[:300])
    scores = {k: v for k, v in (raw.get("scores") or {}).items() if isinstance(v, dict)}
    if isinstance(raw.get("answers_questions"), dict):
        scores["answers-questions"] = raw["answers_questions"]
    overall = raw.get("overall") if isinstance(raw.get("overall"), int) else None
    known = {judge_spec, generator_spec}.isdisjoint({None, "scripted"})  # scripted test models have no identity
    independent = judge_spec != generator_spec if known else None
    return JudgeReport(status="scored", model=judge_spec, independent=independent,
                       scores=json.loads(json.dumps(scores)), overall=overall, summary=str(raw.get("summary") or ""))
