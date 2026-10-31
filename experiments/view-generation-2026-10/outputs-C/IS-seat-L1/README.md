# UML component diagram: seat booking (view.puml / view.png)

**Takeaway:** a booking request from the web or Swing UI enters through `LibraryFacade`, is executed by `ReservationManager` (which uses the domain, the registries, a seat-assignment strategy and `NotificationManager`), and is persisted via `PersistenceManager` to MySQL.

Stakeholder: software developer about to modify seat booking. Detail: *detailed* for the booking path (ReservationManager highlighted), overview elsewhere (15 nodes, within the ≤20 budget). Wording: technology names kept.

## Concern → where answered
- **Main components involved:** all boxes; yellow `ReservationManager` is the place the booking rules live (`makeReservation`, `cancelReservation`, `performCheckIn`).
- **How they interact:** labelled edges, caller → callee. Entry: Web Client → REST Controllers → LibraryFacade, or Swing → LibraryFacade; down through managers to registries, persistence and DB; side paths to the seat-assignment strategy and notifications (Observer + `NotificationService`).
- Control flow order inside one booking is *not* shown (needs a sequence view): resolve student/room/area/slot → validate seat → (synchronized) uniqueness, availability, seat choice → save → notify.

## Inventory (element → evidence)
- Web Client: `static/reservation.html:385` POST `/reservations/create`; `static/app.js:2` `API='/api'`.
- Swing Booking Wizard: `boundary/Swing/ReservationSummary.java:100`, `DateAndRoomSelection.java:214`, `TimeSlotSelection.java:87`, `AreaSelection.java:85`.
- REST Controllers: `boundary/SpringBoot/ReservationController.java:15-49` (create/cancel/checkIn → facade).
- Notification Scheduler: `boundary/NotificationScheduler.java:15-29` (60 s; `@EnableScheduling` in `ReservationsApplication.java:13`).
- LibraryFacade: `controller/LibraryFacade.java:117-164` (delegates to managers).
- ReservationManager: `controller/ReservationManager.java:65-102` (make), `:205` cancel, `:240` check-in; notify `:120-123`, `:220`.
- StudyRoomManager: `controller/StudyRoomManager.java:196,225,263` (rooms, slots, detail).
- AssignmentStrategy: `controller/strategy/AssignmentStrategy.java:10`, `FirstAvailableAssignment.java:15`; used `ReservationManager.java:39,400`.
- Reservation Domain: `entity/Reservation.java:82-88` (setState notifies), `:101-126` state transitions; `entity/state/*`; `entity/Seat.java:44` availability.
- Registries: `entity/ReservationRegistry.java:33-56`; `StudyRoomRegistry`, `UserRegistry` (`ReservationManager.java:28-30`); Seat→registry `Seat.java:45`.
- NotificationManager: `controller/NotificationManager.java:15,40,51,73`; interface `NotificationService.java:11`.
- Email Adapter: `boundary/NotificationServiceAdapter.java:12-20`, `ExternalEmailGateway.java:12` (stub, returns 200); wired in `NotificationConfiguration.java:17`.
- PersistenceManager: `database/PersistenceManager.java:19,74,185`; MySQL: `META-INF/persistence.xml:21`.

## Omitted on purpose
DTOs, Area/TimeSlot/Student entities as separate boxes, JpaUtil, user registration/login, room creation, librarian monitoring, `StudentController`/`StudyRoomController` as separate boxes (merged into REST Controllers). Librarian actor is omitted: the librarian does not book seats.

## Assumptions
- "Registries" merges three registry classes; "Reservation Domain" merges Reservation, its state classes and Seat.
- The Observer edge is drawn Domain → NotificationManager since `ReservationManager` attaches it (`:121`, `:248`).
- Cancel/check-in/end flows are included as they share the booking components.

## Check result
puml-check: 0 crossings, 0 text overlaps; 1 `aspect` warning (ratio 1.26, tall) kept because left-to-right gave 6.0 and unpackaged TB with ranksep 70 gave 0.61; packaged layers gave 7 warnings. Image review added the missing ReservationManager→NotificationManager edge and a missing label.
