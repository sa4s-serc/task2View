# Traceability

## V1-decomposition — Decomposition

| Element | Files | Symbols |
|---|---|---|
| Web client | JavaProject/src/main/resources/static/app.js | — |
| Registration REST endpoint | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/AuthenticationController.java, JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/RestExceptionHandler.java, JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/StudentController.java | it.unina.reservations.boundary.SpringBoot.AuthenticationController, it.unina.reservations.boundary.SpringBoot.RestExceptionHandler, it.unina.reservations.boundary.SpringBoot.StudentController |
| Registration desktop app | JavaProject/src/main/java/it/unina/reservations/boundary/Swing/LibrarianDashboard.java, JavaProject/src/main/java/it/unina/reservations/boundary/Swing/Registration.java, JavaProject/src/main/java/it/unina/reservations/boundary/Swing/StudentDashboard.java | it.unina.reservations.boundary.Swing.Registration, it.unina.reservations.boundary.Swing.StudentDashboard, it.unina.reservations.boundary.Swing.LibrarianDashboard |
| Registration validation service | JavaProject/src/main/java/it/unina/reservations/controller/LibraryFacade.java, JavaProject/src/main/java/it/unina/reservations/controller/UserManager.java, JavaProject/src/main/java/it/unina/reservations/dto/AvailableTimeSlotDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/ReservationRequestDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/RoomDetailDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/StudyRoomCreationDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/StudyRoomDTO.java | it.unina.reservations.controller.LibraryFacade, it.unina.reservations.controller.UserManager, it.unina.reservations.dto.StudyRoomCreationDTO, it.unina.reservations.dto.ReservationRequestDTO, it.unina.reservations.dto.StudyRoomDTO, it.unina.reservations.dto.RoomDetailDTO |
| User and reservation entities | JavaProject/src/main/java/it/unina/reservations/entity/Librarian.java, JavaProject/src/main/java/it/unina/reservations/entity/Reservation.java, JavaProject/src/main/java/it/unina/reservations/entity/Student.java, JavaProject/src/main/java/it/unina/reservations/entity/User.java | it.unina.reservations.entity.Reservation, it.unina.reservations.entity.Student, it.unina.reservations.entity.User, it.unina.reservations.entity.Librarian |
| User persistence storage | JavaProject/src/main/java/it/unina/reservations/database/PersistenceManager.java, JavaProject/src/main/java/it/unina/reservations/entity/ReservationRegistry.java | it.unina.reservations.database.PersistenceManager, it.unina.reservations.entity.ReservationRegistry |
| User account lookup storage | JavaProject/src/main/java/it/unina/reservations/entity/UserRegistry.java | it.unina.reservations.entity.UserRegistry |
| MySQL database | JavaProject/src/main/resources/META-INF/persistence.xml | — |

## V2-client-server — Client-Server

| Element | Files | Symbols |
|---|---|---|
| Web client | JavaProject/src/main/resources/static/app.js | — |
| Registration REST endpoint | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/AuthenticationController.java, JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/RestExceptionHandler.java, JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/StudentController.java | it.unina.reservations.boundary.SpringBoot.AuthenticationController, it.unina.reservations.boundary.SpringBoot.RestExceptionHandler, it.unina.reservations.boundary.SpringBoot.StudentController |
| Registration desktop app | JavaProject/src/main/java/it/unina/reservations/boundary/Swing/LibrarianDashboard.java, JavaProject/src/main/java/it/unina/reservations/boundary/Swing/Registration.java, JavaProject/src/main/java/it/unina/reservations/boundary/Swing/StudentDashboard.java | it.unina.reservations.boundary.Swing.Registration, it.unina.reservations.boundary.Swing.StudentDashboard, it.unina.reservations.boundary.Swing.LibrarianDashboard |
| Registration validation service | JavaProject/src/main/java/it/unina/reservations/controller/LibraryFacade.java, JavaProject/src/main/java/it/unina/reservations/controller/UserManager.java, JavaProject/src/main/java/it/unina/reservations/dto/AvailableTimeSlotDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/ReservationRequestDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/RoomDetailDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/StudyRoomCreationDTO.java, JavaProject/src/main/java/it/unina/reservations/dto/StudyRoomDTO.java | it.unina.reservations.controller.LibraryFacade, it.unina.reservations.controller.UserManager, it.unina.reservations.dto.StudyRoomCreationDTO, it.unina.reservations.dto.ReservationRequestDTO, it.unina.reservations.dto.StudyRoomDTO, it.unina.reservations.dto.RoomDetailDTO |
| User and reservation entities | JavaProject/src/main/java/it/unina/reservations/entity/Librarian.java, JavaProject/src/main/java/it/unina/reservations/entity/Reservation.java, JavaProject/src/main/java/it/unina/reservations/entity/Student.java, JavaProject/src/main/java/it/unina/reservations/entity/User.java | it.unina.reservations.entity.Reservation, it.unina.reservations.entity.Student, it.unina.reservations.entity.User, it.unina.reservations.entity.Librarian |
| User persistence storage | JavaProject/src/main/java/it/unina/reservations/database/PersistenceManager.java, JavaProject/src/main/java/it/unina/reservations/entity/ReservationRegistry.java | it.unina.reservations.database.PersistenceManager, it.unina.reservations.entity.ReservationRegistry |
| User account lookup storage | JavaProject/src/main/java/it/unina/reservations/entity/UserRegistry.java | it.unina.reservations.entity.UserRegistry |
| MySQL database | JavaProject/src/main/resources/META-INF/persistence.xml | — |

## V3-sequence — Sequence

| Element | Files | Symbols |
|---|---|---|
| UserManager | JavaProject/src/main/java/it/unina/reservations/controller/UserManager.java | it.unina.reservations.controller.UserManager |
| AuthenticationController | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/AuthenticationController.java | it.unina.reservations.boundary.SpringBoot.AuthenticationController |
| LibraryFacade | JavaProject/src/main/java/it/unina/reservations/controller/LibraryFacade.java | it.unina.reservations.controller.LibraryFacade |
| UserRegistry | JavaProject/src/main/java/it/unina/reservations/entity/UserRegistry.java | it.unina.reservations.entity.UserRegistry |
| PersistenceManager | JavaProject/src/main/java/it/unina/reservations/database/PersistenceManager.java | it.unina.reservations.database.PersistenceManager |
| UserFactory | JavaProject/src/main/java/it/unina/reservations/controller/factory/UserFactory.java | it.unina.reservations.controller.factory.UserFactory |
