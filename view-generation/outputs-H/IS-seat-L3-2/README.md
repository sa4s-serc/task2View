# Seat booking: UML package diagram (module viewpoint, balanced)

**Takeaway:** a booking request enters through the Swing client or REST API, passes the Library Facade and is decided in the Reservation Manager. It checks seats with the Reservation Domain Model and Reservation Registry. Reminder emails leave through the Notification Manager and its adapter.

Stakeholder: developer adding booking rules. Detail level: balanced (as given): the modules involved in booking, grouped in their layer packages, with their dependencies. Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation).

## How the concern is answered
- **Components and responsibilities:** each package box is a module; the layer packages are Presentation, Application, Domain and registries, Persistence. Responsibilities are in `inventory.json`.
- **Interaction and dependencies:** the dashed arrows are dependencies, drawn from dependent to dependency and read top to bottom.
- **Handle booking requests:** Swing Desktop Client, REST API, Library Facade, Reservation Manager.
- **Check seat availability:** Reservation Domain Model (Seat.isAvailable), Reservation Registry (occupiesSlot: active or confirmed reservations block a seat) and Study Room Registry. Study Room Manager counts free seats for browsing and builds a seat status map for librarian monitoring, which reuses occupiesSlot; it is not a separate booking check.
- **Apply booking rules:** rules are spread over four places: Reservation Manager (room open and active, area, seat in area), Reservation Domain Model (one booking per slot, via the Student check), Reservation Registry (occupiesSlot: which states block a seat) and Seat Assignment Strategy (seat choice). User Registry only looks up students.
- **Manage and store reservations:** Reservation Manager (saves), Reservation Registry (stores), Persistence Manager (MySQL); Notification Manager also updates reservations (reminder flag). User Registry stores students, not reservations.
- **External services:** Notification Manager, the NotificationService interface (realized by Email Notification Adapter), External email gateway (stub); Notification Scheduler triggers expiry and reminders.
- **What to change and what is affected:** blue = likely changed (Reservation Manager, Seat Assignment Strategy, Domain Model, Reservation Registry); red = may be affected (Study Room Manager, Notification Manager, User Registry). Red also marks Library Facade, REST API and Swing client: they pass request data and error messages, so new rules needing new input reach them.

Names and styling match the earlier component view (IS-seat-L3).

## Omitted on purpose
DTOs, the MySQL database, users, librarian use cases, login and registration, state classes, and undrawn dependencies listed in `inventory.json` under `omitted` (for example adapter to Swing start-up wiring, Notification Manager to Study Room Manager for room deletion).

## Assumptions
Modules are Java classes or packages shown as UML packages; the four layer packages follow the repository graph layers.

## Revision after review (v1/ holds the previous version)
- Every module now carries a one-line responsibility; rule locations (Student check, occupiesSlot) are labelled.
- Added Notification Manager to Reservation Registry (marks reminders); Scheduler label now says expiry and reminders.
- NotificationService is a UML interface with a realization from the adapter; booking-path dependencies are dashed. Legend states that arrows are use dependencies and that boxes are classes or groups of classes. Decision: I did not print «use» on each edge, because it widened the diagram past the one-screen limit.
- Facade, REST API and Swing are marked as possibly affected.
- README corrected: User Registry no longer listed under storing reservations; Study Room Manager occupancy described as monitoring.
- Dropped the Study Room Manager to Study Room Registry edge (listed under omitted) to reduce crossings. Kept the three "opens sessions" edges: each is a real code dependency.

## Check results
- `puml-check`: 6 warnings (labels on container borders, edges crossing container titles); v1 had 3 but empty boxes. `check_view.py`: one issue left: the view is 2389 px wide, so text shrinks to 8 px on a 1600 px screen. Several layout attempts (stacking, left to right, norank) were no better, and the added responsibility text costs width. Not fixed.
- `check_inventory.py --level balanced`: 0 issues. `check_consistency.py`: consistent.
