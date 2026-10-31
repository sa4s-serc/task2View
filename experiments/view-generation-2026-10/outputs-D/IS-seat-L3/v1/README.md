# Seat booking: component view

**Takeaway:** a booking request enters through `ReservationController` (REST) or the Swing UI, goes through `LibraryFacade` to `ReservationManager`, which applies the booking rules (with the domain entities), saves the reservation through the registries and JPA, and notifies the student through `NotificationManager` and the e-mail adapter.

**Stakeholder:** software developer about to add booking rules. **Detail level:** detailed for the booking path, because a change is imminent. Wording uses code names and technologies.

## How the view answers the concern
- **Handling booking requests:** Clients, `ReservationController`, `LibraryFacade` (Web UI over HTTP/JSON; Swing calls the facade directly).
- **Checking seat availability:** `ReservationManager` (room, slot and seat checks), `Domain entities` (`Seat.isAvailable`, `Area.getAvailableSeats`, per-student uniqueness) and `StudyRoomManager` (availability queries for the UI).
- **Applying booking rules:** `ReservationManager` holds the validations (room active and open, slot not past, seat in area, one booking per slot) and seat assignment via `AssignmentStrategy`. Part of the rules sit in the entities.
- **Managing and storing reservations:** `ReservationRegistry`, `StudyRoomRegistry`, `PersistenceManager` (JPA), MySQL.
- **External services:** `NotificationManager` calls the `NotificationService` interface, implemented by the adapter and a stub e-mail gateway. `NotificationScheduler` triggers reminders and end-of-slot handling.
- **What to change / what is affected:** new rules go mainly in `ReservationManager` and the entities. Affected: `LibraryFacade` and the controllers if the request or its errors change, the registries if new data is stored, and `NotificationManager` if new messages are needed. Cancel and check-in rules share the same manager.

Evidence and responsibilities: `inventory.json`. `check_inventory.py` result: exit 0 (clean, 20 elements incl. 5 packages, 19 relations).

## Omitted on purpose
DTOs, reservation state classes, user factories, `UserManager`, authentication and other REST controllers, `NotificationConfiguration` (wiring only).

## Assumptions
- "Domain entities" merges Area, Seat, Student and Reservation, which contain availability and state logic.
- The e-mail gateway is a stub (returns 200), so the external service is simulated in this code.

## Check result
`puml-check`: renders, 0 errors. Last run still warns: aspect (too tall, left-to-right was too wide), three edge-through-text on package titles, two label-on-border, one bundled-edges. Direction and `--->` tweaks did not reduce the count further, so this version was kept.
