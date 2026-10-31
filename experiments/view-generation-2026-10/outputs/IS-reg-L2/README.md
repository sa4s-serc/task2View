# View: User registration (UC1) - UML sequence diagram

Viewpoint: dynamic. Model kind: UML sequence diagram. Stakeholder: integration tester.
Source: `JavaProject/src/main` (AuthenticationController, LibraryFacade, UserManager,
StudentFactory/LibrarianFactory, UserRegistry, PersistenceManager, registration.html, Swing `Registration`).

## What it shows
The runtime interaction when a new Student or Librarian creates an account: from the registration
form (web page or Swing client), through the REST controller (web only), the facade, the
`UserManager` (validation, uniqueness checks, role-specific creation), the `UserRegistry` and
`PersistenceManager`, down to the MySQL database. The success path and the two error paths
(validation/uniqueness -> HTTP 400; persistence failure) are shown as alternatives.

## How it addresses the concern
- **Main components and responsibilities (structural/behavioural):** each participant is labelled
  with its role. The form collects input; `AuthenticationController` exposes `POST /api/auth/register`;
  `LibraryFacade` is the single entry point and delegates; `UserManager` validates and orchestrates;
  the factories create the Student or Librarian; `UserRegistry` provides lookups and save;
  `PersistenceManager` runs JPA transactions; `RestExceptionHandler` maps errors to HTTP.
- **Control flow:** the message order shows validation first (no data access), then duplicate checks
  on email and identifier, then creation and persistence, then the DTO or error returned to the user.
- **Connectivity / integration points:** markers IP0-IP7 (explained in the legend) identify the interfaces
  to exercise: the HTTP contract (IP1), the facade entry shared by web and Swing (IP2),
  manager-to-registry checks (IP3), factory (IP4), registry-to-persistence-to-database with
  the unique-email constraint (IP5/IP6), and response/error mapping (IP7).

## Observations useful for test design
- Swing calls `LibraryFacade` directly, so the HTTP layer is only covered via the web client or REST calls.
- A `RuntimeException` from a failed save is not handled by `RestExceptionHandler` (only
  IllegalArgument/IllegalState/Security), so the response then depends on the framework default.
- Passwords are stored and compared in plain form in the entity (no hashing in the registration path).
