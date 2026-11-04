# Registration: UML sequence view (balanced)

**Takeaway:** a registration request passes through five layers (controller, facade, UserManager, UserRegistry, PersistenceManager) to MySQL; UserManager validates and checks uniqueness before the single INSERT.

Stakeholder: integration tester. Detail level: balanced (7 lifelines; 14 calls plus returns, a few over the 12-message budget because the call chain reaches the database and the error return path is drawn). Files: `view.puml`, `view.png`, `inventory.json`.

## How the concern is answered
- **Components and responsibilities:** the seven lifelines, each named after its code element (see `inventory.json` for responsibilities and evidence). Client = REST caller or Swing `Registration` form; AuthenticationController = REST entry; LibraryFacade = application entry; UserManager = validation, uniqueness, user creation (UserFactory folded in); UserRegistry = domain access to users; PersistenceManager = JPA transactions; MySQL = store.
- **Interaction:** messages 1-19 show the success flow; the `alt` branch shows the validation/duplicate failure, which stops before any write (messages 20-22).
- **Integration points to test:** (1) REST boundary, POST /api/auth/register to controller (1); (2) controller to facade to UserManager (2-3); (3) UserManager to UserRegistry lookups for duplicate email and identifier (5); (4) UserRegistry to PersistenceManager to MySQL: SELECT (6-7) and INSERT in a transaction (13-14); (5) error propagation back to the caller (20-22); (6) Swing form calling the facade directly (note).

## Omitted
UserFactory/StudentFactory/LibrarianFactory (self-message), UserDTO, JpaUtil, entity classes, login flow. The Swing-to-facade call (`Registration.java:134`) is a note rather than a lifeline.

## Assumptions
- Exceptions are drawn as returns up the chain; the REST layer has no exception handler in the code shown, so the HTTP error status is unknown (the "error response" label is generic).
- A save failure (`registerUser` returns false) throws RuntimeException; it is not drawn separately.
- A different level (detailed) would add the individual field validation rules and the UserFactory classes.

## Checks
- puml-check: renders, 0 warnings (1 info about a group label).
- check_inventory.py --level balanced --graph .claude/repo-graph.json: 0 issues (note: client and db have no code members).
