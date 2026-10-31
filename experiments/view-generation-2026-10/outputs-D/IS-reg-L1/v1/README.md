# UML sequence diagram: user registration

**Takeaway:** a registration request goes form -> REST controller -> facade -> `UserManager` (validate, uniqueness check, create, persist) -> `UserRegistry` -> database, and comes back as a `UserDTO` (success) or an error message (failure).

**Stakeholder:** integration tester, testing registration end to end. **Level:** detailed (7 lifelines, 20 messages). It exceeds the "balanced" budget of 12 messages on purpose: an end-to-end test needs every layer boundary and both outcomes. Wording is technical (endpoint, class and method names).

Files: `view.puml`, `view.png`, `inventory.json` (evidence for every element and relation).

## How it addresses the concern
- **Components involved:** the seven lifelines are the tester, registration form (`registration.html` + `app.js`), `AuthenticationController`, `LibraryFacade`, `UserManager`, `UserRegistry` (with `PersistenceManager`) and the JPA database.
- **How they interact:** messages 1-4 carry the call down (`POST /api/auth/register`, then `register(...)` twice). Messages 5-8 are format validation and the email/identifier duplicate lookup. Messages 9-12 create a Student or Librarian through its factory and persist it. Messages 13-16 return `UserDTO` and the success dialog. The `alt` branch (17-20) shows an `IllegalArgumentException` mapped to `400 {"error": ...}` by `RestExceptionHandler` and displayed by the form.

## Omitted on purpose
The Swing `Registration` form is an alternative entry point that calls `LibraryFacade` directly (`Registration.java:134`), so it appears only as a note. The factories, DTO and entity classes are collapsed into `UserManager`. Other `LibraryFacade` operations (login and so on) are left out.

## Assumptions
- Tests (`RegistrationTest`) enter at `LibraryFacade.register`, not through REST. The diagram shows the REST path, which covers every layer above the facade.
- Validation and duplicate checks all throw `IllegalArgumentException`. A save failure throws `RuntimeException` (`UserManager.java:93-95`) and is not drawn.
- The `alt` is drawn after the checks for readability. Validation failures (messages 5-6) actually occur before it.

## Check results
- `puml-check`: one `aspect` warning (ratio 1.31 vs 1.78, a tall sequence diagram), one advisory `info` about a group label, and no overlaps or lifeline crossings. One revision routed the error path through the facade to remove a lifeline crossing.
- `check_inventory.py`: the final run exited 0 (printed output not captured).
