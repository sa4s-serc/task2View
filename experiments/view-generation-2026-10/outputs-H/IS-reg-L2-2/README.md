# View IS-reg-L2-2: account creation interaction flow (UML sequence diagram)

**Takeaway:** a registration enters through the desktop Registration form or the Authentication REST API, passes
through the Library facade to the User manager, which checks for duplicates and saves through the User registry and
Persistence manager into the Account database; failures return as errors to the caller.

Stakeholder: integration tester. Detail level: **balanced** (the parts involved in registration, with the calls
between them). Files: `view.puml`, `view.png`, `inventory.json`. Element names match view IS-reg-L2 (component).

## How the view answers the concern
- **How components interact when a new user creates an account:** messages 01-07 are entry, blank-field check and
  validation; 09-13 are the duplicate lookups (a loop of two); 15-20 are creation and save; 21-22 are the save
  outcome. The outer `alt` blocks give each outcome: invalid input (08), duplicate email or identifier (14), save
  failure (21) and success (22).
- **Callers are separated:** the last `alt desktop / REST` shows who receives the result. The form shows its own
  dialog (24, Registration.java:134-142); the REST API answers the HTTP client (26) with 200, 400 or 500.
- **Integration points to exercise** (each message between two lifelines): form or REST to facade (03, 05), facade
  to User manager (06), User manager to User registry (09, 16), registry to Persistence manager (10, 17),
  Persistence manager to database (11, 18), and the result returned to each caller (23, 25-26).

## Omitted on purpose
Users and HTTP client (drawn as found messages, to keep 7 lifelines), UserDTO and entity classes, user factories,
field-level validation rules, JpaUtil, login after success. The repeated duplicate queries (email, then identifier)
are collapsed into one message "2 calls".

## Assumptions
- Account database has no code members (external), so its relation is not graph-checked.

## Revision 1 (reviewer critique; previous version in `v1/`)
Accepted, each checked against the code: added the invalid-input outcome (UserManager.validate throws
IllegalArgumentException); added the REST result of a save failure: RuntimeException is not handled by
RestExceptionHandler (it handles IllegalArgumentException, IllegalStateException, SecurityException), so a
note states it ends as HTTP 500; the facade now only propagates (LibraryFacade.java:37-39), the form shows its own
dialog and the REST API answers the HTTP client, in separate `desktop` / `REST` operands; the duplicate check is a
loop of two lookups, the identifier lookup chosen by role. Nothing contradicted the code, so no point was rejected.
Limits: the two duplicate messages ("Email is already associated...", "Identifier is already in use.") are one
branch, not two; the 500 is derived from the handler's exception list, not from a run (unconfirmed).

## Check results
puml-check: OK (info only: two REST-to-facade messages span the form lifeline). check_inventory.py
`--level balanced --graph`: 0 issues. check_view.py: clean. check_consistency.py with IS-reg-L2: consistent.
