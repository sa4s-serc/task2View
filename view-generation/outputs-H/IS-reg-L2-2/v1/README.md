# View IS-reg-L2-2: account creation interaction flow (UML sequence diagram)

**Takeaway:** a registration enters through the desktop Registration form or the Authentication REST API, passes
through the Library facade to the User manager, which checks for duplicates and saves through the User registry and
Persistence manager into the Account database; failures return as errors to the caller.

Stakeholder: integration tester. Detail level: **balanced** (the parts involved in registration, with the calls
between them). Files: `view.puml`, `view.png`, `inventory.json`. Element names match view IS-reg-L2 (component).

## How the view answers the concern
- **How components interact when a new user creates an account:** messages 01-12 are the entry, validation and
  duplicate check; 16-21 are creation and save; the `alt` blocks show the duplicate error (13-15), the save failure
  (22-23) and success (24-26).
- Integration points to exercise (each message between two lifelines): form/REST to facade (03, 05), facade to
  User manager (06), User manager to User registry (08, 17), registry to Persistence manager (09, 18),
  Persistence manager to database (10, 19), and the error mapping to the form and to HTTP 400.

## Omitted on purpose
Users and HTTP client (drawn as found messages, to keep 7 lifelines), UserDTO and entity classes, user factories,
field-level validation rules, JpaUtil, login after success. The repeated duplicate queries (email, then identifier)
are collapsed into one message "2 calls".

## Assumptions
- Where the form and the REST entry share a reply, the reply goes to whichever entry was used.
- Account database has no code members (external), so its relation is not graph-checked.

## Check results
puml-check: OK (info only: three REST-to-facade messages span the form lifeline). check_inventory.py
`--level balanced --graph`: 0 issues. check_view.py: clean. check_consistency.py with IS-reg-L2: consistent.
