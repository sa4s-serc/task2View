# Sequence diagram – User registration (view.puml / view.png)

**Takeaway:** a registration request travels Registration form → AuthenticationController → LibraryFacade → UserManager → UserRegistry → MySQL; UserManager validates, checks duplicates, creates the Student or Librarian through a factory and persists it, and returns a UserDTO or an error that is mapped to HTTP 400.

**Stakeholder:** integration tester (end-to-end test of registration). **Detail:** balanced (one feature), engineering wording (REST path, JPA, MySQL). 6 lifelines, 11 messages (slightly under the 12 budget).

## Concern
- *System components involved:* the six lifelines, one per architectural role (inventory below).
- *How they interact / control flow:* the top-to-bottom messages show the call chain, the validation, duplicate check, creation, persistence and return path. The `alt` shows the error path (invalid input or duplicate -> IllegalArgumentException -> HTTP 400); the note on UserRegistry gives the save-failure path.

## Inventory (element -> evidence)
| Element | Evidence |
|---|---|
| Registration form (web) | `resources/static/registration.html:53-66` (POST `/auth/register`, then redirect to login) |
| Registration form (Swing) | `boundary/Swing/Registration.java:116-141` (calls `LibraryFacade.register` directly) |
| AuthenticationController | `boundary/SpringBoot/AuthenticationController.java:15-31` (`POST /api/auth/register`) |
| LibraryFacade | `controller/LibraryFacade.java:37-40` |
| UserManager (validate, duplicates, factory, save) | `controller/UserManager.java:65-97` |
| StudentFactory / LibrarianFactory | `controller/factory/StudentFactory.java:8-18`, `UserManager.java:89` |
| UserRegistry | `entity/UserRegistry.java:26-67` |
| PersistenceManager save (merged into UserRegistry lifeline) | `database/PersistenceManager.java:19-37` (begin/persist/commit, rollback -> false) |
| MySQL reservationsdb | `resources/META-INF/persistence.xml:21` |
| HTTP 400 mapping | `boundary/SpringBoot/RestExceptionHandler.java:18-21` |
| Test entry point (calls the facade) | `src/test/.../RegistrationTest.java:53-90` |

## Omitted on purpose
UserDTO/User entities, `app.js` helper, PersistenceManager as separate lifeline, individual validation rules, the repeated registry lookups (email, student number, librarian code), the Student/Librarian role branch in detail, the login flow.

## Assumptions
- The Swing and web forms are shown as one lifeline; the Swing path skips AuthenticationController (note in view).
- Error replies are drawn as one message from UserManager to the form, with a note that they pass through LibraryFacade and AuthenticationController.
- No notification or e-mail step exists in registration code (none found).

## Check
Final puml-check: 0 errors; 2 warnings (alt label and one error message cross a lifeline because the form is far left of UserManager) – accepted, as shortening further lost meaning. Image review: layout readable, no overlaps; no changes needed after the first image.
