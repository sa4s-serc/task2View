# Seat booking – component view (UML component diagram)

**Viewpoint/model kind:** component / UML component diagram. **Stakeholder:** developer about to modify seat booking. **Concern:** control flow.

## What it shows
The components on the path of a seat booking and the calls between them, derived from `JavaProject/src/main/java/it/unina/reservations`:

- **Presentation:** Swing wizard (students/librarians; `ReservationSummary` calls `makeReservation`), static web UI (`app.js` → `/api`), REST controllers (`/api/reservations/create`, `/api/rooms/...`), and `NotificationScheduler`.
- **Control:** `LibraryFacade` (single entry point), `ReservationManager`, `StudyRoomManager`, `NotificationManager`, and the `AssignmentStrategy` interface (`FirstAvailableAssignment`).
- **Domain:** `Reservation` with its state classes, room/area/seat/time-slot/student entities, and the three registries.
- **Persistence/external:** `PersistenceManager` (JPA) → MySQL; `NotificationServiceAdapter` → email gateway.

## How it addresses the concern
- **Main components involved in seat booking:** the packages and components above; the booking logic lives in `ReservationManager.makeReservation`, which validates room/area/slot/seat, enforces one active reservation per student and slot (`Student.hasActiveOrConfirmedReservation...`), picks the seat (explicit id, or `AssignmentStrategy` when seatId = 0), saves an ACTIVE `Reservation`, and notifies.
- **How they interact:** edges are labelled with the calls. Both UIs (Swing directly, web via REST) go through `LibraryFacade`; the facade delegates to managers; managers use entities and registries, which persist via `PersistenceManager`. Seat availability is computed in the domain (`Area.getAvailableSeats` → `Seat.isAvailable` → `ReservationRegistry`). State changes are pushed to `NotificationManager` via the Observer link, which delivers through the `NotificationService` interface. The scheduler drives expiry/completion and reminders.

Notes: the booking section is `synchronized` on `ReservationManager`; the notification is attached and fired after the reservation is saved. Not rendered/validated with PlantUML here.
