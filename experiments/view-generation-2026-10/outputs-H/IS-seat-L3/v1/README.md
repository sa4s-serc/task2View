# Seat booking: components and dependencies (UML component diagram)

**Takeaway:** a booking request enters through the Swing client or REST API, passes the Library Facade, and is handled by the **Reservation Manager**. It applies the booking rules, uses the domain model for seat availability and the Seat Assignment Strategy to choose a seat, and stores the result in the Reservation Registry. Notifications go out through the Notification Manager and the email adapter.

Stakeholder: software developer changing the booking rules. Detail level: **balanced** (as given). A detailed level would add the individual private validation steps of `ReservationManager.makeReservation` and the reservation state classes.

Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation).

## How the view answers the concern
- **Main components and responsibilities**: each box is one component; the responsibilities are in `inventory.json`.
- **Interactions and dependencies**: arrows point from caller to dependency, top to bottom: presentation, application, domain and registries, database.
- **Handle booking requests**: Swing Desktop Client and REST API receive them, Library Facade routes them, Reservation Manager executes them.
- **Check seat availability**: Reservation Domain Model (`Seat.isAvailable`, `Area.getAvailableSeats`), which queries the Reservation Registry; the Study Room Manager uses the same checks to count free seats for browsing.
- **Apply booking rules**: Reservation Manager (room, area, time slot, one booking per slot, seat checks), Seat Assignment Strategy (automatic seat choice), and the domain model (reservation states, check-in tolerance).
- **Manage and store reservations**: Reservation Registry, Persistence Manager, MySQL database; the lifecycle itself lives in the domain model.
- **External services**: Notification Manager, Email Notification Adapter and the external email gateway (a stub that only prints and returns 200); the Notification Scheduler triggers expiry and reminders.
- **What to change / what is affected**: the blue components are the likely change points (Reservation Manager, Seat Assignment Strategy, Reservation Domain Model, Reservation Registry). Likely affected: Library Facade and both clients (if the request or its error messages change), Study Room Manager (shares availability logic), Notification Manager (new messages or states).

## Omitted on purpose
User Manager, User Registry and factories; DTOs; librarian functions (room creation, monitoring); the Librarian actor, since librarians do not book. Undrawn dependencies are listed in `inventory.json` under `omitted`.

## Assumptions
- The Domain Model groups the entities, including Seat and Area, with the reservation state classes. Availability logic lives in the entities, not in a separate service.
- The Library Facade and the managers are singletons, which is not shown.

## Check results
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (7 notes: undrawn dependencies recorded as omitted, and elements without members).
- `check_view.py`: clean.
- `puml-check`: two warnings remain: aspect ratio 1.21 (tall, the layered layout needs it), and one edge crossing the "Domain and registries" title. No overlapping labels.
