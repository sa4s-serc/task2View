# Registration sequence view (balanced), revision 1

**Takeaway:** a registration request travels REST controller → LibraryFacade → UserManager, which validates, checks uniqueness via UserRegistry/PersistenceManager, builds the user with a role-based factory and saves it; the outcome is 200 UserDTO, 400 (bad format or duplicate) or an unmapped RuntimeException (default 500) when the save fails.

Stakeholder: integration tester. Detail level: balanced (7 lifelines, 12 messages), as given. Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation), `v1/` (first version), `critique-1.json`.

## Concern coverage
- **Components and responsibilities:** each lifeline header now carries a one-line responsibility (e.g. UserManager: validate, check unique, choose factory, persist; LibraryFacade: pass-through entry, also used by Swing). Details are in `inventory.json`.
- **Interaction:** messages 01-12 in code order. Validation comes first (`[bad format]`), then the uniqueness lookups, then a nested `[duplicate]` / `[new]` alt, then `[save ok]` / `[save returned false]`. Exceptions are drawn as dashed replies labelled with the exception type.
- **Integration points:** marked IP1-IP4 on the messages and listed in the legend: IP1 HTTP form parameters (Swing bypasses it), IP2 validation and exception-to-HTTP mapping, IP3 role-based factory choice, IP4 JPA lookups and save transaction with rollback.

## Changes after the review
- Uniqueness lookups moved out of the guard that assumed their result; alt is now nested in code order.
- Added the save-failure outcome (`UserManager.java:93-94`, unmapped, Spring default 500).
- RestExceptionHandler shown by merging it into the controller lifeline (same boundary layer), which keeps 7 lifelines (the balanced budget). A separate lifeline would make 8.
- Role guard on createUser; responsibilities in headers; integration points marked in the diagram.
- Kept: the Swing entry point stays a legend remark, not a lifeline (reviewer accepted it).

## Where I kept my version
- The factory stays a lifeline with a role guard on the message instead of a «create» message: the factories are stateless, selected by role, and one lifeline stands for both.
- Exception replies go straight from UserManager to the controller lifeline ("via facade" in the label), not drawn hop by hop, to stay within 12 messages.
- Format validation is not a separate self-message; it is the `[bad format]` guard and IP2 (the separate email/identifier lookups and per-field rules stay collapsed, as the reviewer advised).

## Omitted on purpose
Swing form lifeline, UserDTO and entity classes, JpaUtil, login, per-field validation rules, internal success replies.

## Assumptions / unconfirmed
- "Default 500" for the unmapped RuntimeException is Spring's standard behaviour; it was not run.
- Unknown-role rejection happens in validation (UserManager.java:54), so the factory's "otherwise" branch only sees Librarian.

## Check results
puml-check: OK (info only: one alt label on the first lifeline, 5 of 12 messages span one lifeline). check_inventory.py --level balanced: 0 issues, 7 elements, 10 relations (self-messages are not parsed by the checker; none are drawn now).
