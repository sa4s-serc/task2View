# Municipal Report Management System: component view (overview)

**Takeaway.** A standalone Swing desktop app in four layers: GUI screens call a controller layer, which calls domain services, and those use a generic persistence service (JPA/Hibernate) to reach one MySQL database.
**Stakeholder:** software architect, whole system before planning evolution. **Detail:** overview (7 components), with one box per role instead of one per class.

## How the view addresses the concern
- **Components and responsibilities:** each of the 7 boxes is described in `inventory.json`. The box label gives the layer and the role.
- **Layers:** Presentation (Swing GUI screens), Application (Services facade, Use-case controllers), Domain (Domain services, Domain entities), Persistence (Persistence service), plus the external MySQL database.
- **Main dependencies:** arrows run from dependent to dependency. The GUI goes through the facade, except login, which calls its controller directly. The controllers use the domain services, and those use the entities and the persistence service. Persistence maps the entities and talks JDBC to MySQL.
- **UI / logic / entities / persistence separation:** the GUIs never touch persistence. The only GUI-to-entity link is the `ReportCategory` enum. The persistence service has no knowledge of the controllers.

Evidence for every element and relation: `inventory.json`. `check_inventory.py`: 0 issues, 7 elements, 9 relations.

## Omitted on purpose
Individual GUI, controller and entity classes (merged per role); libraries (Swing, Hibernate, forms_rt) are named in labels only; tests.

## Assumptions
- The domain services (`ReportService`, `UserService`) live in the `Entity` package, so I drew them in the Domain layer. They also call persistence directly, so the Domain layer is not persistence-ignorant.
- Layer names are my grouping of the packages `Boundary`, `Control`, `Entity` and `Database`. Component boxes carry the layer in their label instead of package boxes.
- `NotificationController` and the others are inside "Use-case controllers". The facade does not reference `NotificationController` directly, since the status-update controller owns it.

## Check result
`puml-check`: renders with 0 crossings and 0 overlaps. One remaining `aspect` warning (portrait 0.84 against 16:9) comes from the strictly layered chain. I accepted it because flipping to left-to-right produced edge and label collisions. `view.png` is the rendered output.
