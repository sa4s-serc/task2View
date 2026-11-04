# Seat booking: UML component diagram (overview)

**Takeaway:** both front ends (Swing UI, REST API) call `LibraryFacade`, which delegates booking to `ReservationManager`. That manager validates and assigns the seat and saves it through the domain registries. It then notifies observers. `StudyRoomManager` serves the availability data used while picking a seat.

Stakeholder: software developer about to modify seat booking. Detail level: overview (given), 7 components, wording uses technology names.

## How the concern is answered
- **Main components involved:** the 7 boxes (UI, REST API, Facade, Reservation Manager, Study Room Manager, Domain model & persistence, Notification). Blue marks the core booking flow. Edges are dashed «use» dependencies, numbered 1 browse availability, 2 makeReservation, 3 check/assign/save, 4 notify.
- **How they interact:** the arrows read top to bottom as the call chain of `makeReservation` (`ReservationSummary.java:100`, `ReservationController.java:29`, `LibraryFacade.java:118`, `ReservationManager.java:65-96`). Availability queries from both front ends (`DateAndRoomSelection.java:214`, `TimeSlotSelection.java:87`, `AreaSelection.java:85`, `StudyRoomController.java:44-65`) go through the facade to the Study Room Manager before booking; the binding seat check is inside the Reservation Manager (`ReservationManager.java:85-91, 378-400`).

Evidence and member mapping: `inventory.json`.

## Omitted on purpose
DTOs, `UserManager` and user factories, `NotificationScheduler`, the MySQL database as a box, the reservation state classes (inside "Domain model"). Undrawn dependencies (notification→domain, facade→notification, room manager→notification) belong to reminder and room-deletion paths. A balanced/detailed view of `ReservationManager` would show the internal steps (strategy, state, observer).

## Assumptions
None marked unconfirmed. The Swing UI calls the facade in-process (no HTTP client found).

## Revision after critique-1 (previous version in `v1/`)
- Front-end edges now carry both browse availability and makeReservation; flow steps are numbered.
- Responsibilities corrected: Study Room Manager is for display; Reservation Manager checks availability and assigns the seat.
- Relations are dashed «use» dependencies; the non-standard `<<accent>>` stereotype is removed (highlight is a plain fill).
- Not adopted: showing LibraryFacade's provided interface or NotificationService as separate elements (kept at overview); notification is labelled as reservation observer on the Notification component.

## Check result
puml-check: OK, no overlaps or edges through text (ratio 0.97, top-to-bottom; left-to-right was too wide). check_inventory.py (`--level overview --graph`): 0 issues; 3 notes for undrawn dependencies, listed above as omitted.
