# Traceability (element → files and symbols)

## V1-decomposition

| Element | Files | Symbols |
|---|---|---|
| ReservationController | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/ReservationController.java | it.unina.reservations.boundary.SpringBoot.ReservationController |
| ReservationSummary | JavaProject/src/main/java/it/unina/reservations/boundary/Swing/ReservationSummary.java | it.unina.reservations.boundary.Swing.ReservationSummary |
| LibraryFacade | JavaProject/src/main/java/it/unina/reservations/controller/LibraryFacade.java | it.unina.reservations.controller.LibraryFacade |
| ReservationManager | JavaProject/src/main/java/it/unina/reservations/controller/ReservationManager.java | it.unina.reservations.controller.ReservationManager |
| FirstAvailableAssignment | JavaProject/src/main/java/it/unina/reservations/controller/strategy/AssignmentStrategy.java<br>JavaProject/src/main/java/it/unina/reservations/controller/strategy/FirstAvailableAssignment.java | it.unina.reservations.controller.strategy.FirstAvailableAssignment<br>it.unina.reservations.controller.strategy.AssignmentStrategy |
| NotificationManager | JavaProject/src/main/java/it/unina/reservations/controller/NotificationManager.java<br>JavaProject/src/main/java/it/unina/reservations/entity/Observer.java | it.unina.reservations.controller.NotificationManager<br>it.unina.reservations.entity.Observer |
| NotificationServiceAdapter | JavaProject/src/main/java/it/unina/reservations/boundary/NotificationServiceAdapter.java<br>JavaProject/src/main/java/it/unina/reservations/controller/NotificationService.java | it.unina.reservations.boundary.NotificationServiceAdapter<br>it.unina.reservations.controller.NotificationService |
| ExternalEmailGateway | JavaProject/src/main/java/it/unina/reservations/boundary/ExternalEmailGateway.java | it.unina.reservations.boundary.ExternalEmailGateway |
| Reservation | JavaProject/src/main/java/it/unina/reservations/entity/Reservation.java | it.unina.reservations.entity.Reservation |
| Student | JavaProject/src/main/java/it/unina/reservations/entity/Student.java | it.unina.reservations.entity.Student |
| Area | JavaProject/src/main/java/it/unina/reservations/entity/Area.java | it.unina.reservations.entity.Area |
| Seat | JavaProject/src/main/java/it/unina/reservations/entity/Seat.java | it.unina.reservations.entity.Seat |
| ReservationRegistry | JavaProject/src/main/java/it/unina/reservations/entity/ReservationRegistry.java | it.unina.reservations.entity.ReservationRegistry |
| StudyRoomRegistry | JavaProject/src/main/java/it/unina/reservations/entity/StudyRoomRegistry.java | it.unina.reservations.entity.StudyRoomRegistry |
| PersistenceManager | JavaProject/src/main/java/it/unina/reservations/database/PersistenceManager.java | it.unina.reservations.database.PersistenceManager |

## V2-uses

| Element | Files | Symbols |
|---|---|---|
| ReservationController | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/ReservationController.java | it.unina.reservations.boundary.SpringBoot.ReservationController |
| ReservationSummary | JavaProject/src/main/java/it/unina/reservations/boundary/Swing/ReservationSummary.java | it.unina.reservations.boundary.Swing.ReservationSummary |
| LibraryFacade | JavaProject/src/main/java/it/unina/reservations/controller/LibraryFacade.java | it.unina.reservations.controller.LibraryFacade |
| ReservationManager | JavaProject/src/main/java/it/unina/reservations/controller/ReservationManager.java | it.unina.reservations.controller.ReservationManager |
| FirstAvailableAssignment | JavaProject/src/main/java/it/unina/reservations/controller/strategy/AssignmentStrategy.java<br>JavaProject/src/main/java/it/unina/reservations/controller/strategy/FirstAvailableAssignment.java | it.unina.reservations.controller.strategy.FirstAvailableAssignment<br>it.unina.reservations.controller.strategy.AssignmentStrategy |
| NotificationManager | JavaProject/src/main/java/it/unina/reservations/controller/NotificationManager.java<br>JavaProject/src/main/java/it/unina/reservations/entity/Observer.java | it.unina.reservations.controller.NotificationManager<br>it.unina.reservations.entity.Observer |
| NotificationServiceAdapter | JavaProject/src/main/java/it/unina/reservations/boundary/NotificationServiceAdapter.java<br>JavaProject/src/main/java/it/unina/reservations/controller/NotificationService.java | it.unina.reservations.boundary.NotificationServiceAdapter<br>it.unina.reservations.controller.NotificationService |
| ExternalEmailGateway | JavaProject/src/main/java/it/unina/reservations/boundary/ExternalEmailGateway.java | it.unina.reservations.boundary.ExternalEmailGateway |
| Reservation | JavaProject/src/main/java/it/unina/reservations/entity/Reservation.java | it.unina.reservations.entity.Reservation |
| Student | JavaProject/src/main/java/it/unina/reservations/entity/Student.java | it.unina.reservations.entity.Student |
| Area | JavaProject/src/main/java/it/unina/reservations/entity/Area.java | it.unina.reservations.entity.Area |
| Seat | JavaProject/src/main/java/it/unina/reservations/entity/Seat.java | it.unina.reservations.entity.Seat |
| ReservationRegistry | JavaProject/src/main/java/it/unina/reservations/entity/ReservationRegistry.java | it.unina.reservations.entity.ReservationRegistry |
| StudyRoomRegistry | JavaProject/src/main/java/it/unina/reservations/entity/StudyRoomRegistry.java | it.unina.reservations.entity.StudyRoomRegistry |
| PersistenceManager | JavaProject/src/main/java/it/unina/reservations/database/PersistenceManager.java | it.unina.reservations.database.PersistenceManager |

## V3-context

| Element | Files | Symbols |
|---|---|---|
| Progetto-IS-main-English | JavaProject/src/main/java/it/unina/reservations/ReservationsApplication.java | — |
| Student | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/ReservationController.java<br>JavaProject/src/main/java/it/unina/reservations/boundary/Swing/ReservationSummary.java | — |
| ExternalEmailGateway | JavaProject/src/main/java/it/unina/reservations/boundary/ExternalEmailGateway.java | — |
| reservationsdb | JavaProject/src/main/resources/META-INF/persistence.xml | — |
