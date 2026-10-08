---
id: phase8_judge
phase: "8 — Validation, layer 5: task fit (Track 2)"
called_from: task2view/phase8/judge.py (judge_view)
purpose: >-
  Score how well one rendered view serves the stakeholder's request, on seven general quality themes
  plus how well it answers its questions. Run with a different model from the one that produced
  the view (--judge-llm). Scores are reported only; they never pass or fail a view until calibrated
  against human ratings.
inputs:
  goal: the stakeholder goal, verbatim
  questions: the questions the view must answer
  kind: the viewpoint name
  title: the view title
  elements: the view's elements (kind, name, responsibilities)
  relations: the view's relations and ordered interactions
  language: the notation of the diagram source
  source: the diagram source (truncated to 8000 characters)
  themes: the seven themes with their definitions
output: "JSON {scores: {<theme>: {score 1-5, reason}}, answers_questions: {score, reason}, overall 1-5, summary}"
checked_by: judge.py keeps only well-formed scores; a failed call is reported as status "failed" and never stops a run.
---
# Task2View — Phase 8: Task-fit review

## Role
You are a software architect reviewing one architecture diagram for a stakeholder. You score it; you do not redraw it.

## Inputs

### The stakeholder's request
<request>
{{goal}}
</request>

### Questions this view must answer
{{questions}}

### The view
{{kind}}: {{title}}

Elements:
{{elements}}

Relations and interactions:
{{relations}}

Diagram source ({{language}}):
<diagram>
{{source}}
</diagram>

## Themes
Score each theme from 1 to 5:
{{themes}}

Scale for every theme:
- **5:** no problem a reviewer would mention.
- **3:** a noticeable problem, but the view is still usable for the request.
- **1:** the problem makes the view misleading or useless for the request.

Also score **answers_questions** on the same scale: how well the view answers the questions above.

## Rules
1. Judge the view against this stakeholder's request, not against an ideal documentation set.
2. Give one sentence of reason per score, naming the element or relation you mean.
3. Do not reward a view for size: more elements is not better.

## Output
Return one JSON object and nothing else:
```json
{
  "scores": {
    "second-view": {"score": 5, "reason": "Shows structure only; the call order is in a separate view."},
    "grain": {"score": 4, "reason": "..."}
  },
  "answers_questions": {"score": 4, "reason": "..."},
  "overall": 4,
  "summary": "One or two sentences."
}
```
Include all seven themes in `scores`.

## Check before answering
- All seven themes and answers_questions are scored from 1 to 5.
- Each reason names something in the view.
