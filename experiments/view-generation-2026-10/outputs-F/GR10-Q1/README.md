# UML component diagram: Municipal Report Management System (overview)

**Takeaway:** the desktop app is a strict top-down stack (Swing screens → use-case controllers → domain services → persistence → MySQL), where only the screens (for the `ReportCategory` enum), the services and the persistence mapping touch the domain entities.

**Stakeholder:** software architect. **Detail level:** overview, as given in the perspective: one component per layer, 6 components plus the user. Engineering wording (Swing, JPA/Hibernate, JDBC) is used. A balanced level would add the individual screens and controllers and the per-use-case chains.

Files: `view.puml`, `view.png` (and `view.svg`), `inventory.json` (elements, relations, `file:line` evidence).

## How the concern is addressed
- **Components and responsibilities:** each box names its package and role. Swing screens (`Boundary`) render the UI and call the controllers. Use-case controllers (`Control`) include the `SystemServicesController` facade. Domain services (`ReportService`, `UserService`) hold business rules. Domain entities are the JPA entities and the report states (Submitted → Assigned → In Progress → Resolved). Persistence access (`PersistenceService`, `JpaUtil`) is the generic JPA CRUD and query layer.
- **Layers/subsystems:** the vertical order is the layer order (presentation, application, domain, persistence). The BCED packages `Boundary`, `Control`, `Entity` and `Database` map to these layers. The domain services live in the `Entity` package, so the domain layer is split into services and entities.
- **Main dependencies:** arrows point from dependent to dependency. The screens only reach the domain for the `ReportCategory` enumeration. Only the domain services reach persistence, and only persistence reaches the database.
- **UI / logic / entities / persistence separation:** the UI never touches services or persistence, and the controllers never touch persistence or entity objects: they work with Map-based data returned by the services. Entities are accessed via services, and the persistence component is the only one that talks to MySQL (`reports_db`, per `persistence.xml`).

## Omitted on purpose
Individual screens and controllers, test packages, and fine-grained class dependencies (collapsed into the layer relations). The three `main` entry points (Home, Login, Registration screens) are not drawn separately. The `forms_rt` GUI library is not drawn, since libraries are not boxes.

## Assumptions
- The user is shown as a single actor, "Citizen / Municipal operator". Both roles exist as entities (`Citizen`, `MunicipalOperator`).
- Domain services are treated as a separate component from the entities, although both are in package `Entity`.

## Revision 1 (after reviewer critique-1.json)
The previous version is in `v1/`. Changes:
- Removed Controllers → Domain entities ("handles entities"). Verified: the only non-service `Entity` import in `Control` is an unused `ReportCategory` import (`ReportCreationController.java:3`). It is listed under omitted. Services return `Map<String,Object>` data, which is now stated on the services box.
- Added Persistence access ..> Domain entities ("maps to tables"), backed by `persistence.xml:14-20`.
- All inter-component relations are now dashed dependencies (`..>`). The user → screens relation stays solid, since it is a use by a person, not a code dependency.
- Each box now has a one-line responsibility and its package name. The controllers box says "mostly via SystemServicesController" because `UserLoginGUI` calls `UserLoginController` directly (`UserLoginGUI.java:111`).
- **Not applied as drawn:** layer UML packages around the components. I tried them, but they count as extra drawn elements (11 against the overview budget of 7) and made edges run through package titles. The layers and the single `Entity` package that holds both domain services and entities are shown by the vertical order and the "(package …)" labels. The MySQL box is muted and marked "(external)" instead of being placed outside a boundary box.

## Check results
- `puml-check`: OK, 7 nodes, 8 edges, 0 crossings, 0 issues.
- `check_inventory.py --level overview --graph .claude/repo-graph.json`: 1 issue, 2 notes.
  - Issue: `persist->dom` has no dependency in the code graph, because the mapping is declared in `persistence.xml` and not imported. I kept it because the reviewer and the config both support it.
  - Note: `ctrl--dom` is not drawn (the unused import above).
  - Note: `user` and `db` are not checked against the graph (no members).
