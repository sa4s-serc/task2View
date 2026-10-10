# Task2View run IS-seat-L2

**Goal (verbatim):** I am a software developer. I need to modify the seat booking functionality to introduce new booking rules. Before changing the code, I need to understand the main components involved in this functionality, their responsibilities, and how they interact with each other. I also want to identify which parts of the system may be affected by the modification.

- **Role:** software developer (`developer`) · **Target:** seat booking functionality · **Detail level:** feature
- **Primary needs:** collaboration, change-impact · **Secondary needs:** decomposition (not shown as a view of its own; responsibilities are inside the elements)
- **Produced by:** Claude Sonnet 5.5 (claude-sonnet-5-5) working as one agent with the task2view skill, no pipeline run. Token and cost usage is not reported by the tool, so `usage.json` is not written.

## Views

| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-client-server | Client-Server (V&B 4.3.1) with layered overlay | simplify | pass_with_limitations | 5 | PlantUML (`view.puml`) |
| V2-uses | Uses (V&B 2.2) with layered overlay | simplify | pass_with_limitations | 4 | PlantUML (`view.puml`) |

Task fit is `not-run`: a different model must judge it.

## Rationale

- **V1-client-server** answers "which components take part in seat booking and how they work together". The repository exposes REST endpoints (`ReservationController`), so the C&C view is specialised to client-server; the repository is layered, so layers are overlaid.
- **V2-uses** answers "what is affected when a part changes". No single viewpoint covers both primary needs, hence two views.
- Both views were **simplified**: the evidence model has 24 components (cap is 10), so each view has one box per layer listing its components, and relations between layers carry a dependency count. The class-level picture is in `evidence_model.json` and in the table below.

## What the evidence says about the seat booking flow

Entry points are the REST route `POST /api/reservations/create` (`ReservationController.java:21`) and the Swing wizard (`SeatSelection` -> `ReservationSummary.confirm`, `ReservationSummary.java:98`). Both call `LibraryFacade.makeReservation` (`LibraryFacade.java:117`), which delegates to `ReservationManager.makeReservation` (`ReservationManager.java:65`).

Booking rules currently live in these places:

| Rule | Where |
|---|---|
| room active, open on weekdays | `ReservationManager.resolveRoom` (189-194), `StudyRoom.isOpenOnDate` (141-146) |
| slot not in the past or already started | `ReservationManager.resolveTimeSlot` (362-374) |
| seat belongs to the chosen area (0 = automatic) | `ReservationManager.validateSeatInArea` (104-117) |
| one active or confirmed reservation per student, date and slot | `ReservationManager.validateUniqueness` (151-155) -> `Student.hasActiveOrConfirmedReservationForDateAndSlot` (42-50) |
| seats left in the area | `ReservationManager.availableSeats` (142-149) -> `Area.getAvailableSeats` (49-58) |
| chosen seat still free / automatic choice | `ReservationManager.selectSeat` (385-400) -> `Seat.isAvailable` (44-52), `AssignmentStrategy` / `FirstAvailableAssignment` |
| what counts as occupying a slot | `ReservationRegistry.occupiesSlot` (119-123): ACTIVE or CONFIRMED |
| cancellation (6 h before start) and check-in (same day, 10 min tolerance) | `Reservation` (160-164, 144-152, `CHECK_IN_TOLERANCE_MINUTES` at 19) |

## Parts that may be affected by a change to the booking rules

Direct dependents come from the evidence-model relations (`uses`); "transitive" counts every component that reaches the target through `uses`. The entities, registries and `NotificationManager` depend on each other in cycles (for example `Reservation` <-> `Student`, `Seat` <-> `Area`), so most of them reach the same 16 components; `ReservationManager` (5) and `FirstAvailableAssignment` (6) are the only narrow ones.

