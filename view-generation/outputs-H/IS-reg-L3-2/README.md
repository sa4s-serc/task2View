# UML sequence diagram: registration with invalid or already existing data

**Takeaway:** every registration check (format, email, identifier) runs in User manager, which queries the User registry through the Persistence manager. A rejection goes back as `IllegalArgumentException` through Library facade and Registration API, and the REST error handler turns it into HTTP 400. A duplicate that passes the lookups is stopped by the unique database columns. The save then fails and the client gets a default 500, because the handler does not map that exception.

**Stakeholder:** integration tester. **Detail level:** balanced (given), seven lifelines. A different level would add the Swing form, MySQL and the account entities (more) or only the REST path (less). Lifeline names match view `IS-reg-L3`.

## How the concern is answered
- *Who handles the request:* Registration API, then Library facade, then User manager. A note says the Swing form calls the facade the same way.
- *Validates personal data and role:* the first `alt`. The check covers role (Student or Librarian only), names, password, email and identifier characters. Only students need the pattern letter + 8 digits.
- *Role-specific data:* the identifier lookup is role-scoped (students by student number, librarians by code). A student number equal to a librarian code is therefore not rejected, which is a test case. User factories create the Student or Librarian and return it.
- *Validity and uniqueness:* the email lookup and the identifier lookup go User manager, User registry, Persistence manager.
- *Persistence:* transactional save. The guard "unique column violated" is the second line of defence, for example for concurrent duplicate registrations. The response is 500 (RuntimeException not mapped by the handler).
- *Invalid or existing data:* three rejection operands (format invalid, email taken, ID used) throw `IllegalArgumentException`. The first draws the full path to 400, and the others use a `ref` to it.
- *Integration points:* API to facade, facade to manager, manager to registry, registry to persistence, manager to factories, and the exception-to-response mapping.

Inventory: `inventory.json`. check_inventory.py (balanced, with graph): 0 issues. check_view.py: clean. check_consistency.py with `IS-reg-L3`: consistent. puml-check: 3 warnings, where nested `alt` labels are crossed by a lifeline. The labels are still readable in `view.png`.

## Revision (v1 is kept in `v1/`)
Addressed from critique-1: the save-failure guard and its 500 outcome (confirmed: unique columns at User.java:21, Student.java:19 and Librarian.java:13, and the handler maps only the three exception types); the error handler is entered by a found message from Spring instead of a reply from the controller; "(same path to 400)" labels replaced by `ref` frames; activation bars removed so no lifeline looks stuck active after an exception; role-scoped identifier lookup and role-specific format checks made explicit; the Swing note moved to Library facade.

Kept as is: the lifeline stays named "User factories" (not "factory : UserFactory"). It stands for both factories, and the component view `IS-reg-L3` uses that name for the same code. A note says StudentFactory or LibrarianFactory is chosen by role.

## Omitted on purpose
Registration form (note only), MySQL, account entities, UserDTO, login. After the first rejection, the exception propagation is collapsed into `ref` frames.

## Assumptions
- The 500 is Spring's default behaviour for an unmapped RuntimeException. The code shows only that no handler maps it.
- A unique-column violation is shown as the trigger for the failed save. Other persistence errors would take the same branch.
