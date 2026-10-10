# Task2View run IS-seat-L3 — seat booking architecture

**Model:** Claude Sonnet 5.5 (single agent + task2view skill). `usage.json` is not written: no token or cost report was available to the agent.

## Goal
> I am a software developer. I need to modify the seat booking functionality to introduce new booking rules. Before making changes to the code, I need to understand the high-level architecture supporting this functionality. [...] which parts of the system need to be modified and which other components may be affected by the changes.

- **Role:** software developer (`developer`)
- **Target:** seat booking functionality
- **Detail level:** detailed (the goal lists 5 subjects: handling booking requests; checking seat availability; applying booking rules; managing and storing reservations; interacting with external services such as the notification service)
- **Primary needs:** decomposition, dependencies, change-impact, boundary
- **Secondary needs:** collaboration (not shown as its own view)
- **Quality attribute:** maintainability

## Views
| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-decomposition | Decomposition (V&B 2.1) + layered overlay | confirm | pass_with_limitations | 15 components in 4 layer groups | PlantUML |
| V2-uses | Uses (V&B 2.2) + layered overlay | confirm | pass_with_limitations | 15 components in 4 layer groups, 33 uses relations | PlantUML |
| V3-context | Context (V&B 6.3) | confirm | pass_with_limitations | system, actor, external system, datastore | PlantUML |

(V2 draws every `uses` relation between its 15 components: 33 relations. The remaining 4 relations in the evidence model involve the actor, external system and datastore and appear in V3.)

All three PlantUML sources pass `plantuml -checkonly`. Task fit is `not-run`: a different model must judge it.

## Rationale
- **V1** answers *what are the main components, what is each responsible for* for the four internal subjects. Components sit in layers (boundary → Presentation, controller → Application, entity → Domain, database → Persistence).
- **V2** answers *which components depend on which* and *what is affected when one changes* for the target "seat booking functionality". Read it from a component you plan to change: the incoming arrows are what may be affected.
- **V3** answers *what is outside the system*: the student, the external email service reached through `ExternalEmailGateway`, and the `reservationsdb` MySQL database.
- Collaboration is only secondary, so it adds no view; the participants and their calls are visible in V2 and in the recovered scenario `make reservation` (evidence model, 15 ordered steps with one `alt`).

## Where the work happens (summary for the change)
- **Handling requests:** `ReservationController` (REST) and `ReservationSummary` (Swing) → `LibraryFacade` → `ReservationManager.makeReservation`.
- **Checking availability:** `ReservationManager` → `Area.getAvailableSeats` → `Seat.isAvailable` → `ReservationRegistry.findReservationsBySeat` (statuses that occupy a slot: ACTIVE, CONFIRMED, defined in `ReservationRegistry.occupiesSlot`).
- **Applying booking rules:** mostly inside `ReservationManager` (room active and open on weekdays, slot not started or passed, seat belongs to area, no seat available) plus `Student.hasActiveOrConfirmedReservationForDateAndSlot` (one reservation per student/date/slot) and `Reservation` (6-hour cancellation window, 10-minute check-in tolerance). Seat choice is the `AssignmentStrategy` extension point (`FirstAvailableAssignment`).
- **Managing and storing:** `Reservation` (state delegated to `ReservationState`), `ReservationRegistry` / `StudyRoomRegistry` → `PersistenceManager` → `reservationsdb`.
- **Notifying:** `ReservationManager` attaches `NotificationManager` (Observer) to the reservation; `Reservation.notifyObservers` → `NotificationManager.update` → `NotificationServiceAdapter` → `ExternalEmailGateway` (stub). Delivery errors are caught in `NotificationManager`, so they do not fail a booking.

## Limitations and declared gaps
- No declared evidence gaps; no uncovered primary need.
- Cap of 15 components: read but **not modelled** — `StudyRoom` (active flag, weekday opening, time-slot schedule), `TimeSlot`, `UserRegistry`, `StudyRoomManager`/`StudyRoomController` (availability browsing used by the wizard), `JpaUtil`, `NotificationConfiguration` (wires `NotificationServiceAdapter` into `NotificationManager`), `NotificationScheduler` (reminders and end-of-reservation job), `ReservationState` classes. Several of these are directly relevant if rules touch rooms or time slots; check them before editing.
- Layer groups are not counted in the 15-element cap (assumption).
- `NotificationServiceAdapter` and `ExternalEmailGateway` live in package `boundary`, so the alias table places them in Presentation although they act as an adapter to an external service.
- `ExternalEmailGateway` is a stub (always returns 200); the real external service is not named in the code.
- Interfaces `AssignmentStrategy`, `NotificationService` and `Observer` are merged into their single implementation, so calls through them are drawn against the implementation.
- Managers, registries and the facade are singletons (`getInstance()`); `ReservationManager.makeReservation` serialises with `synchronized (this)`, which matters if new rules need concurrency guarantees.
- Source comments are placeholder text ("English implementation note"), so responsibilities come from code, not documentation.
- No documentation files were used as evidence; tests were not used as evidence.

## Evidence counts
- Claims: 96 verified (96 observed, 0 inferred), 0 rejected
- Evidence-model elements: 18 (15 components, actor, external system, datastore); relations: 37; scenarios: 1; entities: 6; reflexion: 33 convergences, 0 divergences, 4 absences (non-component endpoints)

Files: see `traceability.md` for element → files and symbols per view.
