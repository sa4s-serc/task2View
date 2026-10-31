# Seat booking – component view (UML component diagram)

Source: `view.puml`. Derived from `JavaProject/src/main/java/it/unina/reservations`.

**What it shows.** The components on the seat-booking path, grouped in layers (boundary, control, entity, persistence), the external email service, and the calls between them. Student and librarian use either the web UI (REST) or the Swing wizard (direct facade calls).

**How it addresses the concern**
- *Handling booking requests:* `ReservationController` (`POST /api/reservations/create`) and the Swing `ReservationSummary` both go through `LibraryFacade` to `ReservationManager.makeReservation`.
- *Checking seat availability:* `StudyRoomController` and `StudyRoomManager` serve availability to the UI. During booking, `ReservationManager` calls `Area.getAvailableSeats` and `Seat.isAvailable`, which query `ReservationRegistry`.
- *Applying booking rules:* these live in `ReservationManager` (room active and open, slot not past, seat in area, one reservation per student and slot, seat selection under a `synchronized` block). `AssignmentStrategy` handles automatic seat choice. `Reservation` and its states hold the cancellation window and check-in rules. This is where new rules go.
- *Managing and storing reservations:* `ReservationManager`, `Reservation`, `ReservationRegistry`, `PersistenceManager` (JPA), MySQL.
- *External services:* `Reservation` notifies `NotificationManager` (Observer), which uses the `NotificationService` interface. `NotificationServiceAdapter` and `ExternalEmailGateway` (a stub) reach the email service. `NotificationConfiguration` wires the adapter at startup.
- *Impact of changes:* a new rule mainly touches `ReservationManager` and possibly `Reservation` / `Student` / `Seat`. It may affect `ReservationRegistry` queries, the `ReservationRequestDTO` / `ReservationController` parameters, `RestExceptionHandler` and the UIs (error display), `NotificationManager` messages, and `NotificationScheduler`-driven expiry and reminders.
