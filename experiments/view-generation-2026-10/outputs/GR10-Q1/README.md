# GR10-Q1 – Component view (UML component diagram)

`view.puml` shows the high-level structure of the municipal problem-reporting desktop application (Java Swing + Hibernate/JPA + MySQL), derived from the packages in `src/main/java`.

## What it shows
Four layers, each matching a source package, plus the external MySQL database:
- **Presentation (`Boundary`)**: Swing GUIs, grouped into access/registration, dashboard, citizen report screens and operator screens.
- **Application logic (`Control`)**: `SystemServicesController` is a facade that delegates to one controller per use case; `UserLoginController` is called directly by the login GUI; `NotificationController` is used by the status-update controller.
- **Domain (`Entity`)**: JPA entities (users, reports, notes, notifications, ...), the status-state classes behind the `ReportStatus` interface, and the domain services `UserService` / `ReportService`, which hold the business rules.
- **Persistence (`Database`)**: `PersistenceService` (generic save/update/find) over `JpaUtil` (EntityManagerFactory, unit defined in `persistence.xml`), connected to MySQL `reports_db`.

## How it addresses the concern
- **Main components and responsibilities**: each component is labelled with its role and key classes.
- **Layers/subsystems**: the four packages above.
- **Main dependencies**: arrows go strictly downward (GUI -> controllers -> domain services -> persistence -> DB). Dotted arrows are GUI-to-GUI navigation and the JPA mapping of entities.
- **Separation of UI, logic, domain, persistence**: the GUIs only talk to controllers and exchange `Map<String,Object>` data rather than entities. Controllers orchestrate use cases through the domain services. Only the domain services access persistence, and only `JpaUtil` touches the database.

## Observation
The domain services live in the `Entity` package and call `PersistenceService` directly, so the domain layer depends on persistence. This is not a clean separation and is worth noting before planning evolution.
