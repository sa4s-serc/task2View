# Component view: Municipal report management application

**Takeaway:** the application is four stacked components (screens, use-case controllers, domain entities and services, JPA persistence). Screens enter Control through two interfaces (the controller facade and the login controller), and only the domain talks to persistence.
**Stakeholder:** software architect; **detail level:** overview (as given). A balanced level would add the individual controllers, services and entities.

Files: `view.puml`, `view.png`, `inventory.json` (elements, relations, evidence). Names match view GR10-Q1. The first version is kept in `v1/`.

## How the concern is addressed
- Components and responsibilities: four boxes with a one-line responsibility note each (also in `inventory.json`).
- Layers: presentation (Boundary), application (Control), domain (Entity), persistence (Database), top to bottom.
- Dependencies: arrows go downward only. Boundary uses the controller facade and, for login, the login controller directly (`Boundary/UserLoginGUI.java:3,111`). Boundary also uses the domain's report category enum. Domain and persistence use the external JPA API («library»).
- Separation: UI reaches logic only through Control (facade or login controller). The note on Entity states that domain entities and services live together and that the services call PersistenceService directly, so domain and persistence are coupled.
- Collaboration: the note on Control lists the use cases the facade exposes (register, create report, review, details, status update, internal note, monitoring). Each use case runs screen, controller, domain service, PersistenceService. Login follows the same chain through the login controller.

## Omitted
Classes, forms, enums; the MySQL database (outside the code, configured in `persistence.xml`); users (use case view); a sequence of each use case (sequence view).

## Assumptions
Interface names group the public classes of each package. "Report and user services" is a logical interface: the code has two concrete classes (ReportService, UserService) and no Java interface.

## Revision after review (v1 to v2)
- Added the login controller interface and the direct Boundary-to-Control login dependency. The reviewer was right: v1 claimed the facade is the only entry.
- Added responsibility notes, the facade use-case list, and the Entity coupling note.
- jakarta.persistence now uses «library» instead of the hidden muted style; «use» labels carry no extra text.
- Marked the services interface as logical.
- Not changed: the reviewer's level judgement (right), so no components were added or removed. The tall layout stays; lollipop edges still touch interface names.

## Check results
puml-check: 4 edge-through-text warnings remain (provider lines touching interface names; render is legible). check_inventory: 0 issues (4 notes: dependencies through interfaces). check_view: clean. check_consistency with GR10-Q1: consistent.
