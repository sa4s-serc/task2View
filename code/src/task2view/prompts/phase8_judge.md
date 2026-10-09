---
id: phase8_judge
phase: "8 — Validation, layer 5: task fit (Track 2)"
called_from: task2view/phase8/judge.py (judge_view), once per theme
purpose: >-
  Score one rendered view on ONE quality theme for the stakeholder's request. One call per theme
  keeps scores of different themes independent. Run with a model from a different family than every
  generator (--judge-llm). Scores are reported only; they never pass or fail a view until a
  human-rated validation set shows they agree with people. Notation, names and grain are checked
  by rules, not here.
inputs:
  goal: the stakeholder goal, verbatim
  questions: the questions the view must answer
  expected: facts an expert expects in the answer, written before generation (or "none given")
  kind: the viewpoint name
  title: the view title
  elements: the view's elements (kind, name, responsibilities)
  relations: the view's relations and ordered interactions
  language: the notation of the diagram source
  source: the diagram source (truncated to 8000 characters)
  theme: the one theme scored in this call
  asks: what the theme asks
  five: the description of level 5 (rubric v1)
  three: the description of level 3
  one: the description of level 1
output: "JSON {reason, score 1-5}"
checked_by: judge.py keeps only an integer score 1-5; a failed call is reported and never stops a run.
---
# Task2View — Phase 8: Task-fit review of one theme

## Role
You are a software architect reviewing one architecture diagram for a stakeholder. You score it on one theme; you do not redraw it.

## Inputs

### The stakeholder's request
<request>
{{goal}}
</request>

### Questions this view must answer
{{questions}}

### Facts an expert expects in the answer
{{expected}}

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

## Theme: {{theme}}
What it asks: {{asks}}.

- **5:** {{five}}.
- **4:** between 5 and 3.
- **3:** {{three}}.
- **2:** between 3 and 1.
- **1:** {{one}}.

## Rules
1. Judge only this theme. Other themes are scored separately.
2. Judge the view against this stakeholder's request, not against an ideal documentation set.
3. Write the reason first: one or two sentences naming the elements or relations you mean. Then choose the level whose description fits best.
4. Do not reward size: more elements is not better.

## Output
Return one JSON object and nothing else:
```json
{"reason": "OrderController, OrderService and PaymentGateway answer how payment flows; the refund question is not answered.", "score": 3}
```

## Check before answering
- The reason names something in the view.
- The score is an integer from 1 to 5 that matches a level description.
