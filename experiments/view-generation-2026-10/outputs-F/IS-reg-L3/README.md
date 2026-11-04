# UML sequence diagram: user registration

**Takeaway:** a registration request flows AuthenticationController → UserManager (via LibraryFacade); UserManager validates, runs two separate uniqueness checks through UserRegistry, builds the role-specific user with a factory and saves it through UserRegistry/PersistenceManager. Every failure is an exception that travels back through AuthenticationController, where RestExceptionHandler turns it into an HTTP response.
**Stakeholder:** integration tester. **Detail level:** balanced (as given): 6 lifelines, 13 messages (one over the 12 default, see below). Files: `view.puml`, `view.png`, `inventory.json`; the previous version is in `v1/`.

## How the concern is answered
- **Handles the request:** `AuthenticationController` (POST /api/auth/register). The Swing form skips it and calls `LibraryFacade.register` directly (note).
- **Validates personal data and role:** `UserManager`, first self-message and the "invalid data or role" branch.
- **Role-specific data:** the same self-message carries the role guards ([Student] ID format `[A-Z]\d{8}` / [Librarian] code); the `createUser` message names StudentFactory vs LibrarianFactory by role.
- **Validity and uniqueness:** two separate lookups on `UserRegistry`, each with its own failure branch: email taken ("Email is already associated"), identifier taken ("Identifier is already in use").
- **Persist:** `registerUser` → `PersistenceManager.save`; the `not saved` branch is guarded by the boolean `save` returns (it catches the exception, rolls back, returns false).
- **Invalid / existing data:** exceptions are drawn from `UserManager` back to `AuthenticationController`; the note states the mapping: `IllegalArgumentException` → 400 `{"error"}`; the save-failure `RuntimeException` is not mapped (Spring default 500).
- **Integration points to cover:** controller↔UserManager (incl. exception→HTTP mapping), UserManager↔UserRegistry (email lookup, identifier lookup, save), UserManager→factory per role, UserRegistry→PersistenceManager (lookup and save, with its boolean result).

## Changes after review (v1 → v2)
- Errors and the result now return along the call chain to `AuthenticationController`, and one `HTTP response` goes to the client; the 400/500 mapping is in a note.
- Uniqueness split into email and identifier checks with separate branches.
- Role guards added on validation and on the factory choice.
- Return values (found / not found, save true / false) appear as branch guards on the alts, not as separate arrows. This keeps the view near the balanced budget (13 messages, 1 over the default 12) instead of adding about six reply arrows.
- `AuthenticationController` activation now closes after the outer alt.
- Not adopted: a separate reply from `UserRegistry`/`PersistenceManager` for each lookup and a reply from the factory (budget; guards carry the information). Lookups' call to `PersistenceManager.findFirstByFields` is collapsed into a note rather than two more arrows. The factories are called as `createUser(...)` rather than a `<<create>>` arrow: the code instantiates them per role (`UserManager.java:89`), noted in the label.

## Omitted on purpose
UserDTO and entity classes, `JpaUtil`, the MySQL database as a separate lifeline, the Swing non-blank precheck, login, per-field validation rules. `LibraryFacade` is a pass-through, merged into the `UserManager` lifeline. A fuller view with every reply and each validation rule would need the detailed level.

## Assumptions
- HTTP 500 for the unmapped save-failure `RuntimeException` is Spring's default (unconfirmed).
- The success status (200) is Spring's default and is not drawn; the arrow says "HTTP response".

## Check result
puml-check: no warnings after shortening branch labels (info only on message spans). check_inventory.py (`--level balanced --graph`): 0 issues, 1 note (client has no members; it is an external actor).
