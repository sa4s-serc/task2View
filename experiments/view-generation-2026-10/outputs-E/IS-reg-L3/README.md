# View: user registration (UML sequence diagram, balanced)

**Takeaway:** `UserManager.register` validates first, then checks email and identifier uniqueness through `UserRegistry`/`PersistenceManager`, builds a Student or Librarian through the matching factory and saves it. Each failure exits early, throws, and nothing further runs.
**Stakeholder:** integration tester. **Detail:** balanced (given), 7 lifelines, engineering wording (class names, HTTP). A detailed level would split the validation self-call (04) into its per-field checks.

## Concern coverage
- Request handling: HTTP client → `AuthenticationController` → `LibraryFacade` → `UserManager` (01-03). The Swing `Registration` form is a second entry: it rejects blank fields, then calls `LibraryFacade` directly (note over the first lifelines).
- Validation of data and role: self-message 04 (role, names, unina.it email, password, identifier format).
- Role-specific data: `alt` on role for the identifier lookup (`findStudentByStudentNumber` / `findLibrarianByCode`, 12-15) and for the factory (`StudentFactory` sets studentNumber, `LibrarianFactory` sets internalIdentifierCode, 18-21). Student ID is one uppercase letter + 8 digits; librarian code is alphanumeric.
- Validity and uniqueness: validation (04), then email check (08-10), then identifier check (12-16), each followed by its own `break`.
- Persistence: `registerUser` → `save`; `save` returns false after a rollback on a persistence error (22-25).
- Invalid or existing data: three `break` fragments (invalid data: registry never called; email taken; ID in use) and a final `alt` (saved / save failed). Exceptions return along the call chain facade → controller. `RestExceptionHandler` maps `IllegalArgumentException` to HTTP 400; the save-failure `RuntimeException` is not mapped by it.
- Integration points: controller↔facade, facade↔manager, manager↔registry (three lookups, one save), registry↔persistence, manager↔factory, and the controller's HTTP mapping.

Evidence: `inventory.json`. Final results: `check_inventory.py --level balanced`: 0 issues; `puml-check`: OK (info lines only).

## Revision (from critique-1.json; v1 kept in `v1/`)
Changed: validation moved before any registry call; email and identifier lookups split into separate messages with early exits; role shown as `alt`; exceptions and results returned along the call chain; second (Swing) entry added as a note; student ID format corrected; save rollback stated.
Not followed literally: Swing is a note, not an eighth lifeline, to stay within the 7-lifeline budget. Exception replies for the second and third `break` stop at the facade ("propagates as above") instead of repeating the three-hop chain.

## Omitted
DTOs, entities, `JpaUtil`, the Swing dialog flow, the login flow.

## Assumptions
- The message count (29 including returns) exceeds the balanced guideline of 12; kept because the error paths and role branches were asked for.
- The HTTP status for the unmapped `RuntimeException` is not drawn (framework default, not shown in code).
- Persistence is one lifeline that includes MySQL (persistence.xml).
