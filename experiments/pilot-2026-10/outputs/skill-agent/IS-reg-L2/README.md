# Task2View — IS-reg-L2 (single agent + skill)

**Goal (verbatim):** I am an integration tester. I need to design integration tests for the user registration functionality. Before defining the tests, I need to understand the main components involved in registration, their responsibilities, and how they interact when a new user creates an account. I also need to identify the main integration points that should be exercised during the tests.

- **Role:** integration tester (`tester`) · **Target:** user registration functionality · **Detail level:** feature (3 primary needs, no subjects)
- **Primary needs:** collaboration, interaction-order, interface-contract · **Secondary:** decomposition ("their responsibilities")
- **Produced by:** Claude Sonnet 5.5 (`claude-sonnet-5-5`), Claude Code with the task2view skill. `usage.json` is omitted: no cost report was available to the agent.

## Views
| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-client-server | Client-Server (V&B 4.3.1), layered overlay | confirm | pass_with_limitations | 10 (+4 layer groups) | PlantUML (compiles) |
| V2-sequence | Sequence (V&B 8.3.1), layered overlay | confirm | pass_with_limitations | 8 (+4 layer boxes) | PlantUML (compiles) |

Task fit (layer 5) is `not-run`: a different model must judge it.

## Rationale
- **V1** answers *which components take part in registration, what each is responsible for, and through which operations they call each other*. The repository exposes REST endpoints, so `cnc-generic` is specialised to client-server. Edge labels are the integration-point operations.
- **V2** answers *the order of calls* from `POST /api/auth/register` down to the database, with an `alt` for the Student and the Librarian branch.
- Two views are the minimum: no single viewpoint covers both structural and behavioural needs.

## Main integration points for the tests (read from the views)
1. `AuthenticationController.register` (POST `/api/auth/register`, form parameters role, name, surname, email, password, identifier) and the Swing `Registration.register()`: two entries into the same `LibraryFacade.register`.
2. `LibraryFacade` -> `UserManager.register`: validation, uniqueness checks, factory choice.
3. `UserManager` -> `UserRegistry` (`institutionalEmailExists`, `findStudentByStudentNumber` / `findLibrarianByCode`, `registerUser`) -> `PersistenceManager` (`findFirstByFields`, `save`).
4. `UserManager` -> `StudentFactory` / `LibrarianFactory` (`createUser`).
5. `PersistenceManager` -> `JpaUtil` -> persistence unit `reservationsPU` -> MySQL `reservationsdb` (the test unit points to `reservationsdb_test`; `RegistrationTest` already deletes from `Reservation` and `User` around each test).
6. Failure paths worth exercising (code read, not drawn as messages): `IllegalArgumentException` for invalid input, duplicate email or identifier; `RuntimeException` when `registerUser` returns false; `RestExceptionHandler` maps `IllegalArgumentException` to HTTP 400.

## Limitations and declared gaps
- No declared gaps; no uncovered primary need. Secondary need `decomposition` is not a framed need of any chosen view; responsibilities appear inside components.
- Only one scenario is drawn (REST entry). The Swing entry differs only in its first step.
- Not drawn, read but not claimed: `UserFactory` (interface with two implementations; client-server has no generalization relation), entities `User`/`Student`/`Librarian`, `UserDTO`, `RestExceptionHandler`, the browser page `registration.html` (no code symbol).
- `JpaUtil` reaches MySQL only through `persistence.xml`; reads/writes edges are drawn from `PersistenceManager` with both files cited.
- The goal's enumeration ("components", "responsibilities", "interact", "integration points") was treated as needs, not as subjects.
- Layer groups do not count toward the cap of 10 / 8.
- Source comments are placeholders ("English implementation note"); responsibilities are my reading of the code.

## Evidence counts
34 claims verified (11 elements, 10 relations, 13 interactions), 0 rejected; evidence model: 11 elements, 10 relations, 1 scenario (13 steps, 1 alt). All claims `observed`. Excerpts were checked against the files by script (±3 lines of slack).
