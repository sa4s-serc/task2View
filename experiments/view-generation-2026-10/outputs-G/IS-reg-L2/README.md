# User registration: UML sequence diagram (balanced)

**Takeaway:** a registration request enters through the Swing form or `POST /api/auth/register`, passes `LibraryFacade` to `UserManager`, which validates it and checks uniqueness through `UserRegistry`/`PersistenceManager` before creating and persisting a Student or Librarian in MySQL. Failures travel back to the caller as exceptions.

Stakeholder: integration tester. Detail level: balanced (the parts involved, with their operations).

## How the view answers the concern
- **Main components and responsibilities**: the six lifelines (user, entry point, `LibraryFacade`, `UserManager`, `UserRegistry` + `PersistenceManager`, MySQL). Each one's role is in `inventory.json`.
  - Entry point: the form rejects blank fields; the REST controller only forwards.
  - `LibraryFacade`: delegates.
  - `UserManager`: validates, checks uniqueness, picks the factory, builds the DTO.
  - `UserRegistry` + `PersistenceManager`: lookups and the transactional persist.
- **Interaction on account creation**: messages 1–17 are the main flow. The nested `alt` blocks show the two error paths: input validation fails, or the email/identifier is a duplicate or the save fails.
- **Integration points to exercise**:
  1. Swing form or REST endpoint to `LibraryFacade` (messages 1–3).
  2. `LibraryFacade` to `UserManager` (4).
  3. `UserManager` to `UserRegistry` for the uniqueness checks (6, 8).
  4. `UserManager` to the factories and `registerUser` (11–12).
  5. Registry to MySQL via JPA, for SELECT and INSERT (7, 9, 13).
  6. Error propagation to the caller (18–23).

Evidence is in `inventory.json`. `check_inventory.py --level balanced --graph .claude/repo-graph.json` gives 0 issues; one note says `user` and `db` have no members to check against the graph.

## Omitted on purpose
- `UserDTO`, `UserFactory` classes (shown as one self-call), `JpaUtil` and Swing helpers.
- The login flow.
- Individual validation rules, which are collapsed into one self-call.
- Detailed level would add the per-field rules (unina.it email regex, student ID `[A-Z]\d{8}`, password 8–32 characters).

## Assumptions
- The Swing form and the REST controller are drawn as one lifeline because they follow the same path after the entry point. Only the form checks for blank fields and shows a dialog; the REST call returns the `UserDTO`.
- The `INSERT` is inferred from JPA `persist`/`commit` in `PersistenceManager.save`; the exact SQL is not in the code.
- Passwords are stored as given. The code shows no hashing.

## Check result
`puml-check` reports the `aspect` ratio warning (1.1 vs 1.78) and a label-crossing warning on `[invalid]`. I accepted both: the diagram is a tall sequence of 23 messages, and a clear label matters more here. I did not run a separate fresh-context review.
