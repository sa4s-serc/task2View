# UML sequence diagram: main functionalities across the layers (overview)

**Takeaway:** every main function runs the same chain: Boundary screens call Control, Control calls Entity services, Entity calls Database, Database talks to MySQL.

Stakeholder: software architect reviewing the organisation before planning evolution. Detail level: overview (given), so lifelines are the four layers, the user and the external database, not classes. Names match the module (GR10-Q1) and component (GR10-Q1-2) views.

## How the view answers the concern
"How do these parts collaborate to provide the main functionalities?" Three flows are drawn, ordered by lifelines left to right:
- **Sign in**: Boundary calls the login controller directly (not the facade); Control asks Entity, which reads via Database.
- **Citizen reports a problem**: one `alt` shows the error path: Control validates the data and the citizen role; if invalid it rejects and Boundary shows the message, otherwise Entity saves the report through Database in a transaction.
- **Operator advances status**: Boundary → Control → Entity updates the report and, if the status is notifiable, saves a notification for the citizen.

Details are in `inventory.json` (check_inventory.py: 0 issues; 2 notes: one undrawn dependency, two elements without members).

## Omitted on purpose
Individual controllers, services, entities, forms; the other functions (registration, review, notes, monitoring), which follow the same chain; the JPA library; Boundary's direct use of the ReportCategory enum from Entity (data type, not a step; see the other views).

## Assumptions
- Internal calls inside one layer are collapsed into one message.
- Reply arrows are drawn only where a result matters to the flow.
- A different (balanced) level would show the facade, per-use-case controllers and the notification controller.

## Check results
puml-check: clean (one info on a group label); check_view.py: clean; check_consistency.py: consistent. View rendered to `view.png`.
