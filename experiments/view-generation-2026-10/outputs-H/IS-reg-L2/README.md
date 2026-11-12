# Component view: user registration (balanced)

**Takeaway:** a new user registers through the desktop form, or an HTTP client calls the REST endpoint; both reach the Library facade, the User manager validates and checks duplicates through the User registry, and the Persistence manager saves to the MySQL account database.

Stakeholder: integration tester. Detail level: balanced (given). Previous version kept in `v1/`.

## How it answers the concern
- **Components:** Registration form (desktop), Authentication REST API, Library facade, User manager, User registry, Persistence manager, Account database (MySQL), grouped by layer.
- **Responsibilities:** now written inside each component box in the view (form blank-field check; User manager validation rules, duplicate checks, building the Student or Librarian, failure on save error; registry lookups; persistence transaction and rollback), and in `inventory.json`.
- **Integration points:** the interfaces drawn, each now listing its operations: sign-up screen, `POST /api/auth/register`, `register(role, name, surname, email, password, identifier) : UserDTO` on the facade and manager, the four registry operations, `save` / `findFirstByFields`, and JDBC (MySQL). A note lists the paths to test: invalid input (HTTP 400 on REST), duplicate email / student number / librarian code, and save failure (`save` returns false, the manager throws RuntimeException, not mapped to 400).

## Changes after review (critique-1)
- Responsibilities and operation names added to the view.
- Error contract added (RestExceptionHandler maps IllegalArgumentException to HTTP 400; it is part of the REST API component).
- User factories folded into User manager: they are created with `new` inside `register()`, so not a replaceable seam.
- REST endpoint now used by an external "HTTP client", not the person at the form.
- Database interface relabelled JDBC (MySQL); JPA is provided in-process by Hibernate.
- Note no longer attached to User manager only; it is a free note linked to Persistence manager, where the failure seam originates.

## Omitted
User DTO/entities, login flow, UI styling helpers, factories as a separate component, direct dependency edges (drawn as interface pairs).

## Assumptions
Database is MySQL per `persistence.xml`. RestExceptionHandler also maps IllegalStateException (HTTP 400) and SecurityException (401); only the registration-relevant case is shown. Call order would need a sequence view.

## Checks
puml-check: no warnings. check_inventory.py --level balanced --graph: 0 issues (notes only for interface-mediated dependencies and external elements). check_view.py: clean.
