# Seat booking: component view (UML component diagram)

**Takeaway:** a booking request travels client → REST controllers (or Swing directly) → `LibraryFacade` → `ReservationManager`, which validates, picks a seat, saves through the registries and notifies via `NotificationManager`.

**Stakeholder:** software developer about to modify seat booking. **Detail level:** detailed for the booking path only (14 nodes incl. 2 actors, 15 relations); engineering wording (Spring MVC, JPA, HTTP).

## Concern coverage
- *Main components involved*: all boxes; `ReservationManager` (blue) is where the booking rules live (`makeReservation`).
- *How they interact*: edges, read top to bottom. The note gives the internal order: validate student/room/area/slot, then a synchronized block (uniqueness, seat selection, save, notify). `seatId` 0 means automatic seat assignment via `AssignmentStrategy`. `StudyRoomManager` serves the earlier wizard steps (rooms, slots, seat availability). Librarians feed the flow by creating rooms.

Evidence for every element and relation: `inventory.json` (`check_inventory.py`: 0 issues, 0 unbacked items).

## Omitted on purpose
`NotificationScheduler` (reminders/expiry), `UserManager`, factories, DTOs, state classes, cancel and check-in flows.

## Assumptions
- Registries and `PersistenceManager` are merged into one "Registries" component; the stub `ExternalEmailGateway` is folded into the email adapter.
- The "attach, notify" edge represents the Observer callback that goes through `Reservation` entities.

## Check result
`puml-check`: 0 overlaps or edge-through-text; one remaining `aspect` warning (ratio 1.07, view is taller than 16:9; left-to-right was tried and gave 4:1, which is worse). Not independently reviewed.
