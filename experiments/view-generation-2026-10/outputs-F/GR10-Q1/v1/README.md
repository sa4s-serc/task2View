# UML component diagram: Municipal Report Management System (overview)

**Takeaway:** the desktop app is a strict top-down stack (Swing screens → use-case controllers → domain services → persistence → MySQL) in which the domain entities are shared by every layer above persistence.

**Stakeholder:** software architect. **Detail level:** overview, as given in the perspective: one component per layer, 6 components plus the user. Engineering wording (Swing, JPA/Hibernate, JDBC) is used. A balanced level would add the individual screens and controllers and the per-use-case chains.

Files: `view.puml`, `view.png` (and `view.svg`), `inventory.json` (elements, relations, `file:line` evidence).

## How the concern is addressed
- **Components and responsibilities:** each box names its package and role. Swing screens (`Boundary`) render the UI and call the controllers. Use-case controllers (`Control`) include the `SystemServicesController` facade. Domain services (`ReportService`, `UserService`) hold business rules. Domain entities are the JPA entities and the report states (Submitted → Assigned → In Progress → Resolved). Persistence access (`PersistenceService`, `JpaUtil`) is the generic JPA CRUD and query layer.
- **Layers/subsystems:** the vertical order is the layer order (presentation, application, domain, persistence). The BCED packages `Boundary`, `Control`, `Entity` and `Database` map to these layers. The domain services live in the `Entity` package, so the domain layer is split into services and entities.
- **Main dependencies:** arrows point from dependent to dependency. The screens only reach the domain for the `ReportCategory` enumeration. Only the domain services reach persistence, and only persistence reaches the database.
- **UI / logic / entities / persistence separation:** the UI never touches services or persistence, and the controllers never touch persistence. Entities are accessed via services, and the persistence component is the only one that talks to MySQL (`reports_db`, per `persistence.xml`).

## Omitted on purpose
Individual screens and controllers, test packages, and fine-grained class dependencies (collapsed into the layer relations). The three `main` entry points (Home, Login, Registration screens) are not drawn separately. The `forms_rt` GUI library is not drawn, since libraries are not boxes.

## Assumptions
- The user is shown as a single actor, "Citizen / Municipal operator". Both roles exist as entities (`Citizen`, `MunicipalOperator`).
- Domain services are treated as a separate component from the entities, although both are in package `Entity`.

## Check results
- `puml-check`: OK, 7 nodes, 8 edges, 0 crossings, 0 issues.
- `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues. The only note is that `user` and `db` have no members, so their relations are not checked against the graph.
- Not reviewed by a separate reviewer.
