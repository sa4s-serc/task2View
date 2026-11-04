# UML sequence diagram: user registration

**Takeaway:** Registration is submitted from the Swing form through `LibraryFacade` to `UserManager`, which validates first and only then queries and saves through `UserRegistry`/`PersistenceManager` (JPA, MySQL); each failure (blank field, invalid input, duplicate, failed save) ends in a distinct error shown in an error dialog.

**Stakeholder:** integration tester. **Detail level:** balanced (given): 5 lifelines, 15 messages including self-call and replies (the budget is 12; the extra messages are replies and failure exits an end-to-end tester needs to tell failures apart; see Revision).

## How the concern is addressed
- *System components involved*: the lifelines user, Registration form, LibraryFacade, UserManager, UserRegistry/PersistenceManager (database access shown in message labels).
- *How they interact*: main flow top to bottom with replies; nested `alt` fragments name the three backend failures and their exception types; a `break` fragment shows the client-side blank-field check that never reaches the facade.
- The REST entry `AuthenticationController` (`POST /api/auth/register`) calls the same `LibraryFacade.register`; shown in a note.

Evidence is in `inventory.json`.

## Omitted on purpose
REST controller as a lifeline, DTOs, entities, student/librarian factories (inside `UserManager`), Login window, per-role validation rules, separate MySQL lifeline.

## Assumptions
Failure replies pass through `LibraryFacade` unchanged (no catch). The diagram is drawn for the Swing entry.

## Revision (v1 kept in `v1/`)
Addressed from critique-1: validation is now a `UserManager` self-call before any lookup (no SELECT on invalid input); blank-field check added as a `break`; replies from the persistence lifeline added, with `saved=false` becoming `RuntimeException`; failure guards split by cause with exception types named; activations closed; message count corrected.
Trade-off: to stay near the budget I merged the MySQL lifeline into the persistence lifeline (SELECT/INSERT in labels), but the message count is still above 12 (15); I kept it because the reviewer's missing items are all needed and not detail beyond balanced. The self-call is not counted by `check_inventory.py`.

## Check results
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (one note: `user` has no code members), 14 relations plus the self-call.
- `puml-check`: 0 warnings in the final run.
