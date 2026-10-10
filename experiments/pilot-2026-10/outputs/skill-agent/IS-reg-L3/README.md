# Task2View single-agent run: IS-reg-L3

**Goal:** I am an integration tester. I need to design integration tests for the user registration functionality. Before defining the tests, I need to understand the high-level architecture supporting this functionality. I want to identify the main components involved in the registration process, their responsibilities, and the interactions and dependencies among them. In particular, I need to understand which components handle the registration request, validate the user's personal information and selected role, manage role-specific data such as the student ID or librarian identifier, verify the validity and uniqueness of the account, and persist the newly created user. I also need to understand how these components collaborate when invalid or already existing user data is provided, so that I can identify the main integration points and interactions that should be covered by the tests.

- **Role:** integration tester (`tester`)
- **Target:** user registration functionality
- **Detail level:** detailed (the goal enumerates 5 subjects)
- **Primary needs:** decomposition, dependencies, collaboration, interaction-order
- **Secondary needs:** interface-contract (covered by V2), data-structure (not shown)
- **Model / condition:** Claude Sonnet 5.5 (claude-sonnet-5-5), agent + task2view skill, notation PlantUML. No usage.json: the tool does not report tokens or cost to the agent.

## Views

| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-decomposition | decomposition | confirm | pass_with_limitations | 14 | PlantUML (`V1-decomposition/view.puml`, compile check: pass) |
| V2-client-server | client-server | confirm | pass_with_limitations | 15 | PlantUML (`V2-client-server/view.puml`, compile check: pass) |
| V3-sequence | sequence | confirm | pass_with_limitations | 9 | PlantUML (`V3-sequence/view.puml`, compile check: pass) |

## Rationale

- **decomposition**: Decomposition Style (2.1 Decomposition Style) covers decomposition; combined with layered (V&B 6.6) because the repository shows layered.
- **client-server**: Client-Server (4.3.1 Client-Server Style) covers dependencies, collaboration, interface-contract; specialised from cnc-generic because the repository shows rest-api; combined with layered (V&B 6.6) because the repository shows layered.
- **sequence**: Sequence (8.3.1 Notations for Capturing Traces (sequence diagrams)) covers interaction-order; combined with layered (V&B 6.6) because the repository shows layered.

Order of views follows the first primary need each covers: structure and responsibilities (V1), collaboration and dependencies (V2), failure and alternative paths (V3).

## Limitations and declared gaps

- (V1-decomposition) Layer groups are containers and are not counted toward the 15-element cap; the 14 drawn components fit the cap.
- (V1-decomposition) is-part-of is drawn as nesting of each component in its layer group (the relations are listed in view.json).
- (V1-decomposition) UserDTO (returned by AuthenticationController, LibraryFacade and UserManager) is not an element of the evidence model and is not drawn.
- (V2-client-server) RestExceptionHandler has no relation: Spring binds it through @RestControllerAdvice/@ExceptionHandler, so no registration component depends on it statically. Its role in failure paths is shown in V3.
- (V2-client-server) Generalization (StudentFactory/LibrarianFactory implement UserFactory; Student/Librarian extend User) is not a Client-Server relation kind and is not drawn; it is in the evidence model.
- (V2-client-server) Swing Registration calls LibraryFacade in-process; the only request-reply connector (HTTP from registration.html to AuthenticationController) is shown in V3.
- (V2-client-server) The 15-element cap is reached (14 components and the datastore); layer groups are containers and not counted.
- (V2-client-server) UserDTO is not drawn (not an element of the evidence model).
- (V3-sequence) One scenario only: registration through POST /api/auth/register. The Swing client calls LibraryFacade.register directly and shows errors with showError(ex.getMessage()); it is an alternative entry and is not drawn.
- (V3-sequence) The returns '400 {error}', 'UserDTO' and the RuntimeException of a failed save are inferred from the controller/handler/manager code (no direct call), so they have support 'inferred'.
- (V3-sequence) RestExceptionHandler handles IllegalArgumentException, IllegalStateException and SecurityException only: the RuntimeException of a failed save has no handler in the code, so the HTTP response of that path is not evidenced.
- (V3-sequence) Role alternatives (Student / Librarian) are drawn as alt/else pairs of the fragments recorded separately in the evidence model.
- (V3-sequence) The layered overlay is shown as stereotypes on the lifelines (lifelines follow first appearance, so layer boxes cannot be contiguous).
- Declared gaps: none. Uncovered primary needs: none. Secondary need not shown: data-structure (no data-model view was selected; role-specific fields appear only as responsibilities of Student and Librarian).
- The 15-element cap is counted on non-group elements; layer groups are not counted. If groups were counted, V1 and V2 would exceed the cap (4 + 14 and 4 + 15).
- Task fit (layer 5) is `not-run`: a different model must judge.
- Source comments in the repository were replaced by a placeholder, so responsibilities come from names, validations and calls, not from documentation.

## Evidence counts

- Claims: 70 verified, 0 rejected (element: 20, relation: 23, interaction: 27); support: observed: 64, inferred: 6
- Evidence model: 16 elements, 37 relations (incl. 14 derived is-part-of), 1 scenario with 27 steps and 11 alt fragments
- Reflexion: all claimed relations converge with code edges; no divergence or absence recorded.
