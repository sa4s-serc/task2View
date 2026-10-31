# UML sequence diagram: user registration

**Takeaway:** a registration request goes form -> REST controller -> facade -> `UserManager` (validate, email check, identifier check, create, persist) -> `UserRegistry` -> database. Each check exits early with an error, and a failed save raises an unmapped `RuntimeException`.

**Stakeholder:** integration tester, testing registration end to end. **Level:** detailed (7 lifelines, 22 messages, within the 25-message budget). Wording is technical (endpoint, class and method names).

Files: `view.puml`, `view.png`, `inventory.json` (evidence for every element and relation). The previous version is in `v1/`.

## How it addresses the concern
- **Components involved:** the lifelines are the user, registration form (`registration.html` + `app.js`), `AuthenticationController`, `LibraryFacade`, `UserManager`, `UserRegistry` (with `PersistenceManager`) and the JPA database.
- **How they interact:**
  - Messages 1-4 carry the call down.
  - Message 5 validates the fields, by role (`validateStudent` or `validateLibrarian`). A `break [invalid input]` returns 400 (06).
  - Messages 7-10 look up the email, and a `break [email used]` returns 400 (11).
  - Messages 12-13 look up the identifier by role (`findStudentByStudentNumber` or `findLibrarianByCode`), and a `break [id used]` returns 400 (14).
  - Messages 15-19 create the user through its factory and persist it.
  - An `alt` then shows the outcome: success returns `UserDTO` and the "Registration complete" dialog (20-21). A failed save returns an unhandled `RuntimeException`, not a 400 (22).
- **Test entry point:** a note says `RegistrationTest` and the Swing client enter at `LibraryFacade.register`, skipping the form and the controller.

## Changes after review (critique-1)
- The single `alt` after the checks is replaced by one `break` fragment per early exit. The unconditional "not found" reply is gone.
- The email and identifier lookups are separate, each with its own error message. The role branch is shown in the message text.
- The save-failure path is added.
- Exceptions are no longer drawn as dashed "propagated" replies. Each exit is a labelled reply carrying the HTTP result.
- Activation bars are removed, so none run past the end. The actor is renamed "User (Student / Librarian)". Database replies are added.

**Kept as it was, with reasons:**
- The reviewer asked for reply hops through the facade and controller. They only pass the result along (`AuthenticationController.java:29-30`, `LibraryFacade.java:39`), so I collapsed them into one note. This keeps the view within 25 messages. It also makes five replies span two lifelines, which `puml-check` reports as an info line.
- Only the first lookup shows its database round trip. The identifier lookup reply says "SELECT as above", which is a shortcut for the budget (both go through `findFirstByFields`).

## Omitted on purpose
`RestExceptionHandler` as a lifeline (mentioned in a note), the factories, DTO and entity classes (collapsed into `UserManager`), and other `LibraryFacade` operations.

## Assumptions
- A `RuntimeException` is not handled by `RestExceptionHandler` (`RestExceptionHandler.java:19-28`). The exact HTTP status then depends on Spring's default handling, which is not in the code. The view says "not 400" and does not name a status (unconfirmed).
- Replies from the facade and controller are assumed to pass through unchanged.

## Check results
- `puml-check`: no overlaps and no group-label warnings. The remaining warning is `aspect` (ratio 0.97 vs 1.78: a tall sequence diagram that cannot be reshaped without splitting it). There are two info lines: a group label on a lifeline, and five replies spanning two lifelines.
- `check_inventory.py`: exit 0, 0 issues, 7 elements, 7 relations.
