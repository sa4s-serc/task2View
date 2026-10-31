# UML sequence diagram: user registration (web path, POST /api/auth/register)

**Takeaway:** a registration request goes from the web page to `AuthenticationController` and on to `UserManager` (via `LibraryFacade`). `UserManager` validates by role, checks the email and then the role-specific identifier through `UserRegistry`, builds the user through the role's factory and saves it through `PersistenceManager`. Failures propagate back as exceptions; `RestExceptionHandler` turns the validation and duplicate ones into HTTP 400 `{error}`.

**Stakeholder:** integration tester. **Detail level:** detailed, for this one feature, with 7 lifelines and 25 messages, which is within the detailed budget (≤7, ≤25).

## How the view addresses the concern
| Concern detail | Where in the view |
|---|---|
| Handles the request | `Web registration page` (msg 01), `AuthenticationController` (02), `RestExceptionHandler` as its own lifeline (07-08) |
| Validates personal data and role | `UserManager` self-calls 03-05: role and password, then the Student or Librarian validation (`alt` on role) |
| Role-specific data | Student ID (letter + 8 digits) vs librarian code (letters/digits) in 04/05; `findStudentByStudentNumber` vs `findLibrarianByCode` in 12/13; the factory in 16-17 |
| Validity and uniqueness | Email lookup first (09-10, `[email exists]`), then the role-specific identifier lookup (12-14, `[id used]`), each with its own error message |
| Persists the new user | `registerUser` → `save` (18-21) and `[not saved]` / `[saved]` |
| Invalid or already existing data | `[invalid data]`, `[email exists]`, `[id used]` end in `IllegalArgumentException`, which becomes 400 `{error}`. `[not saved]` ends in an unmapped `RuntimeException` (default 500). A note says the DB unique columns also reject a concurrent duplicate, which ends in `[not saved]` |
| Integration points | Page↔controller (HTTP, empty fields dropped by the page), controller↔`UserManager`, `UserManager`↔`UserRegistry`↔`PersistenceManager`, `UserManager`↔factory, controller↔`RestExceptionHandler`. A note names the Swing form as a second entry point |

`inventory.json` holds the evidence. `check_inventory.py`: 0 issues, 7 elements, 12 relations.

## Changes in this revision (v1 is kept in `v1/`)
- Split the email and identifier duplicate checks, in the code's order (email first), with a role `alt` for validation, lookup and factory.
- `RestExceptionHandler` is now its own lifeline. The factories are one `:UserFactory` lifeline, and the role is chosen in the message label.
- The user-as-actor is replaced by the web page as a participant. The Swing form is a note naming its separate entry point, since it calls `LibraryFacade.register` directly.
- The save-failure response is labelled as the default 500 (unmapped). A note covers the DB unique constraints and rollback.
- Removed `x2` and the `: persist` return-type notation, and added the note that the page drops empty fields.

## Reviewer points kept as before, and why
- **`LibraryFacade` as its own lifeline:** not added. The class is pure delegation, and an 8th lifeline would exceed the 7-lifeline budget. It is named in msg 02. As a result exceptions are drawn from `UserManager` back to the controller in one step, not through the facade.
- **Swing as a lifeline:** shown only as a note, for the same budget reason. It needs its own view or test list: a dialog message replaces the HTTP status.
- **Lookups to `PersistenceManager`:** the `UserRegistry`→`findFirstByFields` calls are collapsed into the lookup messages. Only `save` is drawn, because the persistence seam matters most there.
- **Reply arrows for exceptions:** kept as dashed replies labelled with the exception type, and the later branches refer to the first full handler path (07-08) in a note. The exception does reach `RestExceptionHandler` through Spring dispatch from the controller, which is how it is drawn.

## Omitted on purpose
Entities, `UserDTO`, `JpaUtil`, the login flow, `LibraryFacade` and the Swing lifeline (see above), and the repeated `findFirstByFields` calls.

## Assumptions and unconfirmed items
- The 500 for an unmapped `RuntimeException` is Spring's default (unconfirmed): the handler has no mapping and the status was not run.
- The `UserManager` self-calls are not tracked by `check_inventory.py`; they are listed under `omitted` with evidence.

## Check result
`puml-check`: OK, with 0 warnings in the final run. The earlier runs' lifeline-crossing warnings were fixed by moving the factory lifeline to the end and shortening labels. `check_inventory.py`: exit 0. I viewed the PNG. No second review has been done.
