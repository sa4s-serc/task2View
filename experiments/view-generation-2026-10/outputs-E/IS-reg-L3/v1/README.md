# View: user registration (UML sequence diagram, balanced)

**Takeaway:** `UserManager` validates role, personal data and role-specific identifier, checks email/identifier uniqueness through `UserRegistry`, builds a Student or Librarian via a factory and persists it via `PersistenceManager`; every failure raises an exception and nothing is saved.
**Stakeholder:** integration tester. **Detail:** balanced (given); 7 lifelines. Wording uses class names and HTTP terms for an engineering audience.

## Concern coverage
- Request handling: Client (Swing `Registration` or HTTP) → `AuthenticationController` → `LibraryFacade` → `UserManager` (messages 1-3).
- Validation of personal data and role: self-message 4 in `UserManager` (role, names, unina.it email, password length, identifier format); note on the role branch.
- Role-specific data: Student ID `[A-Z]+8 digits` vs librarian alphanumeric code (note); `StudentFactory`/`LibrarianFactory` set the matching field.
- Validity and uniqueness: messages 5-8 (email lookup, identifier lookup via `UserRegistry` → `PersistenceManager`).
- Persistence: `registerUser` → `save` (transactional, returns false on failure).
- Invalid/existing data: `alt` branches: invalid format, email/identifier exists, save failure; success returns `UserDTO`. Errors are IllegalArgumentException (HTTP 400 via `RestExceptionHandler`, or an error dialog in Swing).
- Integration points for tests: each arrow between adjacent lifelines (controller/facade, manager/registry, registry/persistence, manager/factory).

Evidence: `inventory.json`. check_inventory.py `--level balanced`: 0 issues. puml-check: renders, only info lines (group labels on lifeline, long messages spanning lifelines).

## Omitted
DTOs, entities, `JpaUtil`, exception-handler class (shown as a label), login flow. A detailed level would split the validation self-call into its per-field checks.

## Assumptions
- Exceptions are drawn straight to the client for brevity; in the REST path they propagate back through facade and controller. The two lookups are collapsed into one message "(x2)". The message count (18 incl. returns) exceeds the balanced guideline of 12 because the error alternatives were requested; kept deliberately.
- Persistence is shown as one lifeline including MySQL (persistence.xml).
