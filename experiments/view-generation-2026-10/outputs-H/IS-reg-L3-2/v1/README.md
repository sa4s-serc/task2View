# UML sequence diagram: registration with invalid or already existing data

**Takeaway:** every registration check (format, email, identifier) runs inside User manager, which reads the User registry through the Persistence manager. Any failure travels back as an exception through Library facade and Registration API, and the REST error handler turns it into HTTP 400. A failed save is the exception: it is not mapped.

**Stakeholder:** integration tester. **Detail level:** balanced (given). Seven lifelines; the Swing form and the database are not lifelines. A different level would add the form, MySQL and the account entities (more) or only the REST path (less).

Lifeline names match view `IS-reg-L3` (component).

## How the concern is answered
- *Who handles the request:* Registration API (`POST /api/auth/register`), then Library facade, then User manager. A note says the Swing form uses the same facade call.
- *Validates personal data and role:* the first `alt` (User manager checks role, names, password, email and identifier format). On failure nothing is queried or saved.
- *Role-specific data:* the identifier format and uniqueness checks differ for student ID and librarian code. User factories build the Student or Librarian after all checks pass.
- *Validity and uniqueness:* the email check and the identifier check go User manager, User registry, Persistence manager.
- *Persistence:* "register user", then User registry, then Persistence manager (transactional save).
- *Invalid or existing data:* each failing branch (invalid format, email taken, identifier used) throws IllegalArgumentException. The first branch shows the full return path to the 400 response; the others say "same path to 400".
- *Integration points to cover:* Registration API to Library facade; Library facade to User manager; User manager to User registry; User registry to Persistence manager; the error handler; and the save-failure branch, whose RuntimeException is not mapped (outcome unconfirmed).

Inventory: `inventory.json`.

## Omitted on purpose
Registration form (noted only), MySQL database, account entities, UserDTO, login. Repeated exception propagation is collapsed after the first branch.

## Assumptions
- The Registration API to REST error handler message reflects Spring's annotation wiring (`@RestControllerAdvice`), not a code dependency, so check_inventory reports it as 1 issue.
- Behaviour on the unmapped RuntimeException (server error) is not in the code (unconfirmed).

## Check results
- check_inventory.py (balanced, with graph): 1 issue, the framework-wired error handler relation above; nothing else.
- check_view.py: clean. check_consistency.py with IS-reg-L3: consistent.
- puml-check: 2 warnings, where the labels of nested `alt` frames ("ID used", "failed") sit across a lifeline. The text is still readable in view.png. Revisions moved User factories to the right, which cut lifeline crossings from 7 to 1, and shortened labels.
