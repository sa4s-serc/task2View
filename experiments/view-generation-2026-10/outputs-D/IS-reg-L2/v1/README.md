# UML sequence diagram: user registration

**Stakeholder:** integration tester. **Detail level:** balanced (one feature; 6 lifelines, 15 messages incl. returns; the 12-message default is exceeded only by return arrows and the error branch).

**Takeaway:** registration is one synchronous call chain page → `AuthenticationController` → `LibraryFacade` → `UserManager` → `UserRegistry` → MySQL; `UserManager` validates, checks uniqueness, builds the Student/Librarian and persists it, and failures travel back as exceptions that become HTTP 400.

## How the view answers the concern
- **Main components and responsibilities:** the six lifelines (names as in the code); responsibilities are in `inventory.json` and in the message labels (validate, check unused, create, persist).
- **How they interact:** messages 01–12 are the success path (200 `UserDTO`); the `alt` branch (13–15) is the error path (`IllegalArgumentException` → 400 `{"error"}` via `RestExceptionHandler`).
- **Integration points to exercise:** (1) page → REST endpoint (`POST /api/auth/register`, form-encoded params); (2) controller → facade → `UserManager` (the layer boundary; the Swing form enters here, see note); (3) `UserManager` → `UserRegistry` uniqueness lookups (email, student number / librarian code); (4) `UserRegistry`/JPA → MySQL INSERT; (5) exception → HTTP 400 mapping.

Evidence for every element and relation: `inventory.json`. `check_inventory.py`: 0 issues, 0 unbacked, 6 elements, 8 relations. `puml-check`: OK (0 warnings; 1 info about the `alt` label position).

## Omitted on purpose
`UserFactory`/`StudentFactory`/`LibrarianFactory` (collapsed into one `UserManager` self-message), `UserDTO`, entities, `JpaUtil`, login. The Swing `Registration` form is only a note.

## Assumptions / unconfirmed
- A failed save throws `RuntimeException` (`UserManager.java:93-94`), which `RestExceptionHandler` does not map (only `IllegalArgumentException`, `IllegalStateException`, `SecurityException`); the resulting HTTP status (presumably Spring's default 500) is not shown and is unconfirmed.
- Facade return/exception arrows (13–14) are inferred from plain Java propagation; the facade has no handling code.
- Database engine taken from `src/main/resources/META-INF/persistence.xml` (MySQL); the test persistence config was not inspected.
