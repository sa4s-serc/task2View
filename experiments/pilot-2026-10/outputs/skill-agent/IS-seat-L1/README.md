# Task2View — IS-seat-L1

**Run id:** IS-seat-L1 · **Condition:** single agent + task2view skill · **Model:** Claude Sonnet 5.5 (`claude-sonnet-5-5`) · **Notation:** PlantUML

## Goal
> I am a software developer. I need to modify the seat booking functionality and understand the main system components involved and how they interact.

- **Role:** software developer → `developer`
- **Target:** seat booking functionality
- **Detail level:** overview (1 primary need, no enumerated subjects)
- **Primary need:** `collaboration` ("understand the main system components involved and how they interact")
- **Secondary need:** `decomposition` ("main system components"), not shown by a separate view

## Views
| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-client-server | Client-Server (4.3.1), specialised from cnc-generic, layered overlay | simplify | pass_with_limitations | 5 (4 layers + 1 datastore) | plantuml (`plantuml -checkonly` OK) |

## Rationale
- Only `cnc-generic` frames `collaboration`. The repository shows `rest-api`, so it becomes Client-Server. The repository is layered (boundary / controller / entity / database), so the layered overlay applies.
- The evidence model has 8 package components plus the database, above the overview cap of 6. The view is therefore folded to one element per layer, with relations labelled "<n> dependencies".

## What the view says
Presentation → Application → Domain → Persistence → `reservationsdb` (MySQL).
- **Two entry paths, one facade.** Browser pages call REST controllers (`ReservationController` POST `/api/reservations/create`, `StudyRoomController` GET `/api/rooms/{roomId}/detail`). The Swing wizard (`AreaSelection`, `SeatSelection`, `ReservationSummary`) calls `LibraryFacade` in the same JVM. Both reach `LibraryFacade` → `ReservationManager`.
- **`ReservationManager.makeReservation`** resolves student, room, area and time slot, then runs seat validation, the uniqueness check, the available-seat lookup, seat selection and the save inside `synchronized (this)`.
- **Seat selection:** `seatId == 0` means automatic assignment through the `AssignmentStrategy` (`FirstAvailableAssignment`). Otherwise the chosen seat is re-checked with `Seat.isAvailable`.
- **Availability** is computed from stored reservations via `Seat.isAvailable` → `ReservationRegistry` → `PersistenceManager` (JPA).
- **State:** the new reservation starts in `ActiveState`.
- **Notification:** `Reservation` is a `Subject` and `NotificationManager` is its `Observer`. Notifications go through `NotificationService` → `NotificationServiceAdapter` → the e-mail gateway stub.

## Limitations and declared gaps
- Simplified view: package components are folded into layers. Members are listed in each element's responsibilities and `realized_by`.
- Counts cover calls, fields, parameters, extends and implements between the claimed classes only. DTOs, `controller.factory`, `UserManager` and `UserRegistry` were not claimed.
- Relation labels in the evidence model use the most frequent target class names, not method names.
- The two datastore edges (reads, writes) are `inferred`. The excerpt does not name the database; the link comes from the persistence unit `reservationsPU` in `persistence.xml`.
- The boundary notification classes land in Presentation through the layer alias `boundary`. `ExternalEmailGateway` is only a stub.
- Behaviour (call order, alternative paths) was not requested and is not drawn.
- Task fit is `not-run`; a different model must judge it.
- Declared gaps: none. Uncovered primary needs: none. Not shown: `decomposition` (secondary).
- `usage.json` is omitted: no token or cost report is available to this agent. `run.log` is pipeline-only.

## Evidence counts
- Claims: 64 verified (62 observed, 2 inferred), 0 rejected.
- Evidence model: 9 elements (8 package components + 1 datastore), 14 relations, 0 scenarios, 5 states, 8 entities.
- Reflexion: 12 convergent relations, 2 divergent (strategy→entity, entity.state→entity: code dependency without a claim), 0 absent.