| Component | Used directly by | Transitive dependents |
|---|---|---|
| ReservationManager | LibraryFacade | 5 |
| Student | NotificationManager, Reservation, ReservationManager | 16 |
| Seat | Area, Reservation, ReservationManager, StudyRoomManager | 16 |
| Area | ReservationManager, Seat, StudyRoom | 16 |
| StudyRoom | Area, ReservationManager | 16 |
| Reservation | ActiveState, NotificationManager, ReservationManager, ReservationRegistry, Student | 16 |
| TimeSlot | Reservation, ReservationManager, StudyRoom | 16 |
| ReservationRegistry | NotificationManager, ReservationManager, Seat, Student | 16 |
| StudyRoomRegistry | Area, ReservationManager, StudyRoom, StudyRoomManager | 16 |
| FirstAvailableAssignment | ReservationManager | 6 |
| NotificationManager | LibraryFacade, NotificationConfiguration, Reservation, ReservationManager | 16 |

Points worth checking before changing code (all from the cited code):

- The checks and the creation run inside `synchronized (this)` (`ReservationManager.java:84-100`); a rule that depends on other reservations (counts, limits per student) belongs inside this block, or it can race.
- Seat availability is computed in three places that all go through `Seat.isAvailable`: `ReservationManager.selectSeat`, `Area.getAvailableSeats`, and `StudyRoomManager.getRoomDetail` (289) for the seat-selection screen; `StudyRoomManager.getAvailableTimeSlots` also counts seats (253). A rule that changes availability needs to be reflected in all of them, or the screens will offer seats the booking then rejects.
- Rule violations are reported as `IllegalArgumentException` / `IllegalStateException`; `RestExceptionHandler` turns both into HTTP 400 with the message (`RestExceptionHandler.java:19-22`) and the Swing screen shows `ex.getMessage()` (`ReservationSummary.java:106-107`). New rules should follow the same exceptions.
- Automatic seat choice is behind `AssignmentStrategy` (set to `FirstAvailableAssignment` in `ReservationManager.getInstance`, line 39), the one existing variation point for seat assignment.
- Reservation states: a new booking is saved in `ActiveState`, and `NotificationManager` sends a message for each state change (`Reservation.setState` notifies observers). A new rule that adds a state or changes transitions also touches `StatusEnum`, the state classes, `Reservation.initializeState` and `NotificationManager.messageForState`.
- Dependencies against the layer order: Reservation (domain) -> NotificationManager (application); NotificationManager (application) -> NotificationServiceAdapter (presentation).
- Tests that reference `ReservationManager` or `LibraryFacade`: `MakeReservationTest` (booking), `CancelReservationTest`, `PerformCheckInTest`, `ManageReservationEndTest`, `AvailableStudyRoomsQueryTest`, plus the room, registration and authentication tests.
- The browser client `static/reservation.html` posts to `/reservations/create` and `ReservationRequestDTO` / `ReservationDTO` carry the data across layers; adding an input to a rule changes the DTO, the controller parameters, the Swing wizard state and the web page.

## Limitations and declared gaps

- No declared evidence gaps; no uncovered primary needs. Secondary need `decomposition` has no view of its own.
- Both views are simplified (see above); their question is `partial`, not `supported`.
- Dependencies were read by hand; there is no static-analyser cross-check, so reflexion `divergence` was not computed.
- Not examined as components: `CancelledState`, `ConfirmedState`, `CompletedState`, `ExpiredState` (transitions are in the evidence model), `UserManager`, factories, the DTO classes, the Swing screens other than `SeatSelection` and `ReservationSummary`, and the JavaScript client.
- No scenario (call order) was recovered: the goal asks for structure, so no behavioural view was planned.
- Layer assignment follows package names (see the limitation on `NotificationServiceAdapter`).

## Evidence counts

- Claims: 112 verified, 0 rejected (51 element, 57 relation, 4 transition); support: all observed.
- Evidence model: 24 components, 1 datastore, 51 relations, 8 entities, 0 scenarios.
- Views: 2, each with 0 overflow (folded).

Files: see `traceability.md` for element -> files and symbols, `reconciliation.json` and `validation_report.json` for decisions.
