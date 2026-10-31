# UML sequence diagram: user registration (POST /api/auth/register)

**Takeaway:** a registration request goes form → `AuthenticationController` → `LibraryFacade` → `UserManager`. `UserManager` alone validates the data, checks uniqueness through `UserRegistry`/`PersistenceManager`, builds the user through a role factory and saves it. Every failure returns to the caller as an exception, mapped to HTTP 400 by the controller.

**Stakeholder:** integration tester. **Detail level:** detailed, limited to this one feature. The tester needs every failure branch, so the view has 7 lifelines and 23 messages, which is within the detailed budget of ≤7 and ≤25.

## How the view addresses the concern
| Concern detail | Where in the view |
|---|---|
| Handles the request | `AuthenticationController` (msg 1-2, 5-6, 23); `LibraryFacade` is a pure delegating entry point (msg 2-3) |
| Validates personal data and role | `UserManager` self-call (msg 4) and the `[invalid data]` branch |
| Role-specific data (student ID, librarian code) | Format validation in `UserManager` (msg 4); `StudentFactory` or `LibrarianFactory` stores the identifier on the new user (msg 13-14); the uniqueness lookup is chosen by role (msg 7) |
| Validity and uniqueness of the account | Msg 7-10 (`UserManager` → `UserRegistry` → `PersistenceManager`) and the `[already used]` branch |
| Persists the new user | Msg 15-18 (`UserRegistry.registerUser` → `PersistenceManager.save`, a JPA persist) and the `[not saved]` branch |
| Invalid or already existing data | Three nested `alt` fragments: invalid data, duplicate email or identifier, save failure. Each ends in an exception and an error response, and nothing is persisted |
| Integration points to test | Seams: form↔controller (HTTP), controller↔facade↔`UserManager`, `UserManager`↔`UserRegistry`, `UserRegistry`↔`PersistenceManager`/DB, `UserManager`↔factory |

Evidence is in `inventory.json`. `check_inventory.py` result: 0 issues, 7 elements, 13 relations (exit 0).

## Omitted on purpose
Entities (`User`, `Student`, `Librarian`), `UserDTO`, `JpaUtil`, the login flow, and the individual field-level validation rules (collapsed into msg 4). `UserRegistry.institutionalEmailExists` and `findStudentByStudentNumber` / `findLibrarianByCode` are collapsed into msg 7, and the two `findFirstByFields` calls into msg 8 ("x2").

## Assumptions and unconfirmed items
- The Swing `Registration` form calls `LibraryFacade.register` directly (`Registration.java:134`), so it skips the controller and the HTTP mapping. The view draws the web path and shows both forms as one lifeline.
- `RestExceptionHandler` maps only `IllegalArgumentException`, `IllegalStateException` and `SecurityException`. The save-failure `RuntimeException` is not mapped (unconfirmed): the view labels it a generic "error response", and the real HTTP status (probably Spring's default 500) was not verified.
- Uniqueness is checked in code, and the entity columns are also `unique` (`User.java:21`, `Student.java:19`, `Librarian.java:13`). So a concurrent duplicate would surface as a save failure.
- The `um` self-call is not tracked by `check_inventory.py`, so it is listed under `omitted` in `inventory.json` with evidence.

## Check result
`puml-check`: OK, with 2 info lines (the `[saved]` label sits on a lifeline, and 5 of 22 messages span lifelines). The first renders had lifeline-crossing warnings. I fixed them by shortening labels and moving the factory lifeline to the end, and the final run has no warnings. I viewed the PNG. No reviewer revision has been done.
