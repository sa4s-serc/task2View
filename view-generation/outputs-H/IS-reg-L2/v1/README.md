# Component view: user registration (balanced)

**Takeaway:** a new student or librarian registers through either the desktop form or the REST endpoint; both converge on the Library facade, the User manager validates and checks duplicates through the User registry, a factory builds the user, and the Persistence manager saves it to the MySQL account database.

Stakeholder: integration tester. Detail level: balanced (given): parts involved in registration with their interfaces.

## How it answers the concern
- **Main components:** Registration form (desktop), Authentication REST API, Library facade, User manager, User factories, User registry, Persistence manager, Account database (MySQL), grouped by layer.
- **Responsibilities:** one line each in `inventory.json` (e.g. User manager validates role/name/email/password/identifier, rejects duplicate email or identifier, creates and saves the user).
- **Integration points:** the interfaces drawn: sign-up screen and register endpoint (entry points), Library facade API, Register operation, User factory, User registry API, Persistence API, JPA/JDBC to the database. Suggested tests: each entry point through to the database; duplicate email and duplicate identifier (registry reads); save failure (persistence).

## Files
`view.puml`, `view.png`, `inventory.json` (evidence as file:line).

## Omitted
User DTO/entities, login flow, UI styling helpers; direct dependency edges are drawn as interface pairs.

## Assumptions
Database is MySQL per `persistence.xml`; the REST API and desktop form are alternative entry points (separate main classes). Run-time order (sequence) would need a sequence view.

## Checks
puml-check: no warnings (one "busy" advisory earlier). check_inventory.py --level balanced --graph: 0 issues (7 notes). check_view.py: clean.
