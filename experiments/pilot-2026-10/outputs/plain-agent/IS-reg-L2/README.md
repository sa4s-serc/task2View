# Registration architecture views (IS-reg-L2)

Basis: `JavaProject/src/main/java/it/unina/reservations/**`, `static/registration.html`, `app.js`, `persistence.xml`, `RegistrationTest`.

## view-1.puml - Component view with integration points
Shows the components on the registration path (web form and Swing form, `AuthenticationController`, `RestExceptionHandler`, `LibraryFacade`, `UserManager`, user factories, `UserRegistry`, entities, `UserDTO`, `PersistenceManager`/`JpaUtil`, MySQL), their responsibilities, and numbered integration points IP1-IP9 (HTTP, facade, manager->factory, manager->registry, registry->persistence, JPA->DB). Why: gives the tester the component inventory and the seams at which integration tests can be anchored. Note that the existing `RegistrationTest` enters at the facade and so does not cover IP1/IP3 (HTTP binding, status codes) or the UI.

## view-2.puml - Sequence view of a registration
Shows the runtime order of calls for `POST /api/auth/register`: validation, email and identifier uniqueness lookups against the DB, factory creation, persistence, DTO return, and every failure branch with its outcome (400 `{error}` via `RestExceptionHandler`; save failure raises a `RuntimeException` that the handler does not map). Why: it gives the interactions and the expected outcomes per branch, from which integration test cases and oracles are derived (e.g. duplicate email/identifier require a real DB; role-specific factories and subtype tables).

Observations from the code: the Swing client calls `LibraryFacade` directly (no HTTP); singletons are shared across tests so DB cleanup is needed (`RegistrationTest` empties tables); the test unit points to `reservationsdb_test` on MySQL.
