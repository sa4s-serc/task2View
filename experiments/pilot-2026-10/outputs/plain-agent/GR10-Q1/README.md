# Architecture views – GR10-Q1 (Municipal Report Management System)

Java 23 / Swing desktop app, JPA (Hibernate) + MySQL, organised as BCED packages (Boundary, Control, Entity, Database). Derived from `src/main/java` and `persistence.xml`.

- **view-1.puml – Layered component view.** Shows the four layers, the components in each, and dependencies: Boundary GUIs (navigation Home → Login → Dashboard → feature screens), the `SystemServicesController` facade delegating to per-use-case controllers, controllers using `UserService`/`ReportService` (which live in `Entity`), and those services using `PersistenceService` → `JpaUtil` → MySQL. Answers the layering/decomposition and UI / application logic / domain / persistence separation questions. Notable observations: `UserLoginGUI` calls `UserLoginController` directly (bypassing the facade); domain services in `Entity` depend on `Database`; controllers return `Map`s rather than entities.
- **view-2.puml – Domain model.** Entities, embeddables, inheritance (`User` single-table → `Citizen`/`MunicipalOperator`), `Report` aggregate (status history, internal notes, `Notification`), the State pattern for the report lifecycle (Submitted → Assigned → In Progress → Resolved), and where the services sit. Shows what is persisted vs. transient and where domain logic lives.
- **view-3.puml – Collaboration (sequence) for report status update.** Shows how the layers cooperate on one representative functionality, including notification generation and persistence.

Note: `Credentials` and `Location` are `@Embeddable`s and not listed in `persistence.xml`'s class list; this is from the code, not an assumption of the diagrams.
