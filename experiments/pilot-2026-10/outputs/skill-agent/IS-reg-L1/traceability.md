# Traceability

## V1-client-server

| Element | Files | Symbols |
|---|---|---|
| SpringBoot (`cmp:it.unina.reservations.boundary.SpringBoot`) | JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/AuthenticationController.java<br>JavaProject/src/main/java/it/unina/reservations/boundary/SpringBoot/RestExceptionHandler.java | it.unina.reservations.boundary.SpringBoot.AuthenticationController<br>it.unina.reservations.boundary.SpringBoot.RestExceptionHandler |
| Swing (`cmp:it.unina.reservations.boundary.Swing`) | JavaProject/src/main/java/it/unina/reservations/boundary/Swing/Registration.java | it.unina.reservations.boundary.Swing.Registration |
| controller (`cmp:it.unina.reservations.controller`) | JavaProject/src/main/java/it/unina/reservations/controller/LibraryFacade.java<br>JavaProject/src/main/java/it/unina/reservations/controller/UserManager.java | it.unina.reservations.controller.LibraryFacade<br>it.unina.reservations.controller.UserManager |
| factory (`cmp:it.unina.reservations.controller.factory`) | JavaProject/src/main/java/it/unina/reservations/controller/factory/LibrarianFactory.java<br>JavaProject/src/main/java/it/unina/reservations/controller/factory/StudentFactory.java<br>JavaProject/src/main/java/it/unina/reservations/controller/factory/UserFactory.java | it.unina.reservations.controller.factory.LibrarianFactory<br>it.unina.reservations.controller.factory.StudentFactory<br>it.unina.reservations.controller.factory.UserFactory |
| entity (`cmp:it.unina.reservations.entity`) | JavaProject/src/main/java/it/unina/reservations/entity/Librarian.java<br>JavaProject/src/main/java/it/unina/reservations/entity/Student.java<br>JavaProject/src/main/java/it/unina/reservations/entity/User.java<br>JavaProject/src/main/java/it/unina/reservations/entity/UserRegistry.java | it.unina.reservations.entity.Librarian<br>it.unina.reservations.entity.Student<br>it.unina.reservations.entity.User<br>it.unina.reservations.entity.UserRegistry |
| database (`cmp:it.unina.reservations.database`) | JavaProject/src/main/java/it/unina/reservations/database/JpaUtil.java<br>JavaProject/src/main/java/it/unina/reservations/database/PersistenceManager.java | it.unina.reservations.database.JpaUtil<br>it.unina.reservations.database.PersistenceManager |

Overflow (not drawn): `ds:reservationsdb` — `JavaProject/src/main/resources/META-INF/persistence.xml:21`.
