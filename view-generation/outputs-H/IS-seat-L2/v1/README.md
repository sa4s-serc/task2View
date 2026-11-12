# Seat booking: component view (UML component diagram, balanced)

**Takeaway:** every seat booking goes through the Library facade to the Reservation manager, which holds the booking rules and delegates seat choice to a strategy, so new rules mostly touch that manager (and the strategy), with knock-on effects on the entry points, availability display and the model.

Stakeholder: developer changing the booking rules. Detail level: balanced (given), so components and their interfaces, not classes. A detailed level would add the manager's validation steps (`ReservationManager.java:65-102`) and registry queries.

## How it answers the concern
- **Main components:** the Entry points (desktop screens, REST API, scheduler), Library facade, Reservation manager, Room availability manager, Notification manager, Seat assignment strategy, Registries, Reservation and seat model, Persistence manager, database.
- **Responsibilities:** one sentence per component in `inventory.json`. Rules (validation, uniqueness per student/slot, seat choice, saving, notification) live in the Reservation manager.
- **Interactions:** arrows run from caller to dependency, top to bottom. Facade operations and Seat selection are interfaces; the database is reached through JPA.
- **Change impact:** a new rule most likely changes Reservation manager and possibly Seat assignment strategy. It may also affect the Reservation and seat model (new fields/states), Registries (new queries), Room availability manager (seat availability shown to users must stay consistent), the Facade operations signature plus the desktop screens and REST API (new request parameters or errors), and Notification manager. Tests exist for booking, cancel, check-in and expiry (`src/test/.../MakeReservationTest.java`).

## Details
- `inventory.json`: elements, relations, evidence. `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (9 notes: undrawn dependencies, listed under omitted; the unchecked actors, database and interfaces have no code members).
- `check_view.py`: clean. `puml-check`: one warning left (an edge touches the title tab of "Domain and persistence"); crossings 3, no overlaps.
- Omitted: DTOs, user management and factories, email gateway adapter, Swing wizard helpers, entity dependencies of the room manager, notification manager and strategy.

## Assumptions
- The Room availability manager is shown as a separate component because it computes available seats and statuses that bookings must match; the booking manager itself reads rooms through the registries.
- Student and librarian both use the desktop screens (Swing); the REST API caller is not drawn because the code shows no client.
