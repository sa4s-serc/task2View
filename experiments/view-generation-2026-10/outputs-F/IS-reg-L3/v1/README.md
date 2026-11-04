# UML sequence diagram: user registration

**Takeaway:** a registration request flows AuthenticationController → UserManager (via LibraryFacade), which validates, checks uniqueness through UserRegistry/PersistenceManager, builds the role-specific user with a factory and saves it. Every failure is an exception from UserManager that reaches the client (HTTP 400 on REST).
**Stakeholder:** integration tester. **Detail level:** balanced (as given): 6 lifelines, 11 messages. Files: `view.puml`, `view.png`, `inventory.json`.

## How the concern is answered
- **Handles the request:** `AuthenticationController` (POST /api/auth/register; errors mapped to 400 by `RestExceptionHandler`). The Swing form skips the controller and calls `LibraryFacade` directly (note in the diagram).
- **Validates personal data and role:** `UserManager`, first `alt` (role, name, password, surname, email format).
- **Role-specific data:** `UserManager` checks the student ID format (letter + 8 digits) or librarian code; `Student/Librarian Factory` stores it as studentNumber or librarian code.
- **Validity and uniqueness:** `UserManager` validation, then `UserRegistry` lookups (email, student number or librarian code) via `PersistenceManager`.
- **Persist:** `UserRegistry.registerUser` → `PersistenceManager.save` (JPA transaction, MySQL).
- **Invalid / existing data:** three `alt` branches: invalid data, duplicate email or identifier (nothing saved), save failure.
- **Integration points to cover:** controller→UserManager (including exception→400 mapping), UserManager→UserRegistry (both lookups), UserManager→factory (per role), UserRegistry→PersistenceManager (find and save, incl. save failure).

## Omitted on purpose
UserDTO and entity classes, `JpaUtil`, the MySQL database as a separate lifeline, the Swing non-blank precheck, login. `LibraryFacade` is a pass-through, merged into the `UserManager` lifeline. Collapsed: the internal validation steps are one self-message; the return from PersistenceManager lookups is shown in the message label.
A fuller view (all validation rules per field) would need the detailed level.

## Assumptions
- The HTTP 400 status for the "save failed" RuntimeException is not mapped by `RestExceptionHandler` (only IllegalArgument/IllegalState/Security), so it is not shown as 400; likely a 500 by Spring default (unconfirmed).
- Success is shown as the UserDTO returned to the client (HTTP 200 by Spring default, unconfirmed).

## Check result
puml-check: no warnings, only infos (message spans). check_inventory.py (`--level balanced --graph`): 0 issues, 1 note (client has no members; it is an external actor).
