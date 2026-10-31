# Component view: seat booking

**Takeaway:** every booking request, from web or Swing, funnels through `LibraryFacade` into `ReservationManager`. That class holds all booking rules and collaborates with the registries, the domain model, the seat-assignment strategy and the notification observer. New rules belong in `ReservationManager`, and possibly in the model classes it calls.

Stakeholder: software developer about to add booking rules. Detail level: *detailed* for the booking area only (15 components, within the ≤20 budget). Wording uses technology names (Spring, JPA, HTTP), since the audience is engineering.

## How the view answers the concern
- **Components and responsibilities:** each box carries its responsibility in its name (see inventory).
- **Interaction:** edges run caller to callee with a verb label. Dashed edges are dependencies the code resolves through a singleton or observer, not a direct field.
- **Affected parts:**
  - Primary: `ReservationManager`.
  - Likely: Reservation Model (`Student.hasActiveOrConfirmedReservationForDateAndSlot` is already a rule), Room and Seat Model (`Seat.isAvailable`, `Area.getAvailableSeats`), and the Reservation Registry queries.
  - If a rule needs new inputs: `ReservationRequestDTO`, the REST API and the UIs (entry points, so a rule changing the request shape touches them).
  - Notification Manager, if a rule adds a message.
  - Everything below the registries is unaffected unless the schema changes.

## Inventory (element → evidence)
- Web Pages: `static/reservation.html:385` (POST /reservations/create), `app.js:2`
- Swing Booking Wizard: `boundary/Swing/ReservationSummary.java:100`
- Reservation REST API: `boundary/SpringBoot/ReservationController.java:15-49`
- Expiry Scheduler: `boundary/NotificationScheduler.java:15-29`
- LibraryFacade: `controller/LibraryFacade.java:117-150`, `:162`
- ReservationManager: `controller/ReservationManager.java:65-102` (rules: `:104`, `:151`, `:142`, `:378`)
- Seat Assignment Strategy: `controller/strategy/AssignmentStrategy.java:10`, set at `ReservationManager.java:39`
- Notification Manager: `controller/NotificationManager.java:15`, attached at `ReservationManager.java:120-123`
- Reservation Model: `entity/Reservation.java:16`, `:179-182`, `entity/Student.java:42`
- Room and Seat Model: `entity/Seat.java:44-52`, `entity/Area.java:49`
- Reservation, Room, User Registry: `entity/ReservationRegistry.java:33`, `StudyRoomRegistry.java:125`, `UserRegistry.java:16`
- Persistence Manager: `database/PersistenceManager.java`, created in each registry (`ReservationRegistry.java:20`)
- Notification Gateway: `boundary/ExternalEmailGateway.java:12` (stub), reached via `NotificationService`

## Omitted on purpose
DTOs, state classes (folded into Reservation Model), factories, user registration, room management and monitoring, `RestExceptionHandler`, `NotificationServiceAdapter` / `NotificationConfiguration` (folded into the gateway), MySQL (a deployment concern).

## Assumptions
- "Reservation Model" and "Room and Seat Model" group domain classes into one box each. They are not separate modules in the code.
- `StudyRoomManager` also touches reservations (`controller/StudyRoomManager.java:167-174`, forced cancel on room deletion). It is omitted but is a possible impact point.

## Check
puml-check: OK, 0 crossings, 0 warnings (the `busy` note is info only, 20 edges). The first run flagged an edge through its label, which I fixed. The image review needed no changes.
