# Output files

Write these files under `--out`, with exactly these names and fields. They are the files the Task2View pipeline writes (`code/src/task2view/agents/write_v2.py`), so runs can be compared file by file. Values below are illustrative.

```
<out>/
  repository_card.txt          repository_card.json
  stakeholder_profile.json     view_plan.json
  architectural_questions.json investigation_plan.json
  evidence_model.json          reconciliation.json
  viewset.json                 validation_report.json
  traceability.md              README.md
  usage.json                   (tokens and cost; agents: what your tool reports, else omit)
  run.log                      (pipeline only: one line per phase decision)
  V1-<viewpoint id>/view.json  V1-<viewpoint id>/view.puml   (one folder per view)
  V1-<viewpoint id>/architecture.json                       (structural views: parts with member classes, arrows with code evidence)
  V1-<viewpoint id>/view.<notation>.<ext>                   (each further notation asked for)
  V1-<viewpoint id>/render_notes.json                       (only when a notation could not draw something)
```

## repository_card.json
```json
{"root": ".", "name": "repo-name", "languages": {"java": 40},
 "layers": {"presentation": ["com.example.web"], "application": ["com.example.service"]},
 "entry_points": [{"kind": "http-route", "symbol": "com.example.web.OrderController", "file": "src/…/OrderController.java", "line": 14, "detail": "PostMapping /orders/{id}/pay"}],
 "entities": [{"symbol": "com.example.domain.Order", "name": "Order", "table": "orders", "source": "orm", "file": "src/…/Order.java",
               "fields": [{"name": "id", "type": "Long", "key": true, "relation": null, "target": null, "foreign_key": null}]}],
 "deploy": [{"kind": "compose-service", "name": "db", "file": "docker-compose.yml", "details": {"image": "postgres:16"}}],
 "build": [{"tool": "maven", "file": "pom.xml", "name": "shop-service", "packaging": "jar", "dependencies": ["postgresql"]}],
 "signals": {"rest-api": ["com.example.web.OrderController: PostMapping /orders/{id}/pay"], "layered": ["presentation: com.example.web"]},
 "notes": []}
```
`repository_card.txt` is a short readable summary of the same facts.

## stakeholder_profile.json
```json
{"goal": "<verbatim goal>", "role_label": "integration tester", "role": "tester", "target": "order checkout",
 "needs": [{"need": "collaboration", "evidence": "<exact words>", "salience": "primary"}],
 "subjects": [{"text": "<exact words>", "needs": ["interaction-order"]}],
 "quality_attributes": [], "detail_level": "feature", "dropped": []}
```

## view_plan.json
```json
{"views": [{"viewpoint_id": "client-server", "family": "cnc", "model_kind": "uml-component",
            "needs": ["collaboration"], "subjects": [], "overlays": ["layered"], "specialised_from": "cnc-generic",
            "detail_level": "feature", "granularity": {"max_elements": 10}, "evidence_gap": null,
            "rationale": "Client-Server (4.3.1 Client-Server Style) covers collaboration; specialised from cnc-generic because the repository shows rest-api; combined with layered (V&B 6.6)"}],
 "needs": ["collaboration"], "secondary_needs": [], "needs_from_role": false,
 "uncovered_needs": [], "secondary_not_shown": [], "detail_level": "feature", "notes": []}
```

## architectural_questions.json
```json
[{"id": "AQ1", "view_id": "V1-client-server", "viewpoint_id": "client-server", "need": "collaboration", "subject": null,
  "element_kinds": ["component", "interface", "datastore", "external_system"], "relation_kinds": ["request-reply", "uses", "reads", "writes"],
  "fragments": [], "text": "For order checkout: which parts work together for a feature and through which interfaces or connectors?"}]
```

## investigation_plan.json
```json
[{"id": "IT1", "view_id": "V1-client-server", "viewpoint_id": "client-server", "question_ids": ["AQ1"], "need": "collaboration",
  "subject": null, "goal": "Collect evidence for: …", "seeds": {"symbols": ["com.example.orders.OrderService"], "paths": [], "classes": ["code", "config", "web"]},
  "expect_elements": ["component", "…"], "expect_relations": ["uses", "…"], "budget_steps": 10, "suggested_by": ["symbol-name", "entry-point:http-route"]}]
```

## evidence_model.json
```json
{"claims": {"C1": {"id": "C1", "task": "IT1", "kind": "element", "element_kind": "component", "name": "OrderService",
                    "symbol": "com.example.orders.OrderService", "responsibilities": ["validates that an order can be paid"], "attributes": [],
                    "source": null, "target": null, "relation": null, "label": null, "order": null, "scenario": null, "condition": null,
                    "evidence": [{"file": "src/…/OrderService.java", "symbol": null, "lines": [41, 43], "excerpt": "if (order.getStatus() != OrderStatus.NEW) {"}],
                    "support": "observed", "confidence": 0.9, "question_ids": ["AQ1"]}},
 "rejected_claims": [{"task": "IT1", "claim": {"…": "…"}, "reason": "src/…: excerpt not found at lines [10, 10]"}],
 "elements": {"cmp:com.example.orders.OrderService": {"id": "cmp:com.example.orders.OrderService", "kind": "component", "name": "OrderService",
               "realized_by": ["com.example.orders.OrderService"], "layer": "application",
               "responsibilities": [{"text": "validates that an order can be paid", "claims": ["C1"]}],
               "attributes": [], "details": {}, "support": "observed", "claims": ["C1"], "named_by": "symbol"}},
 "relations": {"rel:…": {"id": "rel:…", "kind": "uses", "source": "cmp:…OrderController", "target": "cmp:…OrderService", "label": "pay",
                "multiplicity": null, "member_edges": ["…OrderController -calls-> …OrderService (src/…:15)"], "claims": [], "support": "observed"}},
 "scenarios": {"scn:pay-order": {"id": "scn:pay-order", "name": "pay order",
               "steps": [{"order": 1, "source": "cmp:…OrderController", "target": "cmp:…OrderService", "message": "pay(id)", "kind": "call", "fragment": null, "claims": ["C3"]}],
               "fragments": [{"id": "scn:pay-order:alt1", "kind": "alt", "guard": "order status is NEW"}]}},
 "component_of": {"com.example.orders.OrderService": "cmp:com.example.orders.OrderService"},
 "correspondences": [{"rule": "entity-realized-by-component", "elements": ["ent:…Order", "cmp:…Order"], "note": ""}],
 "reflexion": {"convergence": ["rel:…"], "divergence": ["rel:…"], "absence": []},
 "notes": ["IT1: 6 claims, read 3 files; read 3, search 2, symbol 1"]}
```

