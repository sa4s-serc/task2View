# Seat booking: components and dependencies (UML component diagram), revision 1

**Takeaway:** a booking request enters through the Swing client or REST API, passes the Library Facade, and is handled by the **Reservation Manager**. It applies the booking rules, uses the Reservation Domain Model for seat availability and the Seat Assignment Strategy to choose a seat, and stores the result through the registries in the MySQL database. Notifications reach the email gateway through the `NotificationService` interface.

Stakeholder: software developer changing the booking rules. Detail level: **balanced** (as given); a detailed level would add the private validation steps of `makeReservation` and the individual state classes. Previous version: `v1/`. Evidence: `inventory.json`.

## How the view answers the concern
- **Components and responsibilities**: the key responsibilities are now written inside the Reservation Manager, Reservation Domain Model, Seat Assignment Strategy and Study Room Manager boxes. The rest are in `inventory.json`.
- **Interactions and dependencies**: all usage is drawn as dashed dependencies, from caller to callee, top to bottom.
- **Handle booking requests**: Swing Desktop Client, REST API, Library Facade, Reservation Manager.
- **Check seat availability**: Reservation Domain Model (`Seat.isAvailable`, `Area.getAvailableSeats`), which depends on both the Reservation Registry and the Study Room Registry. Study Room Manager has a second, separate occupancy computation (`createSeatStatusMap`) that reads the Reservation Registry directly.
- **Apply booking rules**: Reservation Manager (room, area, slot, seat choice), Reservation Domain Model (student uniqueness check, states, check-in tolerance), Seat Assignment Strategy (automatic seat), User Registry (student lookup).
- **Manage and store reservations**: Reservation Manager, Reservation Registry, User Registry, MySQL database.
- **External services**: Notification Manager requires the `NotificationService` interface; the Email Notification Adapter provides it and calls the external email gateway stub. The reservation to Notification Manager link is labelled as observer registration and notification. The Notification Scheduler triggers expiry and reminders.
- **Change impact**: blue = likely changed (Reservation Manager, Seat Assignment Strategy, Domain Model, Reservation Registry). Red = may be affected (Study Room Manager occupancy display, Notification Manager messages for new states, User Registry for per-student rules). The Facade and clients are affected only if the request or its error messages change (stated in the legend).

## Changes from v1 (reviewer critique)
- Added dependencies: Study Room Manager to Reservation Registry, Domain Model to Study Room Registry, Reservation Manager to User Registry.
- Modelled `NotificationService` as an interface (provided by the adapter, required by Notification Manager). Removed the direct manager-to-adapter arrow and moved the adapter out of Presentation into "Notification integration".
- Relabelled Reservation Manager to Notification Manager as "registers observer, notifies".
- Solid arrows replaced by dashed dependencies. Responsibilities added to the boxes. A second marking (red) added for affected components.
- Merged the Persistence Manager into the database element, as the reviewer suggested.

## Kept as before, and why
- The «accent»/«alert»/«muted» styling stays: the legend explains it, and these are the template's styling stereotypes, not UML stereotypes. The external email gateway keeps the name "(stub)" and grey styling. Putting it in its own boundary was not done because the diagram is already dense.
- The Notification Manager is still drawn to the Domain Model ("observes reservations"). The code confirms it: `NotificationManager implements entity.Observer` and `Reservation extends Subject`.

## Omitted on purpose
User Manager and factories, DTOs, librarian functions, individual state classes, private validation steps. Undrawn dependencies are listed in `inventory.json` under `omitted` (for example `NotificationConfiguration` wiring, which is start-up only).

## Assumptions
The Domain Model groups the entities (Seat, Area, StudyRoom, TimeSlot, Student, Reservation, states, observer). The managers and registries are singletons, which is not shown.

## Check results
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (only notes on undrawn dependencies, all listed as omitted).
- `check_view.py`: clean.
- `puml-check`: remains with warnings. The diagram is taller than 16:9 (ratio 1.15), smallest text is 8.9 px at 1200 px width, and a few long edges from the application layer to the registries cross container titles. Fewer edges would lose reviewer-requested dependencies, so I kept them.
