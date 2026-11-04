# UML sequence diagram: user registration

**Takeaway:** Registration is submitted from the Swing form through `LibraryFacade` to `UserManager`, which validates the input, checks email/identifier uniqueness through `UserRegistry`/`PersistenceManager` in MySQL, and only then creates and saves the Student or Librarian; any failure comes back as an exception shown in an error dialog.

**Stakeholder:** integration tester. **Detail level:** balanced (given): 6 lifelines, 12 messages.

## How the concern is addressed
- *System components involved*: the six lifelines (user, Registration form, LibraryFacade, UserManager, UserRegistry/PersistenceManager, MySQL).
- *How they interact*: the message order shows the main flow (submit, validate, look up, insert, UserDTO, confirmation) and one `alt` for the failure path (invalid input, duplicate email or identifier, save failure).
- The REST entry `AuthenticationController` (`POST /api/auth/register`) calls the same `LibraryFacade.register`; it is in a note, not a lifeline.

Evidence for every element and relation is in `inventory.json`.

## Omitted on purpose
REST controller as a separate lifeline, DTOs, entities, the student/librarian factories (folded into `UserManager`), and the Login window. A detailed-level view would split validation rules per role.

## Assumptions
The failure reply passes through `LibraryFacade` unchanged (no catch in the facade). The picture is drawn for the Swing entry; the REST flow differs only in the first two lifelines.

## Check results
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (1 note: user and database have no code members).
- `puml-check`: renders; the last run's output is above in the session. A `message-crosses-lifeline`/group-label info may remain for the failure label.
- Revision: the first draft had 17 messages and skipped the facade on replies; it was cut to 12 and the replies were routed through the facade to match the code.
