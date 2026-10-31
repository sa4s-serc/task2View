# Seat booking: component view (revision 1)

**Takeaway:** a booking enters through `ReservationController` (REST) or the Swing UI, passes `LibraryFacade` to `ReservationManager`, which applies the booking rules together with the domain entities, stores the reservation through the registries and JPA, and notifies the student through the Observer mechanism and the `NotificationService` interface.

**Stakeholder:** software developer about to add booking rules. **Level:** detailed, because a change is imminent. Wording uses code names. The previous version is in `v1/`.

## How the view answers the concern
- **Handling requests:** Web UI (to `ReservationController` for create/cancel/check-in and `StudyRoomController` for availability), Swing UI, `RestExceptionHandler` (rule exceptions become HTTP 400, so a new rule's rejection reaches the client here), `LibraryFacade`.
- **Checking availability:** `ReservationManager` calls the domain entities (`Seat.isAvailable`, `Area.getAvailableSeats`), which query `ReservationRegistry` (`occupiesSlot`) and `StudyRoomRegistry`. `StudyRoomManager` runs the same check for the UI.
- **Applying rules:** `ReservationManager` (room, area, seat, slot and uniqueness checks; seat choice via `AssignmentStrategy`) and the entities. The manager node says it also handles cancel, check-in and end of slot (the scheduler reaches it through the facade).
- **Managing and storing reservations:** `ReservationRegistry`, `StudyRoomRegistry`, `UserRegistry` (student lookup on every booking), `PersistenceManager` (JPA, MySQL).
- **External services:** `NotificationManager` provides `Observer` (attached by `ReservationManager`, called by `Reservation`) and requires `NotificationService`, provided by the e-mail adapter and stub gateway. `NotificationScheduler` triggers reminders and end-of-slot handling.
- **Modify vs. affected:** marked in the diagram. Blue (`accent`): `ReservationManager`, domain entities, `AssignmentStrategy`, `ReservationRegistry`. Red (`alert`): `StudyRoomManager` and `NotificationManager`. Also affected but not coloured: `RestExceptionHandler` and the REST and Swing clients.

`inventory.json` holds elements, relations and evidence. `check_inventory.py`: exit 0 (20 elements, 28 relations).

## Changes after the review
- Added `UserRegistry`, `StudyRoomController`, `RestExceptionHandler`, and the dependencies domain entities -> `StudyRoomRegistry`, `StudyRoomManager` -> entities and `ReservationRegistry` (all verified in code).
- `NotificationService` and `Observer` are now UML interfaces (realization arrows). The two separate "notify" edges became one mechanism: attach observer, notify observers.
- Relations are dashed use dependencies. The `muted` stereotype is gone. A note says components are logical groupings of classes.
- `facade -> ReservationManager` is relabelled "all reservation ops". `PersistenceManager` and MySQL merged into one component.
- Four grouping packages (Clients, Request handling, Storage, Notification) were dropped. Only "Booking logic" remains, because the detailed budget is 20 elements and packages count. `NotificationScheduler` is therefore a standalone component, which also fixes its placement under "Clients".
- Not done: interfaces are drawn with realization/use arrows, not ball-and-socket, because the inventory check cannot read that notation. Colour marks change impact, with a legend; no operations are listed on `ReservationManager`, only its responsibilities in the label.

## Omitted on purpose
DTOs, state classes, factories, `UserManager`, authentication, monitoring and student controllers, `NotificationConfiguration` (wiring).

## Assumptions
"Domain entities" merges `Area`, `Seat`, `Student`, `Reservation`. The e-mail gateway is a stub returning 200. `RestExceptionHandler` is shown applying to `ReservationController` only (it is a `@RestControllerAdvice`, so it covers all controllers).

## Check result
`puml-check`: renders, 5 warnings (v1 had 7): tiny text when scaled to 1200 px, one edge through the "Booking logic" title, one edge through its own label, one detached label, one label on the container border. The diagram is dense (28 edges), and I stopped after this one revision.
