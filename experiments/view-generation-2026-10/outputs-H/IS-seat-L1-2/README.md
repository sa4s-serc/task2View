# UML package diagram: seat booking modules (IS-seat-L1-2, revision 1)

**Takeaway:** a booking request goes from the Swing wizard or REST API through the Library facade (all in package `controller`) to the Reservation manager, which picks a seat with the Seat assignment strategy if none was given, saves through the entity registries, and notifies through the Notification manager; DTOs carry the data across the boundary/controller line.

**Stakeholder:** software developer changing seat booking. **Detail level:** balanced (given).

## How it answers the concern
- *Main components:* the real Java packages `boundary` (Booking wizard (Swing), Booking REST API, Email notification adapter, Notification configuration), `controller` (Library facade, Reservation manager, Study room manager, Notification manager, «interface» Notification service, Seat assignment strategy), `dto` (Data transfer objects), `entity` (Reservation model and registries, Reservation state) and `database` (Persistence manager (JPA, Hibernate)). Facade and managers are classes inside `controller`.
- *Interaction:* dashed arrows are «use» dependencies (stated once in the legend), from dependent to dependency. The email adapter realizes Notification service (hollow arrow), and Notification configuration installs it into the Notification manager. Both UIs and the controller depend on the DTOs.

Files: `view.puml`, `view.png`, `inventory.json`; the first version is in `v1/`.

## Changes after the review (critique-1.json)
- Removed the invented layer packages (Presentation, Booking logic, Domain and data); containment now follows the code packages.
- Facade and managers are classes in `controller`; Notification service is an interface; the email adapter realizes it.
- Added the `dto` package, the Notification configuration wiring, and the Reservation state package.
- Moved the email adapter from "Presentation" into `boundary`; qualified the label "picks seat if none given".
- **Kept differently:** the reviewer asked for «use» on each label. I stated «use» once in the legend instead, because the labels made the view 2160 px wide (text shrank to under 9 px). Labels stay as short verbs.

## Omitted on purpose
Notification scheduler, controller.factory and user manager (not seat booking); the MySQL database, users and REST client (not packages; see component view IS-seat-L1). Undrawn dependencies: facade and Study room manager to Notification manager, Swing screens to Notification configuration, per-class DTO use by each manager, and Reservation to the state classes. A detailed level would add the classes inside the managers and the DTO classes.

## Assumptions
"Reservation model and registries" stands for `entity.*` as in IS-seat-L1 (it includes the state package, drawn separately here because ReservationManager depends on it). The container packages `boundary`, `controller`, `entity`, `database` have no member list, so the checker cannot verify them.

## Check results
check_inventory.py (balanced, graph): 0 issues, 12 notes (undrawn, unchecked). check_view.py: clean. check_consistency.py with IS-seat-L1: consistent. puml-check: renders; two warnings remain (a label on a container border and two edges sharing a trunk from the facade); the view is about 2000 px wide, wider than the 1600 px target, because of the cross-package dependencies.
