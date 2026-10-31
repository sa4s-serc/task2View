# Registration sequence view (balanced)

**Takeaway:** a registration request travels REST controller → LibraryFacade → UserManager, which validates, checks uniqueness via UserRegistry, builds the user with a factory and persists it through PersistenceManager to MySQL; the controller answers 200 with a UserDTO or 400 with an error.

Stakeholder: integration tester. Detail level: balanced (7 lifelines, 11 messages), as given. Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation).

## Concern coverage
- **Main components and responsibilities:** the seven lifelines, named after the code classes, with a role hint in each header; responsibilities are in `inventory.json`.
- **Interaction on account creation:** messages 01–11 in order. One `alt` separates success (05–10) from invalid or duplicate input (11). Message 04 is UserManager's own format validation (a self-message; `check_inventory.py` does not parse it, so it is left out of the inventory relations).
- **Integration points to exercise:** (1) form → controller (HTTP form parameters, 400 mapping); (2) controller → facade → manager (call chain; the Swing form enters at the facade, shown in a note); (3) manager → factory (Student vs Librarian); (4) UserRegistry → PersistenceManager → MySQL (uniqueness lookups and the save transaction).

## Omitted on purpose
Swing form as a lifeline (note only), UserDTO and entity classes, JpaUtil, login, replies between internal layers (only the final HTTP replies are drawn), per-field validation rules.

## Assumptions / unconfirmed
- A failed save throws RuntimeException, which RestExceptionHandler does not map (only IllegalArgumentException, IllegalStateException and SecurityException): the HTTP result is unconfirmed.
- Messages 05–09 are drawn inside the success branch of the `alt`. In the code a duplicate is detected after message 05/06 and aborts before createUser. Branches are collapsed into one error reply.
- A different level would add per-field validation rules and the duplicate vs save-failure branches (detailed).

## Check results
puml-check: OK (ratio 1.78, only info lines: label on first lifeline; 2 messages span one lifeline). check_inventory.py --level balanced: clean after removing the self-message relation. First draft had 16 messages (over budget) and was cut to 11 by dropping return messages.
