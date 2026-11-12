# User registration: components involved (UML component diagram)

**Takeaway:** a registration, from the Swing form or the REST endpoint, passes through the Library facade to the User manager, which uses the User factories and the User registry, and the registry stores the account through the Persistence manager in the MySQL database.

Stakeholder: integration tester. Detail level: balanced (the parts involved in registration with the calls between them; the given level, not changed).

## How the view answers the concern
- *Which system components are involved in user registration?* All of them are in `view.puml`: two entry points (Registration form, Authentication REST API), Library facade, User manager, User factories (Student or Librarian), User registry, Persistence manager and the MySQL database. Each arrow is a call a test can exercise; the two entry points are the places to start an integration test.

Evidence for each element and relation is in `inventory.json`.

## Omitted on purpose
UserDTO and entity classes, Swing helpers (WizardStyle, WizardState), the Login screen that follows registration, JpaUtil. The Student, Librarian and User entities are folded into User registry.

## Assumptions
- The calling order inside User manager (validation, duplicate check, factory, save) is in the code but a component diagram does not show order; a sequence view would.
- The REST endpoint's caller is assumed to be a student or librarian client; no such client is in the repository.

## Check results
- puml-check: OK (no warnings; diagram is wide, 1845x362, because left-to-right avoided edges crossing layer titles in top-to-bottom).
- check_inventory.py --level balanced --graph: 0 issues (1 note: users, database and layer packages have no members).
- check_view.py: clean.
