# Registration: UML sequence view (balanced), revision 1

**Takeaway:** a REST registration request goes controller, facade, UserManager, then registry/persistence and MySQL; UserManager validates first, then checks email and identifier uniqueness, then does one transactional INSERT. Failures are mapped to HTTP 400 by RestExceptionHandler, except a save failure, which becomes Spring's default 500.

Stakeholder: integration tester. Detail level: balanced (given). Files: `view.puml`, `view.png`, `inventory.json`; the previous version is in `v1/`.

## How the concern is answered
- **Components and responsibilities:** 7 lifelines: REST client (actor), AuthenticationController (REST entry), RestExceptionHandler (error mapping), LibraryFacade (application entry), UserManager (validation, uniqueness, user creation via UserFactory), UserRegistry + PersistenceManager (user lookups and transactional save), MySQL reservationsdb. Responsibilities are in `inventory.json`; the diagram shows them through the order and labels of messages.
- **Interaction:** success path 1-4, 7-10, 12-15, 17-24. Control flow now follows `UserManager.register`: validation (break, msgs 5-6) before any lookup; email lookup (7-10) then a break; identifier lookup by role (12-15) then a break; create and save; save-failure branch (25-26).
- **Integration points:** marked on the messages and listed in the legend: IP1 REST boundary, IP2 controller to application, IP3 registry lookups, IP4 database SELECT/INSERT, IP5 error mapping (400 via handler, default 500 for save failure).

## Changes after the review (`critique-1.json`)
- Added RestExceptionHandler (it exists: `RestExceptionHandler.java:15-22`) and the 400 `{"error": message}` response; removed the wrong "no exception handler" assumption.
- Moved validation before the lookups; split the combined lookup into email and identifier lookups with separate duplicate breaks; added the save-failure branch.
- Client is now an actor for the REST caller; the Swing form is a note, since it calls `LibraryFacade.register` directly (`Registration.java:134`).
- Integration points marked on the diagram.
- To stay at 7 lifelines, UserRegistry and PersistenceManager are one lifeline (plain delegation, `UserRegistry.java:27-38`). Message count (26 including returns) exceeds the balanced guideline of 12; the extra messages are the break branches and returns, which the reviewer asked for.
- Not taken: a separate Swing lifeline (would exceed 7 lifelines).

## Omitted
UserFactory classes (self-message), UserDTO, JpaUtil, entities, login flow, the Swing path as a lifeline.

## Assumptions
- The exceptions travel from UserManager through the facade and controller to Spring's advice; drawn as direct messages from UserManager to RestExceptionHandler / controller to avoid four extra returns. `check_inventory.py` flags `um->eh` and `um->ctl` because they are runtime exception propagation, not static dependencies; kept deliberately.
- Save failure: `PersistenceManager.save` returns false, `UserManager` throws `RuntimeException` (`UserManager.java:93-95`), which the handler does not cover, so Spring's default 500 (framework behaviour, not verified by running).

## Check result
- puml-check: renders; 5 warnings (messages and break labels crossing one lifeline), because the handler sits between controller and facade; reordering did not reduce them, so layout was kept.
- check_inventory.py --level balanced --graph: 2 issues, the two exception relations above (no static dependency); client and MySQL have no members.
