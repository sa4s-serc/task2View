# User registration: components and dependencies (UML component diagram), revision 2

**Takeaway:** a registration request enters through the Registration form or Registration API, reaches the User manager through the Library facade, which validates the data and checks duplicates through the User registry, creates the role-specific user via the User factories and saves it through the User registry and Persistence manager.

Stakeholder: integration tester. Detail level: balanced (given). The first version is kept in `v1/`.

## How the view answers the concern
- **Handles the request:** Registration form (Swing; also does the blank-field check before submitting) and Registration API (provides `POST /api/auth/register`); both require the facade's `register` interface.
- **Validates personal data and role:** User manager (role, names, email, password, student ID format).
- **Role-specific data:** User factories (provide `createUser`) create a Student with its student ID or a Librarian with its internal code; User accounts hold them.
- **Validity and uniqueness:** User manager checks format and rejects duplicate email or identifier through the User registry's find/save interface; User accounts carry unique columns as a database-level backstop.
- **Persistence:** User registry to Persistence manager (JPA save with rollback, returns false on failure) to the external MySQL database.
- **Invalid or existing data:** the note shows both paths. Validation and duplicate errors are an IllegalArgumentException: HTTP 400 through the REST error handler, an error dialog on the form. A failed save is a RuntimeException from the User manager: not mapped by the handler, so HTTP 500 on the API.
- **Integration points to cover:** the form/API to facade interface; facade to User manager; User manager to `createUser`; User manager to the registry interface (duplicate checks, save); registry to persistence and database; error handler to API responses.

Details: `inventory.json`. check_inventory.py (`--level balanced --graph`): 0 issues, only notes. check_view.py: clean. puml-check: 6 warnings remain (labels or edges touching boxes and package titles); one further layout attempt did not reduce them and was reverted.

## Changes from the reviewer's critique
Added the REST error handler, the error paths and the form's blank-field check; put responsibilities in the component text; switched to dependencies with «use» and provided interfaces; merged the two User manager to User registry arrows into one use of the registry interface; replaced the muted database with a node marked external.

## Where I kept my version
The reviewer suggested a dependency from the error handler to the Registration API. The code has none (Spring applies the handler by annotation, `RestExceptionHandler.java:15`), so it appears as a component and in the note only. The layer packages were kept: they group nine components and the checker expects grouping.

## Omitted on purpose
Login and authentication, UserDTO, UI style helpers, the User manager to account-entity mapping, JPA configuration detail.

## Assumptions
The form and the REST API are alternative entry points calling the same facade. Nothing unconfirmed.
