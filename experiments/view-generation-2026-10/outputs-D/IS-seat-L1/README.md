# Seat booking: component view (UML component diagram), revision 2

**Takeaway:** a booking request goes client → REST controllers (or Swing directly) → `LibraryFacade` → `ReservationManager`, which validates, picks a seat through the `AssignmentStrategy` interface, saves via the registries and triggers notification through the Observer path from the `Reservation` entity.

**Stakeholder:** software developer about to modify seat booking. **Detail level:** detailed for the booking path only (18 nodes incl. 3 interfaces and 1 actor, 20 relations in `inventory.json`); engineering wording.

## Concern coverage
- *Main components involved*: web client, Swing client, REST controllers, `RestExceptionHandler`, `LibraryFacade`, `ReservationManager` (blue, holds the booking rules), `StudyRoomManager` (wizard steps), `FirstAvailableAssignment`, domain entities, registries, `NotificationManager`, `NotificationServiceAdapter`, `NotificationConfiguration`, MySQL.
- *How they interact*: dashed dependencies; numbers 1-5 on `ReservationManager` edges give the order (1 resolve, 2 check availability, 3 pick seat, 4 save, 5 attach observer). The note on `ReservationManager` lists the steps and the synchronized block; `seatId` 0 = automatic seat. Interfaces `AssignmentStrategy`, `Observer` and `NotificationService` show the extension points. The error path is `REST controllers` → `RestExceptionHandler` (HTTP 400).

## Changes after critique 1 (previous version in `v1/`)
- Added `RestExceptionHandler`, `NotificationConfiguration`, the three interfaces, the endpoint `POST /api/reservations/create`.
- Split the strategy into interface + `FirstAvailableAssignment`; notification now runs `Reservation` → `Observer` ← `NotificationManager` instead of a direct `ReservationManager` call.
- Note moved to `ReservationManager`; edges numbered; solid arrows replaced by dashed dependencies; Librarian actor removed.
- **Not adopted:** a drawn system boundary. The database is a muted external component outside the logic, and a container would add nesting and edge-through-title risk without new information. The database also stays a plain component, since «database» is not a UML standard stereotype.

## Omitted on purpose
Librarian/room creation, `NotificationScheduler`, `UserManager`, factories, DTOs, state classes, cancel and check-in flows. Only the booking endpoint is named; `StudyRoomController` endpoints are covered by the "list rooms, slots, seats" edge.

## Assumptions
Registries and `PersistenceManager` are merged; the stub `ExternalEmailGateway` is folded into the adapter. `RestExceptionHandler` also maps `SecurityException` to 401 (not drawn).

## Check result
`check_inventory.py`: 0 issues, 0 unbacked items. `puml-check`: one `aspect` warning (ratio 1.0, taller than 16:9) and one `text-on-node` warning (the `AssignmentStrategy` label touches the left edge of the picture area); edge-through-text and bundled-edge warnings from the first draft were fixed by drawing the realization links sideways. Not independently re-reviewed.
