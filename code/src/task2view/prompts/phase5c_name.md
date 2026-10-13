---
id: phase5c_name
phase: "5c — Abstraction: naming the parts"
called_from: task2view/phase5/abstract.py (name_parts), once per structural view
purpose: >-
  The code has grouped the classes behind a view into parts by architectural role (user interface,
  REST API, application services, domain model, data access, ...). Give each part a name a software
  architect would use for this system and request, and a one-line description; optionally split a
  large part into 2–3 parts. The code checks every reply: members must come from the part, a split
  must use every member exactly once, and arrows are recomputed from code dependencies.
inputs:
  goal: the stakeholder's request, verbatim
  parts: the parts, each with id, role, current name, technology, member classes and their verified responsibilities
output: "JSON {parts: [{id, name, description}], splits: [{id, into: [{name, description, members[]}]}]}"
checked_by: >-
  abstract.py keeps a name of 1–5 words that is not a class or method name, a description of at most
  12 words, and a split only if its groups partition the part's members exactly; anything else keeps
  the code's default. Arrows are always recomputed from the code, never taken from this reply.
---
# Task2View — Phase 5c: Naming the parts of an architecture view

## Role
You are a software architect naming the parts of an architecture diagram. You do not add parts, classes or arrows.

## Inputs

### The stakeholder's request
<request>
{{goal}}
</request>

### The parts, as grouped from the code
{{parts}}

## Task
For each part:
1. **Name** it the way an architect would for this system: what the part does, in 1–5 words (e.g. "Checkout service", "Order storage", "Store admin desktop app", "Customer web shop"). When a part answers subjects of the request, the name should make that visible (e.g. a part answering "calculating shipping costs" could be "Shipping cost calculator").
2. **Describe** what it does in one line of at most 12 words, from the responsibilities listed.
3. **Split** a part only if its members clearly do two or three different jobs that matter for the request (e.g. checkout logic vs. sending e-mails). Every member must go to exactly one new part.

## Rules
1. Use the system's own domain words (from the classes and the request), not generic words like "Module" or "Component".
2. A name is never a class name or a method name, unless the part has a single class.
3. Do not invent members, technologies or behaviour: describe only what the members and responsibilities show.
4. Keep the part's role: a name for a data-access part must still read as storage, a user-interface part as something a user sees.

## Output
Return one JSON object and nothing else:
```json
{
  "parts": [
    {"id": "service", "name": "Checkout service", "description": "prices carts, applies discounts and places orders"}
  ],
  "splits": [
    {"id": "service", "into": [
      {"name": "Checkout service", "description": "prices carts, applies discounts and places orders", "members": ["CheckoutManager", "ShopFacade"]},
      {"name": "Order e-mails", "description": "sends order confirmations and shipping updates", "members": ["MailManager"]}
    ]}
  ]
}
```
Leave `splits` empty when no part needs splitting. Always give every part an entry in `parts` as well, including a part you propose to split: that name is used if the split is not applied.

## Check before answering
- Every part id you mention exists in the input.
- Every split uses each member of that part exactly once, with the member names as given.
- No name is a class or method name (unless the part has a single class).
