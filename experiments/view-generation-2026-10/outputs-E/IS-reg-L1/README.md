# User registration: UML sequence diagram (balanced)

**Takeaway:** a registration request goes form → AuthenticationController → LibraryFacade → UserManager, which validates the input and checks email and identifier uniqueness through UserRegistry / PersistenceManager / MySQL before inserting the new Student or Librarian; any rejection comes back to the caller as HTTP 400.

**Stakeholder:** integration tester (end-to-end test of registration). **Detail level:** balanced, as given in the stakeholder perspective: 7 lifelines, 12 messages, one `alt` for the accepted/rejected paths. Wording uses class names and protocol (POST, JPA, SQL) because the reader is an engineer.

Files: `view.puml`, `view.png`, `inventory.json` (elements and relations with `file:line` evidence).

## How the view addresses the concern (control_flow)
- **System components involved:** the seven lifelines: registration form, `AuthenticationController`, `LibraryFacade`, `UserManager`, `UserRegistry`, `PersistenceManager` and the MySQL database `reservationsdb`.
- **How they interact:** numbered messages 1–12 show the call order. The `alt` frame separates the accepted path (INSERT, then `200 UserDTO`) from the rejected path (validation failure or duplicate email/identifier, then `400 {error}` via `RestExceptionHandler`). The same flow serves the student and librarian roles; only the validated identifier and the created entity differ (note on the `registerUser` message).

## Omitted on purpose
- The Swing `Registration` form: an alternative client that calls `LibraryFacade` directly (`Registration.java:134`); mentioned in a note only.
- Factories (`StudentFactory`/`LibrarianFactory`), `UserDTO` mapping and `JpaUtil`: internal helpers folded into `UserManager` and `PersistenceManager`.
- Login and everything after registration.
- A finer level would add the individual validation rules and the two separate lookups; a different view (login sequence) would cover authentication.

## Assumptions / unconfirmed
- The web form's HTTP request and the JSON error body are taken from `registration.html`, `app.js` and `RestExceptionHandler`; no running server was exercised.
- A failed save throws `RuntimeException`, which `RestExceptionHandler` does not map; it is shown in a note, not as a message.
- The two uniqueness lookups (email, then identifier) are collapsed into messages 5–7.

## Check results
- `puml-check`: OK, 0 warnings (one advisory info: the `[rejected]` label starts on the first lifeline). Rendered `view.png` inspected.
- `check_inventory.py --level balanced`: exit 0 (the `UserManager` self-message is described in its responsibility because the checker does not detect self-messages).
- No revision from an external reviewer has been applied.
