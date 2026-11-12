# Seat booking: UML package diagram (module viewpoint, balanced)

**Takeaway:** a booking request enters through the Swing client or REST API, passes the Library Facade and is decided in the Reservation Manager. It checks seats with the Reservation Domain Model and Reservation Registry. Reminder emails leave through the Notification Manager and its adapter.

Stakeholder: developer adding booking rules. Detail level: balanced (as given): the modules involved in booking, grouped in their layer packages, with their dependencies. Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation).

## How the concern is answered
- **Components and responsibilities:** each package box is a module; the layer packages are Presentation, Application, Domain and registries, Persistence. Responsibilities are in `inventory.json`.
- **Interaction and dependencies:** the dashed arrows are dependencies, drawn from dependent to dependency and read top to bottom.
- **Handle booking requests:** Swing Desktop Client, REST API, Library Facade, Reservation Manager.
- **Check seat availability:** Reservation Domain Model (seat availability), Reservation Registry, Study Room Registry; Study Room Manager keeps its own occupancy computation for browsing.
- **Apply booking rules:** Reservation Manager (room, area, slot, one booking per slot), Seat Assignment Strategy, Reservation Domain Model, User Registry.
- **Manage and store reservations:** Reservation Manager, Reservation Registry, User Registry, Persistence Manager.
- **External services:** Notification Manager, the NotificationService interface, Email Notification Adapter, External email gateway (stub), Notification Scheduler.
- **What to change and what is affected:** blue = likely changed (Reservation Manager, Seat Assignment Strategy, Domain Model, Reservation Registry); red = may be affected (Study Room Manager, Notification Manager, User Registry). Facade and clients only if the request or error messages change.

Names and styling match the earlier component view (IS-seat-L3).

## Omitted on purpose
DTOs, the MySQL database, users, librarian use cases, login and registration, state classes, and undrawn dependencies listed in `inventory.json` under `omitted` (for example adapter to Swing start-up wiring, Notification Manager to Study Room Manager for room deletion).

## Assumptions
Modules are Java classes or packages shown as UML packages; the four layer packages follow the repository graph layers.

## Check results
- `puml-check`: 3 warnings left, all edges crossing container titles (layout of a cross-layer dependency graph).
- `check_inventory.py --level balanced`: 0 issues (7 notes: undrawn dependencies recorded as omitted, grouping packages without members).
- `check_view.py`: clean. `check_consistency.py`: consistent.
