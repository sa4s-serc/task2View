# Registration sequence view (integration tester)

**Takeaway:** a registration request travels form → AuthenticationController (REST) → LibraryFacade → UserManager (validate, duplicate checks, factory) → UserRegistry → PersistenceManager → MySQL, and every failure comes back as an exception that the REST layer maps to HTTP 400.
Stakeholder: integration tester. Detail level: balanced (one feature), engineering wording (REST, JPA, MySQL).

## Concern coverage
- **Main components and responsibilities:** the seven lifelines and their labels; responsibilities per inventory below.
- **Interaction on account creation:** main flow top to bottom (validate, 2 duplicate lookups collapsed into one message, factory, save, INSERT) plus the `alt` for rejection, save failure and success.
- **Integration points to exercise:** (1) form → `POST /api/auth/register`; (2) controller → LibraryFacade → UserManager; (3) UserManager → UserRegistry duplicate lookups; (4) UserRegistry → PersistenceManager → MySQL (SELECT, INSERT, rollback); (5) exception → HTTP 400 mapping. The Swing form enters at (2), bypassing REST (note in view).

## Inventory (element → evidence; paths under JavaProject/src/main)
- Registration form (web): resources/static/registration.html:53-66 (api helper resources/static/app.js:41); Swing: java/it/unina/reservations/boundary/Swing/Registration.java:116-141
- AuthenticationController: boundary/SpringBoot/AuthenticationController.java:22-31
- RestExceptionHandler (400 mapping): boundary/SpringBoot/RestExceptionHandler.java:19-22
- LibraryFacade.register: controller/LibraryFacade.java:37-40
- UserManager.register (validate, duplicates, factory, save): controller/UserManager.java:65-97; rules :52-58, :26, :29
- StudentFactory/LibrarianFactory: controller/factory/StudentFactory.java:8-18
- UserRegistry: entity/UserRegistry.java:26-28, :37-67
- PersistenceManager.save: database/PersistenceManager.java:19-43
- MySQL reservationsdb, unit reservationsPU: resources/META-INF/persistence.xml:7,21
- Existing tests via the facade: src/test/.../RegistrationTest.java:53+

## Omitted on purpose
Factories as own lifelines (a self-call), JpaUtil, entities/DTO details, login, notifications (registration sends none).

## Assumptions
- DB lookups return nothing in the success path; the lookup/INSERT ordering is drawn before the `alt`, whose first branch is raised before the INSERT.
- Unique email constraint (entity/User.java:21) is not drawn; a violation would surface as save failure.

## Check
puml-check: no lifeline crossings, remaining output is info-level group-label notes only. Image review: fixed messages that jumped over LibraryFacade and clarified the failure branch label.
