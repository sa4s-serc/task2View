# View: User Registration - Dynamic View (UML sequence diagram)

**Stakeholder:** integration tester. **Concern:** control flow of user registration: which components take part and how they interact. **Aspect/viewpoint:** behavioural / dynamic.

`view.puml` shows the end-to-end flow of registering a Student or a Librarian, derived from the code in `JavaProject/src/main`.

## How it addresses the concern
- **Components involved:** the participants are the registration client (Swing `Registration`, or web `registration.html`/`app.js`), `AuthenticationController` (`POST /api/auth/register`), `RestExceptionHandler`, `LibraryFacade`, `UserManager`, `StudentFactory`/`LibrarianFactory`, `UserRegistry`, `PersistenceManager` and the database. Stereotypes give each one's layer.
- **How they interact:** messages follow the call chain: UI -> (controller, web only) -> `LibraryFacade.register` -> `UserManager.register` -> validation -> uniqueness checks via `UserRegistry`/`PersistenceManager` -> factory creation -> `registerUser`/`save` -> `UserDTO` returned. The Swing client calls the facade directly; the web client goes through REST.
- **Control flow / branches for test design:** `alt`/`opt` fragments cover the Student vs Librarian validation, invalid data or duplicate email/identifier (`IllegalArgumentException`, mapped to HTTP 400 by `RestExceptionHandler`), persistence failure (`save` returns false, `RuntimeException`), and success (DTO returned, user told to sign in and sent to login).

Scope note: login and other use cases are out of scope. The Swing client's exception path is shown only as propagation to the UI error dialog.
