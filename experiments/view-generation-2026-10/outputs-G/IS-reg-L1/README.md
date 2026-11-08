# User registration: UML sequence diagram (balanced)

**Takeaway:** a registration request travels entry point → LibraryFacade → UserManager → UserRegistry → PersistenceManager → MySQL, and any validation, duplicate or save failure comes back as an exception shown to the user.

**Stakeholder:** integration tester. **Detail level:** balanced (as given): the architectural roles on the path with their calls, not every class.

## Concern details
- *System components involved*: the seven lifelines. The Swing form and the REST endpoint `POST /api/auth/register` share one lifeline because both call `LibraryFacade.register` with the same six fields.
- *How they interact*: messages 1–20 show the main flow (validate, two uniqueness lookups, create user, insert, return a UserDTO) and one `alt` for the failure path (invalid input, duplicate email or identifier, failed save).

Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation).

## Omitted on purpose
DTOs, entity classes, UI helpers and the login screen. The three factory classes and the individual validators are collapsed into self-calls on UserManager. Each failure type (the several validation rules) is not separated in the `alt`.

## Assumptions
- Persistence settings come from `persistence.xml` (MySQL at localhost:3306); the `db` lifeline is based on that config.
- The two uniqueness checks (email, identifier) are drawn as one call labelled "2 lookups".
- Passwords are stored as given; no hashing step exists in the code.

## Check results
- puml-check: OK, 0 warnings (one info about the else label position).
- check_inventory.py (--level balanced, with graph): exit 0, 0 issues (the note concerns the user and database lifelines, which have no code members).
