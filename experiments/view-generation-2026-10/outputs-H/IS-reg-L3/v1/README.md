# User registration: components and dependencies (UML component diagram)

**Takeaway:** a registration request enters through the Registration form or Registration API, passes the Library facade to the User manager, which validates the data and checks duplicates against the User registry, builds the role-specific user through the User factories and saves it via the User registry and Persistence manager.

Stakeholder: integration tester. Detail level: balanced (given), so the components involved in registration with their dependencies, not classes.

## How the view answers the concern
- **Handles the request:** Registration form (Swing) and Registration API (`POST /api/auth/register`), both forwarding to the Library facade.
- **Validates personal data and role:** User manager (role, names, email, password, identifier format).
- **Role-specific data:** User factories build a Student (student ID) or Librarian (internal code); User accounts hold them. User manager checks the identifier format per role.
- **Validity and uniqueness:** format checks in User manager; email and identifier duplicate lookups through User registry (unique columns also in User accounts).
- **Persistence:** User registry to Persistence manager to the Reservations database; a failed save returns false and User manager raises an error.
- **Invalid or existing data:** User manager rejects before the factory and save steps (the note on the diagram); the error returns to the form or API as an exception. Integration points to test: form/API to facade, facade to User manager, User manager to User registry (duplicate checks, save), User manager to factories, registry to persistence and database.
- **Dependencies:** all arrows; the sequence of calls and error ordering would need a sequence view.

Details: `inventory.json` (check_inventory.py with `--level balanced --graph`: only the notes remain, no errors). check_view.py: clean. puml-check: 4 warnings remain (edges crossing package titles, one label near a border); rendered to `view.png`.

## Omitted on purpose
Login/authentication, the data object UserDTO, UI style helpers, the User manager to Student/Librarian dependency (only maps the response), JPA configuration detail.

## Assumptions
The Swing form and the REST API are alternative entry points; both call the same facade. Nothing unconfirmed.
