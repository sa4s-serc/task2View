# UML sequence diagram: main functionalities across the layers (overview)

**Takeaway:** every main function runs the same chain: Boundary screens call Control, Control calls Entity services, Entity calls Database, Database talks to MySQL. Control also decides when a follow-up call (the notification) is made.

Stakeholder: software architect reviewing the organisation before planning evolution. Detail level: overview (given). Lifelines stand for whole layers (packages), not class instances, plus the user and the external MySQL database; this is the overview abstraction. Names match the module (GR10-Q1) and component (GR10-Q1-2) views.

## How the view answers the concern
"How do these parts collaborate to provide the main functionalities?" Three flows, lifelines left to right in calling order:
- **Sign in**: Boundary calls the login controller directly (not the facade); Control asks Entity, which reads via Database. Results return to Control and then Boundary, so "dashboard or error" follows from the reply (session data or none).
- **Citizen reports a problem**: `alt`: Control validates the data and the citizen role; if invalid it rejects with a message, otherwise Entity saves the report through Database in a transaction.
- **Operator advances status**: `alt allowed` / `else not allowed`. Not allowed means: not an operator, report not found, or report already resolved (all checked in Control). When allowed, Control makes two separate calls to Entity: (1) apply the new status, one update transaction; (2) inside `opt status notifiable`, check the status and generate the notification, a second, separate transaction. The notify decision is made in Control (notification controller), not in Entity.

Details are in `inventory.json` (check_inventory.py: 0 issues; notes: one undrawn dependency, two elements without members).

## Omitted on purpose
Individual controllers, services, entities, forms and the facade; the other functions (registration, review of received reports, notes, monitoring), which follow the same chain; the JPA library; Boundary's direct use of the `ReportCategory` enum from Entity (data type, not a step; see the other views). A balanced level would name the facade, the per-use-case controllers and the notification controller.

## Assumptions
- Internal calls inside one layer are collapsed into one message.
- Replies are drawn where a result drives the outcome.

## Revision (after critique-1)
Previous version is in `v1/`. Changed: status flow split into the two Control-to-Entity calls with separate transactions; the note replaced by an `opt [status notifiable]` fragment owned by Control; rejection `alt` added to the status flow; sign-in replies added; lifelines described as layers. Not adopted: renaming lifelines to `:Layer` form, to keep names identical to the other views.

## Check results
puml-check: OK (infos on group labels only); check_view.py: clean; check_consistency.py: consistent; check_inventory.py: 0 issues. Rendered to `view.png`.
