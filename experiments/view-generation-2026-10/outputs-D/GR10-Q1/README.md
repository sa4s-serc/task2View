# Municipal Report Management System: component view (layers and dependencies)

**Takeaway.** A standalone Swing desktop app in four Java packages: GUI screens call the Control package (facade and use-case controllers), which calls report and user services that sit in the Entity package and use a generic persistence service (JPA/Hibernate) to reach an external MySQL database.
**Stakeholder:** software architect, whole system before planning evolution. **Detail:** balanced (12 elements), raised from overview. The reviewer asked for the layer packages and the facade interface to be drawn, and those need more elements than the 7-component overview budget. The previous version is in `v1/`.

## How the view addresses the concern
- **Components and responsibilities:** each component carries a one-line responsibility under its name. Full text is in `inventory.json`.
- **Layers:** the four code packages (Boundary, Control, Entity, Database) are drawn as enclosing packages, so layer membership is part of the model. `ReportService` and `UserService` are visibly inside the Entity package.
- **Dependencies:** all are dashed «use» dependencies, pointing from dependent to dependency.
  - The GUI uses the facade through its «Services API» interface. Login bypasses it and uses its controller directly.
  - Controllers use the services, and the services use the entities and the persistence service.
  - Persistence reaches the external MySQL database over JDBC through Hibernate.
- **Separation and collaboration:**
  - The GUI never reaches persistence.
  - Data crosses layers as `Map<String,Object>`, not as entities, except the `ReportCategory` enum, which is used by the GUI and the controllers.
  - The note on the services shows the main separation issue: the domain-side services depend on persistence, so the domain is not persistence-ignorant.

`inventory.json` holds the evidence. `check_inventory.py`: 0 issues, 12 elements, 11 relations.

## Reviewer points (critique-1.json)
- **Accepted:**
  - Packages are now containers.
  - Dependencies are dashed «use».
  - Responsibilities are on the components.
  - The Map contract is stated in a note.
  - The facade's provided interface is drawn.
  - The controller to entity dependency is added.
  - MySQL is marked external and sits outside all packages.
  - The persistence-to-entity link is relabelled "mapped by config". It comes from `persistence.xml`, not from a code import.
  - The services are no longer called "domain services".
- **Not done, because the code contradicts it:** a required/provided interface for `PersistenceService`. It is a concrete class with no interface, so adding one would invent structure. It is listed under `omitted` in the inventory.
- **Partly done:** the system boundary around all internal packages is not drawn as an extra box, to keep within two nesting levels and the element budget. MySQL is outside every package instead.

## Omitted on purpose
Individual GUI, controller and entity classes; libraries (Swing, Hibernate); tests.

## Assumptions
- The facade's provided interface is its public method set (`SystemServicesController`). The code has no explicit Java interface for it.
- `NotificationController` is one of the use-case controllers. It is owned by the status-update controller, not by the facade.

## Check result
`puml-check` renders with no error. It reports 4 warnings, against 1 for `v1/`:
- aspect (portrait)
- two package-crossing edges
- bundled edges at the entities

These come from drawing real cross-layer dependencies inside package containers. Moving to left-to-right earlier made collisions worse. I kept this version because `v1/` loses the layer, interface and responsibility details the concern asks for. `check_inventory.py` is clean.
