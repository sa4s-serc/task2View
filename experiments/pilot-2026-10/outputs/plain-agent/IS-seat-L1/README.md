# Seat booking: architecture views

Source: `JavaProject/src/main/java/it/unina/reservations` (Spring Boot + Swing, JPA, layered boundary/controller/entity).

- **view-1.puml, component view.** Shows the layers and components that take part in booking: the web UI and Swing wizard, the REST controllers, `LibraryFacade`, `ReservationManager` and `StudyRoomManager`, the entities and registries, persistence, and the notification path. It also shows the scheduler that expires reservations. Use it first to see where a change belongs and what it touches.
- **view-2.puml, class view.** Shows the classes you will edit: `ReservationManager`, the `AssignmentStrategy` seam for seat choice, `Reservation` with its State classes and Observer link, and `Seat`, `Area`, `StudyRoom` and `TimeSlot`. It also shows the registries and the notification adapter. It shows where each rule lives. Availability is in `Seat.isAvailable` and `Area.getAvailableSeats`. The cancel window and check-in tolerance are in `Reservation`. Status transitions are in the `*State` classes.
- **view-3.puml, sequence view.** Shows the `makeReservation` call chain from UI to database and notification. It covers validation order, the `synchronized` block that guards against double booking, the seat auto-assignment when `seatId == 0`, saving, and the observer notification.

Notes for changes: the Swing UI and `app.js` both go through `LibraryFacade`/REST, so add new operations to `LibraryFacade` and the controller. Seat availability is computed from reservations in `ReservationRegistry.occupiesSlot`, so there is no separate seat-status table.
