# Output schemas

Match these shapes so a single-agent run can be compared file-for-file with Task2View.

Allowed `kind` for elements: `actor`, `component`, `module`, `class`, `service`, `datastore`, `external_system`, `deployment_node`, `state`, `system`.

Allowed `kind` for relations: `uses`, `calls`, `call`, `return`, `depends`, `dataflow`, `inherits`, `implements`, `contains`, `deploys`, `transition`.

Allowed `view_type`: `sequence_view`, `component_view`, `deployment_view`, `class_view`, `state_view`, `dataflow_view`, `context_view`.

## stakeholder_task_profile.json

```json
{
  "stakeholder": "member-of-development-team",
  "canonical_role": "member-of-development-team",
  "original_label": "software developer",
  "task": "modify the seat booking functionality",
  "target": "seat booking functionality",
  "goal": "understand the main system components involved and how they interact",
  "scope": "",
  "constraints": [],
  "confidence": 0.9,
  "source_goal": "<verbatim user goal>",
  "concerns": ["maintainability", "control-flow", "connectivity"],
  "environment": ""
}
```

## architectural_questions.json

```json
{
  "concerns": ["maintainability", "control-flow"],
  "questions": [
    {"id": "AQ1", "text": "Which module owns …?", "concern": "maintainability", "priority": 1}
  ]
}
```

## correspondence.json

```json
{
  "role_id": "member-of-development-team",
  "stakeholder_name": "Member of development team",
  "viewpoint_id": "module-decomposition",
  "view_type": "component_view",
  "task_focus": "seat booking",
  "concerns": ["maintainability"],
  "task_concerns": ["maintainability"],
  "preferred_viewpoints": ["module-decomposition", "code-mapping"],
  "phrases": ["modify", "main components involved"],
  "task": "modify the seat booking functionality",
  "purpose": "Module Decomposition View for seat booking: modules named by responsibility…",
  "unanswered_concerns": ["control-flow", "connectivity"],
  "decided_by": "model",
  "grain": {
    "viewpoint_id": "module-decomposition",
    "unit": "component",
    "nodes": "modules or subsystems that own the task, named by responsibility",
    "relations": "containment or uses",
    "forbid": "one box per source file; class inventory"
  },
  "ranked": [
    {"viewpoint_id": "module-decomposition", "view_type": "component_view", "score": 10.0, "reasons": ["task-cue preferred viewpoint"]}
  ]
}
```

## viewpoint_plan.json

```json
{
  "views": [
    {
      "id": "V1",
      "viewpoint_id": "module-decomposition",
      "view_type": "component_view",
      "notation": "Component Diagram",
      "diagram_language": "plantuml",
      "granularity": "component_or_service_level",
      "purpose": "Module Decomposition View for seat booking: modules or subsystems that own the task, named by responsibility. Relations: containment or uses. Do not: one box per source file; class inventory.",
      "addresses": [],
      "required_evidence": ["modules named by responsibility", "containment or uses"],
      "deferred": false
    }
  ],
  "notes": ["Eligible because they frame the chosen concerns: module-decomposition, cnc-runtime"]
}
```

Notation labels: sequence_view → UML Sequence Diagram; component_view → Component Diagram; deployment_view → Deployment Diagram; class_view → Class Diagram; context_view → System Context Diagram; dataflow_view → Data Flow Diagram.

Granularity: high → `system_or_context_level`; medium → `component_or_service_level`; low → `class_or_code_level`.

## view_specification.json

```json
{
  "request_id": "IS-seat-L1",
  "stakeholder": "member-of-development-team",
  "task_summary": "<goal | task | target | understanding>",
  "architectural_concerns": ["maintainability"],
  "selected_view": {
    "view_type": "component_view",
    "notation": "Component Diagram",
    "diagram_language": "plantuml",
    "granularity": "component_or_service_level",
    "purpose": "…",
    "viewpoint_id": "module-decomposition",
    "grain_unit": "component"
  },
  "required_information": [
    {"id": "RI-1", "need": "top-level modules and their responsibilities"}
  ],
  "declared_gaps": [],
  "unanswered_concerns": []
}
```

## repository_scope.json

```json
{
  "request_id": "IS-seat-L1",
  "strategy": "single-agent",
  "files": [
    {"path": "src/…/ReservationManager.java", "reason": "owns booking rules"}
  ]
}
```

Keep ≤ 16 files.

## view_model.json

```json
{
  "request_id": "IS-seat-L1",
  "view_type": "component_view",
  "granularity": "component_or_service_level",
  "groups": [],
  "elements": [
    {
      "id": "E1",
      "name": "ReservationManager",
      "kind": "component",
      "role": "applies booking rules and stores reservations",
      "external": false,
      "evidence": {"file": "src/…/ReservationManager.java", "symbol": "ReservationManager", "excerpt": "public class ReservationManager"},
      "support": "observed",
      "agreement": 1.0
    }
  ],
  "relations": [
    {
      "id": "R1",
      "from": "E1",
      "to": "E2",
      "kind": "uses",
      "label": "createReservation",
      "order": null,
      "evidence": {"file": "src/…/ReservationManager.java", "symbol": "createReservation", "excerpt": "reservationDao.save"},
      "support": "observed",
      "agreement": 1.0
    }
  ],
  "unanswered": [],
  "notes": []
}
```

Relation field is `from` (not `frm`).

## structure_report.json

```json
{
  "request_id": "IS-seat-L1",
  "answered_questions": ["AQ1", "AQ2"],
  "unanswered_questions": ["AQ5"],
  "answered_information": ["RI-1", "RI-3"],
  "unanswered_information": ["RI-2"],
  "package_shaped_names": [],
  "notes": []
}
```

## validation_report.json

```json
{
  "request_id": "IS-seat-L1",
  "notation": "plantuml",
  "syntax": {"status": "pass", "attempts": 1},
  "semantic": {
    "elements_resolved": "8/8",
    "relations_resolved": "10/10",
    "unsupported": [],
    "unresolved_elements": [],
    "granularity_violations": [],
    "unanswered_information": [],
    "unanswered_concerns": ["control-flow"],
    "scope_files": 16,
    "misplaced_groups": []
  },
  "verdict": "pass"
}
```
