# Component view: Municipal Report Management desktop application

**Takeaway:** a layered Boundary → Control → Entity services → Database desktop application, where the domain entities are shared by services and persistence, and the data lives in one MySQL database.
**Stakeholder:** software architect. **Detail level:** overview (6 components, budget ≤ 7), as the perspective is the whole system before planning evolution.

## How the view addresses the concern
- **Main components and responsibilities:** Boundary = GUI screens (login, registration, dashboard, report creation, submitted/received reports, status update, internal notes, activity monitoring). Control = `SystemServicesController` facade plus one controller per use case, which checks roles and delegates. Entity services = `UserService`, `ReportService`, which hold the business operations. Domain entities = the JPA classes. Database = `PersistenceService` (save/update/find) and `JpaUtil` (EntityManagerFactory).
- **Layers/subsystems:** the four packages `Boundary`, `Control`, `Entity`, `Database`; `Entity` is split into services and domain entities because they play different roles.
- **Main dependencies:** arrows point from dependent to dependency (see the diagram labels).
- **Separation UI / logic / domain / persistence:** UI only talks to Control, never to services or the database; persistence is reached only through the Entity services.

## Inventory (element → evidence)
- Boundary: `src/main/java/Boundary/*GUI.java`; the GUIs create `SystemServicesController` (e.g. `ReportCreationGUI.java:70`); `UserLoginGUI.java:111` uses `UserLoginController` directly. Swing is inferred from the `.form` files (IntelliJ forms_rt, `pom.xml`).
- Control: `Control/SystemServicesController.java:23-29` (creates the 7 use-case controllers); controllers create `UserService`/`ReportService` (e.g. `ReportReviewController.java:21-22`).
- Entity services: `Entity/UserService.java:20`, `Entity/ReportService.java:22` (use `PersistenceService`).
- Domain entities: `Entity/User.java:28`, `Citizen.java:11`, `MunicipalOperator.java:11`, `Report.java:31`, `Submitted/Assigned/InProgress/Resolved` implementing `ReportStatus`, `InternalNote`, `StatusUpdate`, `Notification`.
- Database: `Database/PersistenceService.java`, `Database/JpaUtil.java:11`; entity mapping in `resources/META-INF/persistence.xml` (Hibernate, JDBC MySQL `127.0.0.1:3306/reports_db`).

## Omitted on purpose
GUI-to-GUI navigation, individual controllers and GUIs, value classes (`Credentials`, `Location`, `ReportCategory`), tests, and class-level detail.

## Assumptions
- `ReportStatusUpdateController` also uses `NotificationController`; shown only inside the merged Control component.
- `Boundary` imports `Entity.ReportCategory` (`ReportCreationGUI.java:4`, `ReceivedReportsGUI.java:4`), a minor shortcut past Control that is not drawn.
- The MySQL server is drawn as a component (an external system), not as a deployment node.

## Check result
`puml-check`: 0 crossings, no overlaps, no tiny text; one advisory `aspect` warning (portrait ratio 0.79), which is accepted because the view is a layered chain. The first attempt (left-to-right, with interface lollipops) was too wide, and the second had edges through labels, so both were reverted. The image review found no further fixes.
