# Component view: Municipal report management application

**Takeaway:** the application is four strictly stacked components (screens, use-case controllers, domain entities and services, JPA persistence) in which each layer is reached through one interface and only the domain talks to persistence.
**Stakeholder:** software architect; **detail level:** overview (as given). A balanced level would add the individual controllers, services and entities.

Files: `view.puml`, `view.png`, `inventory.json` (elements, relations, evidence). Names match view GR10-Q1.

## How the concern is addressed
- Components and responsibilities: the four boxes, named as in GR10-Q1; responsibilities in `inventory.json`.
- Layers: presentation (Boundary), application (Control), domain (Entity), persistence (Database), top to bottom.
- Dependencies: arrows go downward only; screens also use the domain's report category enum; domain and persistence use the external JPA API.
- Separation: UI only enters logic via the controller facade; domain services call the persistence service. Note: the domain layer holds services that call persistence directly, so domain and persistence are not independent (an observation for evolution planning).
- Collaboration: a screen calls the facade, a controller calls domain services, which store entities through PersistenceService.

## Omitted
Classes, forms, enums; the MySQL database (outside the code, per `persistence.xml`); users (use case view).

## Assumptions
Interface names ("Controller facade", "Report and user services", "PersistenceService") group the public classes of each package.

## Check results
puml-check: 3 label warnings remain (interface lines touching interface names; render is legible, tall layout). check_inventory: 0 issues (4 notes: dependencies pass through interfaces). check_view: clean. check_consistency: consistent.
