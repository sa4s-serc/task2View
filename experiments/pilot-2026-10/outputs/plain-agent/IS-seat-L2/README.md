# Seat booking - architecture views (IS-seat-L2)

Source: JavaProject (Java, Spring Boot REST + Swing UI, JPA). Layers: boundary / controller / entity / database.

- **view-1.puml** - Component view. Shows the components involved in seat booking, their responsibilities and dependencies (UI -> LibraryFacade -> ReservationManager -> entities/registries -> PersistenceManager; Observer to NotificationManager; AssignmentStrategy). Why: answers "what are the main parts and how do they connect".
- **view-2.puml** - Sequence of `makeReservation` (UC7). Shows the order of checks and exactly where each existing booking rule is implemented (room open/active, slot not past, one reservation per student/date/slot, seat availability, explicit vs auto seat, save, notify). Why: this is where new rules will be inserted.
- **view-3.puml** - Reservation state machine (State pattern). Shows statuses and the time-based rules (6h cancel window, 10 min check-in tolerance, expiry/completion by the scheduler). Why: new rules often interact with lifecycle and with which states "occupy" a seat.
- **view-4.puml** - Impact map. Classifies elements as primary (red), to-verify (yellow), secondary (green) for a rule change. Why: addresses "which parts may be affected"; this is my analysis derived from the dependencies in the code, not code structure itself.

Notes: Swing and REST both enter via `LibraryFacade` (Swing directly, REST through `ReservationController`). Rule constants are hard-coded (6h in `Reservation.validateCancellationWindow`, 10 min in `Reservation.CHECK_IN_TOLERANCE_MINUTES`). `ReservationManager.makeReservation` is `synchronized` to guard concurrent booking. Not rendered with PlantUML here; sources only.
