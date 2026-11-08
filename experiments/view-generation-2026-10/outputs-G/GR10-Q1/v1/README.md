# UML component view: municipal report management desktop application

**Takeaway.** The application is a four-layer stack (Presentation → Application logic → Domain → Persistence), and each layer is reached only through the interface of the layer below it. The last layer talks to an external MySQL database.
**Stakeholder:** software architect. **Detail level:** overview, as given (whole system, high level).
Files: `view.puml` (generated from `model.json` by `component_model.py`), `view.png`, `inventory.json` (elements, relations and evidence).

## How the view answers the concern
- **Components and responsibilities:** four components, each with a one-line responsibility in `inventory.json`. They map to the packages `Boundary` (Swing GUIs), `Control` (controllers), `Entity` (entities, status states and the report and user services) and `Database` (JPA persistence). The MySQL database `reports_db` is external.
- **Layers or subsystems:** the diagram reads top to bottom as presentation, application, domain, persistence, then the store.
- **Main dependencies:** each «use» dependency points from caller to the interface it needs: GUIs → use-case services API (`SystemServicesController`); controllers → domain services API (`ReportService`, `UserService`); domain → persistence API (`PersistenceService`); persistence → JDBC (Hibernate/JPA persistence unit).
- **Separation and collaboration:** the GUIs hold no persistence code, and the controllers delegate to the domain services. The domain services are the only callers of `PersistenceService`, and only `Database` uses JPA and JDBC.

## Omitted on purpose
- Individual GUIs, controllers and entity classes, and the report status classes (Submitted, Assigned, InProgress, Resolved).
- **Undrawn dependency:** the GUIs also depend directly on Entity types (7 code dependencies, e.g. `ReportCategory` in `ReceivedReportsGUI.java:430`). I left it out so the layered chain stays readable, so the diagram shows a stricter layering than the code has.

## Assumptions
- The service classes live in the `Entity` package, so they are part of the Domain component.
- The interfaces are named after the facade classes that provide them. They are not Java `interface` types.
- No deployment information beyond the MySQL connection string in `persistence.xml`.

## Check results
- `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues. The notes are the undrawn GUI→Entity dependency and the unchecked external database.
- `puml-check`: renders. It reports 4 `text-on-node` warnings, where interface captions touch the lollipop symbols. The generator controls that layout, so I left them. I read the PNG and all labels are legible.
