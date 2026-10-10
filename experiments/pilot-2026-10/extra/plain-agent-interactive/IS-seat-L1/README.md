# Seat-booking architecture views (IS-seat-L1)

Derived from `JavaProject/src/main/java/it/unina/reservations` (Spring Boot REST + Swing client, layered boundary / controller / entity, JPA persistence).

- **view-1.puml – Component view.** Who is involved in booking: Web and Swing UIs, `ReservationController`/`StudyRoomController`, `LibraryFacade`, `ReservationManager`, `StudyRoomManager`, `NotificationManager`, registries, `PersistenceManager`, plus the scheduler and email adapter. Use it to find where a change belongs and what it will touch.
- **view-2.puml – Sequence of `makeReservation`.** The exact order of validation, the `synchronized` availability check, seat selection (specific seat vs. `AssignmentStrategy` when `seatId == 0`), persistence and notification. Use it to modify booking rules safely (note the concurrency block in `ReservationManager`).
- **view-3.puml – Domain/class view.** Entities (`Reservation`, `Seat`, `Area`, `StudyRoom`, `TimeSlot`, `Student`), the State pattern for reservation status, Observer (`Subject`/`Observer`) and Strategy (`AssignmentStrategy`). Shows where seat availability is computed (`Seat.isAvailable` via `ReservationRegistry`).
- **view-4.puml – Reservation state machine.** Transitions and time rules (6 h cancellation window, 10 min check-in tolerance, scheduler-driven expiry/completion) that determine whether a seat is considered occupied.

Notes: Swing screens (`ReservationSummary`) call `LibraryFacade` in-process, bypassing REST. Singletons are used for facade, managers and registries.
