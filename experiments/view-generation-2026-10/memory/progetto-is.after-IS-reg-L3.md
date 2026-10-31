# Progetto-IS (study-room booking, Java/Spring Boot + Swing + static web)
Layers: boundary -> controller (LibraryFacade singleton) -> managers -> entity registries -> database/PersistenceManager -> MySQL.
Paths below relative to JavaProject/src/main/java/it/unina/reservations (java) or JavaProject/src/main/resources (res).

## Registration flow (verified)
- Web form POSTs `/auth/register` via fetch helper: res/static/registration.html:53-66; helper app.js:41.
- Swing form calls LibraryFacade.register directly: boundary/Swing/Registration.java:116-141.
- REST: AuthenticationController `POST /api/auth/register`, params role,name,surname,email,password,identifier: boundary/SpringBoot/AuthenticationController.java:22-31 (login at :36-40).
- LibraryFacade.register delegates to UserManager: controller/LibraryFacade.java:37-40.
- UserManager.register: validate -> email/identifier format -> duplicate checks -> factory -> registry save -> UserDTO: controller/UserManager.java:65-97. Singletons.
- Rules: password 8-32 (:56-57); email regex *@unina.it (:26,:153); student number [A-Z]\d{8} (:29,:177); role Student|Librarian (:169-171).
- Factories: controller/factory/StudentFactory.java:8-18, LibrarianFactory, UserFactory interface.
- UserRegistry wraps PersistenceManager: entity/UserRegistry.java:26-67.
- PersistenceManager.save: begin/persist/commit, rollback+false on RuntimeException: database/PersistenceManager.java:19-37.
- JPA unit reservationsPU, MySQL localhost:3306/reservationsdb: res/META-INF/persistence.xml:7,21. User entity JOINED inheritance, email unique: entity/User.java:12,21.
- Errors: IllegalArgumentException -> HTTP 400 {error}; SecurityException -> 401: boundary/SpringBoot/RestExceptionHandler.java:18-27.
- Tests call LibraryFacade directly: src/test/java/.../controller/RegistrationTest.java:53+.
- No notification/email step in registration (UserManager.java:65-97 has none).
- Duplicate checks: email via UserRegistry.institutionalEmailExists UserManager.java:77, identifier :81-83; registry finders UserRegistry.java:37-67 all use PersistenceManager.findFirstByFields.
- Failed save -> RuntimeException "could not be saved" UserManager.java:93-95 (not IllegalArgumentException, so RestExceptionHandler.java:19 does not map it to 400).
- Web submit handler redirects to index.html on success: registration.html:53-66; api() throws on !res.ok using body.error: app.js:41-55.
- Swing Registration catches RuntimeException and shows dialog: Registration.java:128-141.

## Notes
- Source comments are placeholder "English implementation note"; identifiers partly Italian (bloccato, tentativi).
- Annotation imports appear as `org.springframework.web.bind.yeartation` (odd rename) in controllers.
- Tooling: plantuml at /opt/homebrew/bin; check script is `python3 -I .claude/skills/plantuml-diagrams/scripts/puml-check`; macOS sed needs `-i ''`.
- Verified again: UserManager.validate :52-58, validateEmail :200-212, validateIdentifier :214-222 (alnum only; student regex extra :177); factory chosen by role UserManager.java:89; registerUser->save UserRegistry.java:26-28.
- puml-new usage: `python3 -I .claude/skills/plantuml-diagrams/scripts/puml-new sequence FILE --title T`; template contains `hide stereotype` (uml-view says remove).
