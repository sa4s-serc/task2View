# Seat booking architecture (IS-seat-L3)

Layers: Boundary (Swing UI, REST controllers, scheduler, e-mail adapter) -> Controller (LibraryFacade, managers) -> Entity (domain + registries) -> PersistenceManager (JPA) -> MySQL.

- **view-1.puml - component view.** Shows the components in the booking process and their dependencies:
  - Request handling: Swing wizard, Web UI, `ReservationController`, `StudyRoomController` and `LibraryFacade`.
  - Booking rules and availability: `ReservationManager`, `StudyRoomManager`, `Student`, `StudyRoom`, `Area`, `Seat`, `AssignmentStrategy`.
  - Reservation storage: `Reservation` (state pattern), `ReservationRegistry`, `PersistenceManager`.
  - Notifications: `NotificationManager` -> `NotificationService` -> `NotificationServiceAdapter` -> `ExternalEmailGateway`, plus the scheduler.
  
  Use it to see which components a rule change touches and what else depends on them.
- **view-2.puml - sequence view of `makeReservation`.** Shows the order of the validations, the availability check, seat assignment, persistence and notification. It marks the `synchronized` block where uniqueness and availability are checked together. It also shows that a notification failure doesn't roll back the booking. The background expiry and reminder job is included at the end.

Observations from the code:
- New rules most naturally go into the `makeReservation` validation chain in `ReservationManager`. Rules that depend on stored data need new queries in `ReservationRegistry`.
- `cancelReservation` and `performCheckIn` have their own rules in `Reservation`: a 6-hour cancellation window and a 10-minute check-in tolerance.
- Seat availability is defined in `Seat.isAvailable` and `ReservationRegistry.occupiesSlot`. `StudyRoomManager` (seat map) and the statistics code reuse these, so changes there affect them too.
- Changing the states in `Reservation` affects `NotificationManager.messageForState`, which switches over every state.
- The e-mail gateway is a stub that always returns 200.
