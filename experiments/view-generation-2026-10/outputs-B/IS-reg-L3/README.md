# Sequence view: user registration (Student / Librarian)

**Takeaway:** A registration request goes Client → AuthenticationController → LibraryFacade → UserManager. UserManager validates the role and personal data, checks uniqueness through UserRegistry/PersistenceManager, builds the role-specific user with a factory, and persists it. Invalid or duplicate data ends in an `IllegalArgumentException` that RestExceptionHandler maps to HTTP 400.

Stakeholder: integration tester. Detail level: balanced-to-detailed for this one feature (7 lifelines, 21 messages with 3 `alt` fragments), because the concern asks for the invalid and duplicate paths and the integration points.

Files: `view.puml` (source), `view.png` (render).

## How the view answers the concern
| Concern | Where |
|---|---|
| Handles the request | Messages 1–3: AuthenticationController (`POST /api/auth/register`) → LibraryFacade → UserManager. The Swing form skips the controller and calls LibraryFacade directly. |
| Validates personal data and role | Message 4 (UserManager): role, password length, name, surname, email (unina.it), identifier format. |
| Role-specific data (student ID / librarian code) | Message 4 and the bottom note (student ID = letter + 8 digits, librarian code alphanumeric); messages 10–11 (role picks the lookup); message 15 (StudentFactory or LibrarianFactory sets the identifier). |
| Validity and uniqueness | Messages 7–12: email check, then identifier check, through UserRegistry → PersistenceManager. |
| Persists the new user | Messages 17–19: `registerUser` → `save` (JPA persist in a transaction). |
| Invalid data | `alt invalid` (5–6): 400 `{"error": message}`. |
| Existing data | `alt duplicate` (13–14): same 400 response. |
| Save failure | `alt not saved` (21): `RuntimeException`. |
| Integration points to test | Client↔Controller (HTTP and error JSON), Controller↔Facade↔UserManager, UserManager↔UserRegistry, UserRegistry↔PersistenceManager↔database, UserManager↔factories. |

## Inventory (element → evidence)
- Registration Client: `static/registration.html:53-57` (POST `/auth/register`); `boundary/Swing/Registration.java:116-134`.
- AuthenticationController: `boundary/SpringBoot/AuthenticationController.java:22-31`.
- RestExceptionHandler (merged into the controller lifeline): `RestExceptionHandler.java:19-28` (IllegalArgumentException → 400).
- LibraryFacade: `controller/LibraryFacade.java:37-39`.
- UserManager: `controller/UserManager.java:65-97` (validation 52-58, 173-221; uniqueness 77-87).
- StudentFactory / LibrarianFactory: `controller/factory/*.java` (UserManager.java:89-90).
- UserRegistry: `entity/UserRegistry.java:26-67`.
- PersistenceManager: `database/PersistenceManager.java:19-37` (`save`), `:172` (`findFirstByFields`).

## Omitted on purpose
UserDTO, User/Student/Librarian entities, JpaUtil, the database itself (shown as the JPA layer), the singleton accessors, the login flow, and the static JS helper `app.js`. The facade and controller hops on the return path are collapsed into one message (5, 13, 20, 21).

## Assumptions / unconfirmed
- The HTTP status for the `RuntimeException` on a failed save (message 21) is unconfirmed. `RestExceptionHandler` has no handler for it, so the framework default presumably applies.
- Messages 5, 13, 20 and 21 run UserManager → Controller or Client directly, standing for the collapsed return through LibraryFacade.
- The uniqueness lookups run in this order (email first, then identifier), so a request with both duplicated reports the email error.
- The email domain `unina.it` is enforced by regex (`UserManager.java:26`).

## Check result
`puml-check` ends with 1 warning (`aspect`: the diagram is tall, ratio 1.23 vs 1.78; kept because a sequence of 21 messages is inherently tall) and 2 info lines (lifeline-spanning messages). The `group-label-crosses-lifeline` warnings were fixed by shortening the alt labels. After viewing the PNG I made no further changes.
