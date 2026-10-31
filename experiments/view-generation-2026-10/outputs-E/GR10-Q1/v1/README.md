# UML component diagram: Municipal Report Management System, whole system

**Takeaway:** the Swing desktop application is a layered system (UI → controllers → domain services → persistence → MySQL), with the domain entities shared by the services and the persistence layer.
**Stakeholder:** software architect. **Detail level:** overview, as given in the perspective. 6 components, 6 relations.

Files: `view.puml`, `view.png`, `inventory.json` (elements, relations, evidence as `file:line`).

## How the view addresses the concern
- **Components and responsibilities:** each box carries a short responsibility (`ui`, `ctrl`, `svc`, `ent`, `pers`, `db`).
- **Layers/subsystems:** the vertical chain User Interface (package `Boundary`), Application Controllers (`Control`), Domain Services, Persistence Layer (`Database`), and the external database.
- **Main dependencies:** arrows point from dependent to dependency. The UI calls controllers; controllers delegate to services; services create and change entities and use persistence; persistence maps entities and talks to MySQL over JDBC.
- **Separation and collaboration:** UI holds no business logic (it only calls `SystemServicesController` or `UserLoginController`). Business rules live in the services. Entities are plain domain objects annotated for JPA. Only `Persistence Layer` touches JPA and the database.

## Omitted on purpose
Individual GUI screens and use-case controllers (merged); state classes, enums, Credentials, Location (inside entities); tests.

## Assumptions
- `ReportService` and `UserService` sit in the Java package `Entity`, but they hold business logic and use persistence, so they are drawn as a separate "Domain Services" component. This is an interpretation of the code, not a package boundary.
- The Notification controller and login controller are folded into "Application Controllers".

A deeper level would show the individual controllers and screens, and the report state hierarchy.

## Check result
`puml-check`: OK, 6 nodes, 6 edges, 0 crossings, 0 issues (after one revision: switched from left-to-right, ratio 6.1, to top-to-bottom, ratio 0.96). `check_inventory.py --level overview`: 0 issues, 0 unbacked items.
