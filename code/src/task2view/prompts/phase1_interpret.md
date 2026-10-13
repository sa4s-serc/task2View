---
id: phase1_interpret
phase: "1 — Stakeholder-task interpretation"
called_from: task2view/phase1/needs.py (extract_needs)
purpose: >-
  Turn a free-text stakeholder goal into a fixed-vocabulary profile: the person's role, the
  target, the information needs (primary or secondary), the enumerated subjects, and the stressed
  quality attributes. Viewpoint selection (Phase 3) is computed from this profile by code.
inputs:
  goal: the stakeholder goal, verbatim
  needs: the 23 information needs with definitions and example wording (knowledge/data/vb/needs.yaml)
  roles: the stakeholder roles with alternative names (knowledge/data/vb/roles.yaml)
  qualities: ISO/IEC 25010 quality attribute ids
output: JSON {role_label, role, target, needs[{need, evidence, salience}], subjects[{text, needs}], quality_attributes, clarifications[{field, question, default}]}
checked_by: >-
  validate_needs drops any need, subject or target whose words are not in the goal, and any id not
  in the vocabulary, and records each drop. The detail level is computed afterwards from the
  checked profile, not asked of the model. Clarifications are kept only for the three spec fields with
  allowed defaults (at most 3); without a person to ask, the defaults are used.
---
# Task2View — Phase 1: Stakeholder-task interpretation

## Role
You read a stakeholder's request for architecture documentation and record what they need, using a fixed vocabulary.

## Task
Record who the person is, what part of the system they are asking about, and which kinds of architectural information they need to see.
You do not choose diagrams. A program chooses them from your answer, and every need you list can add a diagram. So list exactly what the request asks for, nothing more and nothing less.

## Inputs

### The request (the only text you interpret)
<request>
{{goal}}
</request>

### Information needs (use only these ids)
{{needs}}

### Roles (use only these ids)
{{roles}}

### Quality attributes (use only these ids)
{{qualities}}

## Rules
1. **role_label** is the words the person uses for themselves. **role** is one role id, or null if none fits.
   *Why:* the original words are kept for the record; the id makes requests comparable.
2. **target** is the feature, subsystem or system the request is about, copied exactly as a short noun phrase. Use "" if it is the whole system.
3. **needs**: list every information need the request asks for. For each one give:
   - **need**: an id from the list.
   - **evidence**: the exact words from the request that ask for it, copied character for character.
   - **salience**: "primary" if the request is about this (it says the person needs to understand, identify or see it); "secondary" if it is only mentioned in passing, is context, or is implied by a primary need.

   How to decide:
   - A need is information the person asks to **see**. Words that only name the thing they will work on, or describe their situation, are not a need. For example, "I will change the persistence layer" names their work; it does not ask how the system is layered.
   - **Structural** needs ask which parts exist and how they relate. **Behavioural** needs (interaction-order, process-flow, lifecycle, actors-goals) ask what happens: the order of steps, the flow of a process, the states something goes through, or who uses the system for what. List a behavioural need only when the request asks about that dynamic aspect.
   - **People** who use the system belong to actors-goals. **Software parts** that work together belong to collaboration.

   *Why:* only primary needs can add a diagram. A need nobody asked for adds a diagram nobody wanted, and a missed primary need leaves the person without the view they asked for.
4. **subjects** are the specific items the request enumerates as things to understand, for example a list of sub-functions, data items or cases. Copy each exactly and give the need ids it belongs to. The system, the feature being changed and the person are not subjects. A request that enumerates nothing has no subjects.
   *Why:* every subject must appear in a view, so the details of a long request are not lost.
5. **quality_attributes** are quality ids the request stresses, or an empty list. They never choose diagrams.
6. **clarifications**: questions for the person, only where the request leaves one of these open, at most 3, usually none:
   - `scope`: whole system ("system") or one feature ("feature");
   - `granularity`: big blocks ("coarse"), the main parts ("medium") or individual classes ("fine");
   - `behaviour`: parts only ("structure"), order of calls only ("interaction"), or both ("both").

   Give each as `{"field": ..., "question": "...", "default": ...}`, with the default being your best reading of the request.
   *Why:* asking only when it matters improves the result; asking about what the request already says wastes the person's time.

## Output
Return one JSON object and nothing else, in this shape:
```json
{
  "role_label": "integration tester",
  "role": "tester",
  "target": "order checkout",
  "needs": [
    {"need": "collaboration", "evidence": "which components are involved", "salience": "primary"},
    {"need": "interaction-order", "evidence": "in which order they are called", "salience": "primary"}
  ],
  "subjects": [
    {"text": "retrying a declined card payment", "needs": ["interaction-order"]}
  ],
  "quality_attributes": [],
  "clarifications": [
    {"field": "behaviour", "question": "Do you also want the order in which they are called, or only which parts are involved?", "default": "both"}
  ]
}
```
The example shows the shape only; your values must come from the request above.

## Check before answering
- Every `evidence`, `text` and `target` appears word for word in the request.
- Every need, role and quality id is from the lists above.
- Each behavioural need is there because the request asks how something happens, not because a word looked similar.
- Nothing is marked primary that the request only mentions in passing.
- Each clarification is about something the request really leaves open; most requests need none.
