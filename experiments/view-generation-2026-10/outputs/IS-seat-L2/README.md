# Seat booking – component view (UML component diagram)

**Stakeholder / concern:** a developer about to add new booking rules. Viewpoint: component; aspect: structural. Derived from `JavaProject/src/main/java/it/unina/reservations`.

## What it shows
Layers (Boundary, Control, Entity, Persistence) and the components on the seat-booking path, with dependency arrows labelled by the interaction.

## How it addresses the concern
- **Main components and responsibilities.** Component names and stereotypes state the role. The key one is `ReservationManager`, highlighted. It orchestrates `makeReservation` (validation, seat choice, save, notify), cancel, check-in, and expiry or completion. `StudyRoomManager` computes room, slot and seat availability. `AssignmentStrategy` auto-assigns a seat. `NotificationManager` is the Observer for booking events. The registries hide persistence. `Reservation` and its State classes hold the lifecycle.
- **Interactions.** Swing UI, REST controllers and the scheduler all enter through `LibraryFacade`. The facade delegates to the managers. `ReservationManager` uses the registries, the strategy and the notifications. `Reservation` notifies `NotificationManager`. The registries go through `PersistenceManager` to the database. Notifications go through the adapter to email.
- **Likely impact of new rules.**
  - *Primary:* `ReservationManager.makeReservation` and its validators.
  - *Rules scattered in entities:* `Student.hasActiveOrConfirmedReservationForDateAndSlot`, `Seat.isAvailable`, `Reservation` (check-in tolerance, state transitions).
  - *Query support:* `ReservationRegistry`, which would need new queries if a rule needs new data such as per-day limits.
  - *Consistency:* `StudyRoomManager` availability views (room, slot and seat listings shown to the user) should reflect the new rules, or the UI will offer options that are then rejected.
  - *Seat selection:* `AssignmentStrategy`, if the rules change auto-assignment.
  - *Interface contract:* `LibraryFacade`, REST controllers, `ReservationRequestDTO` and the Swing screens, only if inputs or error messages change.
  - *Notifications:* new rules that produce new messages.
  - Tests in `src/test/.../MakeReservationTest` cover the booking path.

Notes: the static HTML pages in `resources/static` contain no `/api/` calls, so they are omitted. The booking path is the Swing UI plus the REST API.
