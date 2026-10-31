# Component view: seat booking and notification (IS-seat-L3)

**Takeaway:** every booking request enters through LibraryFacade and is handled, validated and stored by ReservationManager, so new booking rules belong in ReservationManager (plus the entity availability queries and AssignmentStrategy). Notifications are a side effect triggered by Reservation state changes.

Stakeholder: software developer about to add booking rules. Detail: *detailed* for the booking area (16 elements), technology names included. Files: `view.puml`, `view.png`.

## How the view answers the concern
- **Handle booking requests:** REST ReservationController, Swing wizard and NotificationScheduler all call LibraryFacade, which delegates to ReservationManager.
- **Check seat availability:** ReservationManager asks the entities (Area.getAvailableSeats, Seat.isAvailable), which query ReservationRegistry directly.
- **Apply booking rules:** inside ReservationManager.makeReservation (seat-in-area, one reservation per student/date/slot via Student, availability, seat choice). Seat choice is pluggable through AssignmentStrategy.
- **Manage and store reservations:** ReservationManager creates the Reservation (state pattern), saves it via ReservationRegistry -> PersistenceManager -> MySQL.
- **External services:** Reservation.setState notifies observers; NotificationManager sends through the NotificationService interface, implemented by NotificationServiceAdapter -> ExternalEmailGateway (stub).
- **Impact:** change ReservationManager first. Also affected: Student/Area/Seat (rules that query reservations), ReservationRegistry, REST/Swing callers if the request fields change (ReservationRequestDTO), NotificationManager if new rejections need messages.

## Inventory (file:line, under JavaProject/src/main/java/it/unina/reservations)
- Web/REST ReservationController: boundary/SpringBoot/ReservationController.java:15-49
- Swing wizard: boundary/Swing/ReservationSummary.java:100
- NotificationScheduler: boundary/NotificationScheduler.java:15-29
- LibraryFacade: controller/LibraryFacade.java:117-150, 162
- ReservationManager: controller/ReservationManager.java:65-102 (rules :104, :142, :151; strategy :400; notify :121-122; save :134)
- AssignmentStrategy / FirstAvailableAssignment: controller/strategy/AssignmentStrategy.java, ReservationManager.java:39
- NotificationManager: controller/NotificationManager.java:15,40-60; NotificationService.java:11
- NotificationServiceAdapter: boundary/NotificationServiceAdapter.java:12; ExternalEmailGateway.java:12 (stub); wiring NotificationConfiguration.java:17
- Reservation: entity/Reservation.java:82-88; Student/Seat/Area: entity/Student.java:42, Seat.java:44-52, Area.java:49
- ReservationRegistry: entity/ReservationRegistry.java:33,61,77,120; StudyRoomRegistry, UserRegistry (ReservationManager.java:28-30)
- PersistenceManager: database/PersistenceManager.java:19-37; MySQL: resources/META-INF/persistence.xml:21

## Omitted on purpose
DTOs, state classes, factories, registration/login and room-management flows, StudyRoomManager, monitoring and statistics, REST exception handler, web pages.

## Assumptions
- Entity and registry classes are drawn as components in the "Entity" package; they are really one layer of classes.
- Notification delivery failures are caught and logged in NotificationManager (:57-59), so they do not abort a booking.

## Check result
Final puml-check: 6 warnings (3 bundled-edge, 1 edge-through-text, 1 label-on-border, 1 container-crossing), none overlapping. A left-to-right variant had 4 warnings but tiny text, and a variant with a realization arrow had 7; both were discarded. Image review: layout reads top to bottom, labels sit on their edges.
