# Task2View — IS-reg-L1

- **Goal:** I am an integration tester. I need to test the user registration functionality and understand which system components are involved and how they interact.
- **Role:** integration tester (`tester`) · **Target:** user registration functionality · **Detail level:** overview
- **Primary need:** collaboration ("which system components are involved and how they interact") · **Secondary needs:** none
- **Model:** Claude Sonnet 5.5 (single agent + task2view skill, notation PlantUML). Token/cost usage is not reported by the tool here, so `usage.json` is omitted.

## Views
| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-client-server | Client-Server (4.3.1) + layered overlay | simplify | pass_with_limitations | 6 components in 4 layer groups (+1 overflow) | PlantUML (`V1-client-server/view.puml`) |

## Rationale
Only one need is primary (collaboration), and only `cnc-generic` covers it among applicable viewpoints, so one view suffices. The repository exposes REST endpoints, so the style is Client-Server; it has 4 layers, so layer groups are added. With one need and no enumerated subjects the detail level is *overview*, so components are packages (cap 6). The 7th element (datastore) overflowed → decision `simplify`.

## What the view shows (registration flow)
Entry points: REST `POST /api/auth/register` (SpringBoot), the Swing `Registration` frame, and the web page `registration.html` (not drawn; see limitations). `RegistrationTest` bypasses both and calls `LibraryFacade.register` directly — a seam for integration tests below the UI/HTTP layer. Chain: boundary → `LibraryFacade` → `UserManager` (validation, duplicate checks) → `StudentFactory`/`LibrarianFactory` → `UserRegistry` → `PersistenceManager` → `JpaUtil` → MySQL `reservationsdb`. Failures surface as `IllegalArgumentException`/`RuntimeException` (400 via `RestExceptionHandler`, dialog in Swing).

| From | To | Label in view | Operations | Claims |
|---|---|---|---|---|
| boundary.SpringBoot | controller | 1 dependency | register | C16 |
| boundary.Swing | controller | 1 dependency | register | C17 |
| controller | controller.factory | 3 dependencies | createUser, new StudentFactory | C18, C19, C20 |
| controller | entity | 5 dependencies | registerUser, institutionalEmailExists | C21 |
| controller.factory | entity | 5 dependencies | new Student, new Librarian | C22, C23 |
| entity | database | 3 dependencies | save, findFirstByFields | C24 |

## Limitations and gaps
- Overview grain: one component per package, named after the package's last segment (evidence rule); class-level collaborators are listed in each component's responsibilities.
- Datastore reservationsdb (MySQL, reached through JpaUtil/persistence.xml) overflowed the 6-element cap and is not drawn; it is mentioned in the Persistence component only through JpaUtil.
- The browser client (static/registration.html + app.js, POST /api/auth/register) is a script, not a symbol-backed component, so it is not drawn.
- Relation labels show dependency counts (simplify rule); operations are in evidence_model.json (register, createUser, registerUser, save).
- Dependencies were collected for the registration flow only; login and reservation flows were not traversed.
- UserDTO (package dto) is the return type of the flow but has no claim of its own and no component; it appears only in responsibilities.
- Order of calls is not shown (no behavioural need in the goal).
- Package-named components: constraint `no_package_or_directory_element` was read as applying to package/directory *kinds*; overview components are mandated by the evidence rules. Flagged as a warning.
- Sources import `org.springframework.web.bind.yeartation.*` (not a Spring package), so the delivered code appears not to compile unmodified; the analysis reads the code as written.
- Task fit (layer 5) is `not-run`; a different model must judge.
- Declared gaps: none. Uncovered needs: none.

## Evidence counts
Claims verified: 24 · rejected: 1 · elements: 7 · relations: 6 (all convergence) · scenarios: 0.
