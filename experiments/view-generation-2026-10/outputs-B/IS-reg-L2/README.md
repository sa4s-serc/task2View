# Sequence diagram: new user registration

**Takeaway:** a registration request passes through a fixed chain, UI → AuthenticationController → LibraryFacade → UserManager → UserRegistry → PersistenceManager → MySQL. All validation and the duplicate checks are in UserManager, so the tester can exercise each hop and each failure mode on that path.

**Stakeholder:** integration tester. **Detail level:** balanced (one feature; 8 lifelines counting the actor, 12 forward messages plus replies). Wording is technical (REST, JPA, MySQL) because the reader is an engineer.

## How it answers the concern
| Concern | Where in the view |
|---|---|
| Main components and responsibilities | The lifelines. Responsibilities are given in the inventory below. The self-messages on UserManager show validation and user creation. |
| How they interact | The message order from "submit form" to the reply. The `alt` shows the rejected and saved outcomes. |
| Integration points to exercise | See the list below; IP1 is marked in the diagram. |

Integration points (the numbering is mine, not from the code):
- **IP1 UI → AuthenticationController:** `POST /api/auth/register`, form-encoded, with `role, name, surname, email, password, identifier`. The Swing `Registration` form bypasses REST and calls `LibraryFacade` directly (`Registration.java:116-135`).
- **IP2 AuthenticationController → LibraryFacade → UserManager:** the facade only delegates.
- **IP3 UserManager → UserRegistry → PersistenceManager → MySQL, read:** the duplicate email and identifier checks.
- **IP4 The same chain, write:** the transactional INSERT. `save` returns false on failure, which UserManager turns into a `RuntimeException`.
- **IP5 Error mapping:** `RestExceptionHandler` maps `IllegalArgumentException` to HTTP 400 `{error}`.

## Inventory (element → evidence)
- Registration UI: `static/registration.html:52-68` posts through `app.js` `api()`; `boundary/Swing/Registration.java:116`.
- AuthenticationController (REST endpoint, delegates to the facade): `boundary/SpringBoot/AuthenticationController.java:22-31`.
- LibraryFacade (single entry to the controllers): `controller/LibraryFacade.java:37-40`.
- UserManager (validates, checks duplicates, creates the user via `StudentFactory`/`LibrarianFactory`, builds the DTO): `controller/UserManager.java:65-97`.
- UserRegistry (user lookups and save): `entity/UserRegistry.java:26-67`.
- PersistenceManager (JPA transaction and queries): `database/PersistenceManager.java:19-43, 172`.
- MySQL `reservationsdb`: `META-INF/persistence.xml:21`. Unique constraint on the email column: `entity/User.java:21`.
- Error mapping: `boundary/SpringBoot/RestExceptionHandler.java:19-28`.
- Existing tests that call the facade: `RegistrationTest.java`.

## Omitted on purpose
- `UserDTO`, `JpaUtil` and the Spring/Swing glue.
- The individual validation rules (field formats, `@unina.it` email, password 8-32 characters). They are collapsed into one self-message.
- The repeated email and identifier lookups. They are collapsed into one request (the code does two SELECTs, or one for the email and one for the identifier).
- Login and the other use cases.

## Assumptions
- The `alt` is drawn after the INSERT for readability. Invalid-input and duplicate rejections actually happen before the INSERT, and a failed save happens at the INSERT; a note on the diagram says so.
- A save failure is returned as a `RuntimeException`. `RestExceptionHandler` has no handler for it, so the HTTP result is whatever Spring's default does (unconfirmed). The diagram says "error response" generically.
- The `@unina.it` email rule and the identifier formats are enforced only in `UserManager`; the web form was not checked for client-side rules.

## Check result
- `puml-check` (16:9 target): 1 warning, `aspect`. Sequence diagrams are tall, and it would be cleared only by splitting.
- An earlier version had 5 lifeline-crossing warnings; routing the replies through the facade cleared them.
- Image review: the diagram reads top to bottom with no overlaps. I merged the save-failure branch into one `alt` and added a note to explain it.
