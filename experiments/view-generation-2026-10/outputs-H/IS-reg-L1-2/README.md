# UML sequence diagram: user registration (IS-reg-L1-2)

**Takeaway:** a registration submitted in the Swing form goes form → library facade → user manager. The manager validates, then checks the email and then the identifier through the user registry (persistence manager, MySQL), has a user factory create the account and saves it. Each failure exits at the point where the code throws it and comes back to the form as an error.

Stakeholder: integration tester. Detail level: balanced (components involved and the calls between them, no new lifelines).

## Concern: how do the components interact during registration?
- Main call chain and its arguments: the success path of `view.puml`.
- Early exits, in code order, as `break` fragments: empty field (form only, no facade call); invalid fields (manager, before any registry call); email in use; identifier in use (a second lookup by student number or librarian code, chosen by role); save failed (persistence returns false after rollback, manager throws a server error).
- The user factory is created by the manager for the role (`create` message).
- The REST endpoint `POST /api/auth/register` is in a note: same facade call; its exception handler maps IllegalArgumentException to HTTP 400, while the save-failure RuntimeException is not handled there.

Details: `inventory.json`; `check_inventory.py` 0 issues (note: user and database have no members). `check_consistency.py` against IS-reg-L1: consistent. `check_view.py` clean; `puml-check` no warnings.

## Revision after critique-1 (previous version in `v1/`)
Changed: validation failure moved before the registry lookup; the duplicate check split into email then identifier, each with its own exit; save-failure exit added; form's "Complete all fields" exit added; factory shown with a create message; database replies added; exits drawn as `break` fragments so activations end correctly.
Kept, because the code contradicts the critique: it said REST errors are an unhandled exception. `boundary/SpringBoot/RestExceptionHandler.java:19-22` handles IllegalArgumentException as HTTP 400 with an error body; only the save-failure RuntimeException is unhandled. The note says this.

## Omitted
Authentication REST API lifeline, DTOs, Swing helpers, login screen, JpaUtil; individual field validations are collapsed into one self-call.

## Assumptions
The Swing form is the main flow; "User factories" stays one lifeline standing for StudentFactory/LibrarianFactory so its name matches view IS-reg-L1.
