# UML component view: municipal report management desktop application

**Takeaway.** The application is a four-layer stack (Presentation → Application logic → Domain → Persistence), where each layer uses the interface of the layer below it, except that the GUIs also use domain entity types directly. The last layer talks to an external MySQL database.
**Stakeholder:** software architect. **Detail level:** overview, as given (whole system, high level).
Files: `view.puml` (generated from `model.json` by `component_model.py`), `view.png`, `inventory.json` (elements, relations and evidence).

## How the view answers the concern
- **Components and responsibilities:** four components, each with a one-line responsibility in `inventory.json`. They map to the packages `Boundary` (Swing GUIs), `Control` (controllers), `Entity` (entities, status states and the report and user services) and `Database` (JPA persistence). The MySQL database `reports_db` is external.
- **Layers or subsystems:** the diagram reads top to bottom as presentation, application, domain, persistence, then the store.
- **Main dependencies:** each «use» dependency points from caller to the interface it needs: GUIs → Use-case API (`SystemServicesController`); GUIs → Domain component, labelled "uses entity types" (a layering shortcut: `ReportCategory` in `ReportCreationGUI.java:4` and `ReceivedReportsGUI.java:4`, 7 code dependencies in all); controllers → Domain API (`ReportService`, `UserService`); Domain → Persistence API (`PersistenceService`); persistence → JDBC (Hibernate/JPA persistence unit).
- **Separation and collaboration:** the GUIs hold no persistence code (but do reach the domain directly for entity types), and the controllers delegate to the domain services. The domain services are the only callers of `PersistenceService`, and only `Database` uses JPA and JDBC.

## Omitted on purpose
- Individual GUIs, controllers and entity classes, and the report status classes (Submitted, Assigned, InProgress, Resolved).

## Assumptions
- The service classes live in the `Entity` package, so they are part of the Domain component.
- The interfaces are named after the facade classes that provide them. They are not Java `interface` types.
- No deployment information beyond the MySQL connection string in `persistence.xml`.

## Check results
- `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues. The only note is the unchecked external database.
- `puml-check`: renders. It reports 3 warnings: the captions "Use-case API" and "Domain API" partly overlap, and two captions touch their lollipop symbols. The generator controls that layout, so I left them.

## Revision (v1 is kept in `v1/`)
- Reviewer finding: the view hid the Presentation → Domain dependency. The code confirms it (`ReportCreationGUI.java:4`, `ReceivedReportsGUI.java:4` import `Entity.ReportCategory`), so I added the «use» dependency from Presentation to Domain and removed it from "omitted".
- The parenthesised label the reviewer suggested is rejected by `component_model.py` (labels must be 1–4 plain words), so it reads "uses entity types".
- Side effect: I shortened two interface names ("Use-case services API" → "Use-case API", "Domain services API" → "Domain API") to reduce overlap. The new edge changes the layout, and the two captions still overlap a little.
