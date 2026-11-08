# UML sequence diagram: user registration

**Takeaway:** UserManager validates and uniqueness-checks a registration before UserFactory builds the Student or Librarian that UserRegistry saves via PersistenceManager; each failure throws and nothing is saved.
**Stakeholder:** integration tester. **Detail level:** balanced (the components of this one flow with their calls). Main flow with nested `alt` for the four failure branches.

## Concern coverage
- Request handling: Registration boundary (Swing `Registration` or `POST /api/auth/register`) and LibraryFacade (msgs 1-3).
- Personal data and role validation: UserManager (msg 4, first `alt`: invalid field throws IllegalArgumentException, no DB access).
- Role-specific data: UserManager applies student ID (letter + 8 digits) or librarian code (alphanumeric) rules (note); UserFactory builds the right entity (msgs 18-19).
- Validity and uniqueness: UserManager queries UserRegistry, then PersistenceManager and the database, for the email (6-10) and the identifier (12-16).
- Persistence: registerUser, save, INSERT (20-24); a failed save throws RuntimeException.
- Invalid or existing data: the four nested `alt` branches (invalid field, email taken, identifier taken, save failed).
- Integration points to cover: boundary to facade, facade to UserManager, UserManager to UserRegistry, UserRegistry to PersistenceManager, and PersistenceManager to database. Exceptions propagate unchanged to the boundary, which shows the message.

Evidence is in `inventory.json`. A detailed level would add each validation rule's regex and message.

## Omitted
UserDTO mapping, login/profile flows, singleton wiring, JpaUtil.

## Assumptions
The Swing form and REST controller are shown as one lifeline because both call `LibraryFacade.register` identically. Uniqueness is also enforced by unique DB columns (`User.java:21`), but this view does not show that failure path.

## Check results
puml-check: OK (only 2 info lines about lifeline spans). check_inventory.py: check_inventory.py: exit 0 (clean; user and db have no members by design).
