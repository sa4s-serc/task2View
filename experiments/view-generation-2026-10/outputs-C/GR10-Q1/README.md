# Component view: municipal problem reporting desktop application

**Takeaway:** a four-layer Boundary → Control → Entity → Database application: Swing screens call a controller facade, controllers drive domain services that manipulate JPA entities, and a persistence service stores them in MySQL.
**Stakeholder:** software architect. **Detail:** overview (7 elements), because the perspective is the whole system before planning evolution. Wording is technical (Swing, JPA/Hibernate, JDBC).

## How the concern is addressed
- **Components and responsibilities:** one box per role (see inventory).
- **Layers/subsystems:** the four packages mirror the source packages `Boundary`, `Control`, `Entity`, `Database`.
- **Main dependencies:** the arrows; GUI → controllers → domain services → persistence → MySQL.
- **UI / logic / domain / persistence separation:** Swing GUIs only call controllers; use-case logic lives in `Control`; entities are JPA-annotated classes; all `EntityManager` access is in `Database`.

## Inventory
| Element | Evidence |
|---|---|
| Swing GUI Screens (10 `*GUI` classes) | `src/main/java/Boundary/HomePageGUI.java:6,75` (javax.swing, main) |
| System Services Controller (facade) | `Control/SystemServicesController.java:22-29` creates the 7 use-case controllers; GUIs create it e.g. `Boundary/ReportCreationGUI.java:70` |
| Use-case Controllers (incl. NotificationController) | `Control/ReportStatusUpdateController.java:21` |
| Domain Services (ReportService, UserService) | `Entity/ReportService.java:22`, `Entity/UserService.java:20` |
| Domain Entities | `Entity/User.java:28`, `Entity/Report.java:31`, `resources/META-INF/persistence.xml:14-20` |
| Persistence Service (PersistenceService + JpaUtil) | `Database/PersistenceService.java:18`, `Database/JpaUtil.java:17` |
| MySQL reports_db | `persistence.xml:26-27`, `pom.xml:43` |
| Edge GUI → Use-case Controllers (log in) | `Boundary/UserLoginGUI.java:111` |
| Edge GUI ⇢ Entities | `Boundary/ReceivedReportsGUI.java:4` imports `Entity.ReportCategory` |
| Edge Persistence ⇢ Entities | JPA entities listed in `persistence.xml:14-20` |

## Omitted on purpose
Individual GUI screens and controllers, concrete entity subclasses (Citizen, MunicipalOperator, statuses), Hibernate/JDBC driver as boxes (technology labels), tests.

## Assumptions
- Layer names are the source package names; "Entity" holds both domain services and entities.
- MySQL is shown as a database element, not a deployment node; it is external to the app.
- Separation is by convention: the facade returns `Map<String,Object>` data (`SystemServicesController.java:35,85`), but one GUI imports an entity enum.

## Check result
`puml-check`: 1 warning (aspect ratio 1.16 vs 1.78, tall because the layers are chained; left-to-right was worse at 3.87), 0 label/overlap issues, 1 edge crossing. Image review: all edges and labels readable; no change needed. Rendered with the plantuml-diagrams checker.
