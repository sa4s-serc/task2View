# Seat booking: UML component diagram (overview)

**Takeaway:** both front ends (Swing UI, REST API) call `LibraryFacade`, which delegates booking to `ReservationManager`. That manager validates and assigns the seat and saves it through the domain registries. It then notifies observers. `StudyRoomManager` serves the availability data used while picking a seat.

Stakeholder: software developer about to modify seat booking. Detail level: overview (given), 7 components, wording uses technology names.

## How the concern is answered
- **Main components involved:** the 7 boxes (UI, REST API, Facade, Reservation Manager, Study Room Manager, Domain model & persistence, Notification). Blue marks the core booking flow.
- **How they interact:** the arrows read top to bottom as the call chain of `makeReservation` (`ReservationSummary.java:100`, `ReservationController.java:29`, `LibraryFacade.java:118`, `ReservationManager.java:65-96`). Seat availability queries go through the Study Room Manager.

Evidence and member mapping: `inventory.json`.

## Omitted on purpose
DTOs, `UserManager` and user factories, `NotificationScheduler`, the MySQL database as a box, the reservation state classes (inside "Domain model"). Undrawn dependencies (notification→domain, facade→notification, room manager→notification) belong to reminder and room-deletion paths. A balanced/detailed view of `ReservationManager` would show the internal steps (strategy, state, observer).

## Assumptions
None marked unconfirmed. The Swing UI calls the facade in-process (no HTTP client found).

## Check result
puml-check: OK, no overlaps or edges through text (it warns only about aspect against a 16:9 target; top-to-bottom ratio is 1.07, left-to-right was 3.85). check_inventory.py (`--level overview --graph`): 0 issues; 3 notes for undrawn dependencies, listed above as omitted.
