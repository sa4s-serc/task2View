# Sequence diagram: user registration

**Takeaway:** a registration request travels Registration Form → Authentication Controller → Library Facade → User Manager, which validates, checks uniqueness through User Registry / Persistence Manager, builds a Student or Librarian and saves it; any rule violation comes back as an exception shown to the user as an error.

**Stakeholder:** integration tester (end-to-end registration). **Detail:** balanced (one feature), 7 lifelines, ~18 messages; engineering wording (HTTP path, class names).

Files: `view.puml` (source), `view.png` (render).

## How the view addresses the concern
- **System components involved:** the 7 lifelines: user (Student/Librarian), Registration Form, Authentication Controller, Library Facade, User Manager, User Registry, Persistence Manager.
- **How they interact / control flow:** main flow top to bottom (submit, POST, facade delegation, validation, uniqueness check, factory creation, save, UserDTO back); one `alt` shows the error path (IllegalArgumentException mapped to HTTP 400, RuntimeException if saving fails).

## Inventory (element → evidence)
| Element | Evidence |
|---|---|
| Registration Form (web) | `JavaProject/src/main/resources/static/registration.html:53-70` (POST `/auth/register`, alert, show error) |
| Registration Form (Swing) | `boundary/Swing/Registration.java:116-141` (calls `LibraryFacade` directly) |
| Authentication Controller | `boundary/SpringBoot/AuthenticationController.java:16-31` (`POST /api/auth/register`) |
| Error mapping to HTTP 400 | `boundary/SpringBoot/RestExceptionHandler.java:19-22` |
| Library Facade | `controller/LibraryFacade.java:37-40` |
| User Manager (validate, uniqueness, factory, save, DTO) | `controller/UserManager.java:65-97` |
| Factory (Student/Librarian) | `controller/factory/StudentFactory.java`, `LibrarianFactory.java` (collapsed into a User Manager self-message) |
| User Registry | `entity/UserRegistry.java:26-67` |
| Persistence Manager | `database/PersistenceManager.java:19-43` (`save`, returns false on failure) |

## Omitted on purpose
Database/JPA internals, entities, DTO fields, login and other use cases, individual validation rules (collapsed to "validate input"), the two lookups (collapsed, "x2"), and the facade/controller return hops in the error path are shown but not annotated further.

## Assumptions
- The two uniqueness checks (email, identifier) are drawn as one message pair; in code they are separate calls (`UserManager.java:77-84`).
- On save failure `UserManager` throws `RuntimeException`, which `RestExceptionHandler` does not map (only IllegalArgument/IllegalState/Security); so the HTTP status for that case is unconfirmed. The `alt` shows "HTTP 400" only for rule violations.
- The Swing form path bypasses the controller; noted in the diagram, not drawn separately.

## Check result
Final `puml-check`: 0 warnings other than `aspect` (sequence diagrams are tall; 866x976), plus 1 info. Image review changed the error path from a trailing `alt` to an `alt accepted / else rejected`, and collapsed repeated lookups to stay under the message budget.