## reconciliation.json
```json
{"V1-client-server": {"view_id": "V1-client-server", "decision": "confirm", "reason": "all assigned questions have evidence in the view",
                      "coverage": [{"question": "AQ1", "status": "supported", "claims": ["C1", "C2"], "note": ""}], "unsupported_questions": []}}
```

## V*/view.json (one per view; viewset.json holds all of them)
```json
{"id": "V1-client-server", "viewpoint_id": "client-server", "viewpoint_name": "Client-Server", "vb_ref": "4.3.1 Client-Server Style",
 "model_kind": "uml-component", "title": "Client-Server view — order checkout", "purpose": "…", "detail_level": "feature", "max_elements": 10,
 "addresses": ["AQ1"], "overlays": ["layered"], "scenario": null,
 "elements": [{"id": "group:layer:application", "kind": "layer", "name": "Application", "stereotype": null, "parent": null,
               "responsibilities": [], "attributes": [], "realized_by": [], "support": "observed", "group": true},
              {"id": "cmp:com.example.orders.OrderService", "kind": "component", "name": "OrderService", "stereotype": "application",
               "parent": "group:layer:application", "responsibilities": ["validates that an order can be paid"], "attributes": [],
               "realized_by": ["com.example.orders.OrderService"], "support": "observed", "group": false}],
 "relations": [{"id": "rel:…", "kind": "uses", "source": "cmp:…", "target": "cmp:…", "label": "pay", "multiplicity": null, "support": "observed"}],
 "interactions": [{"order": 1, "source": "cmp:…", "target": "cmp:…", "message": "pay(id)", "kind": "call", "fragment": null}],
 "fragments": [{"id": "scn:pay-order:alt1", "kind": "alt", "guard": "order status is NEW"}],
 "traceability": [{"element": "cmp:…OrderService", "name": "OrderService", "files": ["src/…/OrderService.java"], "symbols": ["com.example.orders.OrderService"]}],
 "limitations": [], "gaps": [], "overflow": []}
```
`viewset.json`:
```json
{"system": "repo-name", "stakeholder": "tester", "goal": "<verbatim>", "views": [ … ],
 "correspondences": [{"rule": "same-element", "elements": ["V1-client-server:cmp:…", "V2-sequence:cmp:…"]}],
 "correspondence_gaps": [], "declared_gaps": [], "uncovered_needs": [], "secondary_not_shown": []}
```

## validation_report.json
```json
{"V1-client-server": {"view_id": "V1-client-server", "verdict": "pass_with_limitations",
  "notation": {"status": "pass", "language": "plantuml", "approximated": false, "model_kind_matches": true},
  "constraints": [{"constraint": "component_has_responsibility", "severity": "warning", "mark": "cmp:…", "message": "… shows no responsibility"}],
  "faithfulness": [], "coverage": [{"question": "AQ1", "status": "supported", "claims": ["C1"], "note": ""}],
  "readability": [{"check": "crossings", "severity": "warning", "mark": "view", "message": "3 crossing arrows in the layered layout"}],
  "metrics": {"parts": 7, "arrows": 7, "crossings": 3, "against_layering": 1, "omitted_relations": 1, "classes_behind_parts": 39},
  "errors": 0, "warnings": 1, "repair_marks": []}}
```

## usage.json
The pipeline records every model call (purpose, model, tokens, seconds, cost) and totals per phase and model. An agent condition writes what its tool reports (for example Claude Code's `/cost`), or leaves the file out, and states that in README.md.
```json
{"total": {"calls": 42, "input_tokens": 512000, "output_tokens": 18000, "cache_read_tokens": 0, "cache_write_tokens": 0,
           "seconds": 310.2, "cost_usd": 1.806, "cost_complete": true},
 "by_phase": {"phase1": {"…": "…"}, "phase5": {"…": "…"}}, "by_model": {"anthropic:claude-sonnet-5-5": {"…": "…"}},
 "pricing_source": "https://platform.claude.com/docs/en/about-claude/pricing (read 2026-10-09)", "calls": [ … ]}
```

## traceability.md and README.md
`traceability.md`: per view, a table `| Element | Files | Symbols |`.

`README.md` has these parts:
- goal, role, target, detail level, primary and secondary needs, and the model you are;
- a table of views (viewpoint, decision, verdict, element count, notation);
- the rationale per view;
- limitations and declared gaps;
- evidence counts (verified and rejected claims, elements, relations, scenarios).
