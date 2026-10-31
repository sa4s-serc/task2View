# UML component diagram: seat booking

**Takeaway:** a booking request enters through the web or Swing client, passes `ReservationController` (REST only) and `LibraryFacade`, and is validated and executed in `ReservationManager`; availability comes from the domain model and `ReservationRegistry`, and a confirmation goes out through `NotificationManager` to the email adapter.

Stakeholder: software developer about to add booking rules. Detail level: **balanced** (given). 12 components. A *detailed* level would add the individual validation steps and the reservation state classes.

## How the view answers the concern
- **Handling booking requests:** Web and Swing clients, ReservationController, LibraryFacade, ReservationManager.
- **Checking seat availability:** ReservationManager calls the domain model (`Area.getAvailableSeats`, `Seat.isAvailable`), which queries ReservationRegistry for occupying reservations.
- **Applying booking rules:** ReservationManager (room/slot/seat/uniqueness checks in `makeReservation`), the domain model (student uniqueness, state) and AssignmentStrategy (seat auto-pick).
- **Managing and storing reservations:** ReservationManager, ReservationRegistry, PersistenceManager (JPA to MySQL).
- **External services:** NotificationManager (observer), Email notification adapter (stub gateway), and NotificationScheduler (periodic expiry and reminders).
- **What to change / what is affected:** the blue ReservationManager is the main change point (note in the view). Likely affected: the domain model (if rules need new queries), AssignmentStrategy, NotificationManager (new messages), the clients and controller (new request fields or error texts).

Evidence: see `inventory.json`. `check_inventory.py --level balanced`: 0 issues.
puml-check (final): 1 `aspect` warning (page is tall, ratio 0.93) and 1 edge crossing; the earlier wide layout had 6 warnings, so this one was kept.

## Omitted on purpose
StudyRoomManager, UserManager, other controllers (browsing, admin, login are not in the booking path); DTOs, state classes, factories, JPA utilities, exception handler. The Student actor and the MySQL database are not drawn separately, to stay within 12 components (the database is named in PersistenceManager).

## Assumptions
- Web client to REST call is taken from `reservation.html`; Swing calls the facade directly.
- Email gateway is a stub that always returns 200 (`ExternalEmailGateway`); no real service is called.
- Cancel and check-in also pass through ReservationManager, but only the booking flow is drawn.
