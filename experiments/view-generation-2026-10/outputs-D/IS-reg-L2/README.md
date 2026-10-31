# UML sequence diagram: user registration

**Stakeholder:** integration tester. **Detail level:** detailed for this one flow (7 lifelines, 24 messages): the tester needs every outcome the tests must cover, not only the happy path.

**Takeaway:** registration is a call chain page → `AuthenticationController` → `LibraryFacade` → `UserManager` → `UserRegistry` → MySQL, in which `UserManager` has four separate exits (invalid input, email in use, identifier in use, save failure). The first three become HTTP 400 through `RestExceptionHandler`; the save failure is not mapped and ends as Spring's default 500.

## How the view answers the concern
- **Components and responsibilities:** seven lifelines named `alias : Type` as in the code, with a one-line responsibility for each in the legend (also in `inventory.json`). `RestExceptionHandler` now has its own lifeline.
- **Interaction:** messages 01–20 are the success path in code order: validate (04), email lookup (06–08), identifier lookup (10–12, `findStudentByStudentNumber` for a student, `findLibrarianByCode` for a librarian), `registerUser` (14–16), then the `UserDTO` replies and 200. Each `break` fragment is an early exit that throws before any later step runs (invalid input happens before any DB access). The closing group shows how exceptions leave: `IllegalArgumentException` → handler → 400 `{"error"}`; `RuntimeException` → 500, handler not involved.
- **Integration points (numbered notes in the diagram):** IP1 form-encoded `@RequestParam` contract; IP2 facade boundary shared with the Swing form; IP3 uniqueness lookups; IP4 transactional INSERT (tests run against `reservationsdb_test`, `src/test/resources/META-INF/persistence.xml:22`); IP5 exception-to-HTTP mapping.

`inventory.json` holds the evidence. `check_inventory.py`: 0 issues, 0 unbacked, 7 elements, 11 relations. `puml-check`: one warning, `aspect` (1585x1477, too tall for 16:9). I kept it: the height comes from the four exits the reviewer asked for, and splitting them across pages would hide the order of checks. One info note remains about the `alt` label position.

## Omitted on purpose
Factories (`UserManager.java:89-90`; creating the object is not an integration point, so the earlier self-message is gone), `UserDTO`, entities, `JpaUtil`, login. The Swing form (`Registration.java:134`) is covered by IP2 only; it has no lifeline.

## Assumptions / unconfirmed
- The 500 for the unmapped `RuntimeException` is Spring's default behaviour, inferred from `RestExceptionHandler` handling only `IllegalArgumentException`, `IllegalStateException` and `SecurityException`; not run.
- `LibraryFacade` has no handling code, so exceptions simply propagate (message 21).
- The exception arrows are drawn as dashed replies labelled `throw ...`, since UML sequence diagrams have no exception arrow.

## Changes from v1 (kept in `v1/`) and why
Followed the reviewer: added the `RestExceptionHandler` lifeline; replaced the single `alt` with ordered `break` exits following `UserManager.register`; added the save-failure/500 case; added replies from `UserRegistry`; real operation names; `name : Type` lifelines; integration-point notes and responsibility legend; the Swing note became part of IP2 (attached to the facade); dropped the factory self-message. Not adopted: a separate reply from MySQL to `UserRegistry` (the results are shown on the `reg` → `mgr` replies, to stay within the lifeline/message size), and MySQL stays a plain lifeline with no stereotype. The reviewer's claim that the test database is `reservationsdb_test` was checked in the code and is correct.
