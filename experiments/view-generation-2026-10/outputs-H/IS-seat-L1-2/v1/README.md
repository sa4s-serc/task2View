# UML package diagram: seat booking modules (IS-seat-L1-2)

**Takeaway:** a booking request goes from the Swing wizard or REST API through the Library facade to the Reservation manager, which picks a seat with the Seat assignment strategy, saves through the Reservation model and registries, and notifies through the Notification manager.

**Stakeholder:** software developer who will modify seat booking. **Detail level:** balanced (given): the packages involved in booking, with the dependencies between them, in three layers (Presentation, Booking logic, Domain and data).

## How it answers the concern
- *Main components involved:* the nine packages in the diagram. Names and members match the earlier component view IS-seat-L1.
- *How they interact:* arrows are package dependencies, from dependent to dependency, with a short verb label. Both entry points use the Library facade. The facade delegates to the Reservation manager (create) and the Study room manager (rooms, time slots, seats). Both managers, the strategy and the Notification manager depend on the model; the model depends on persistence.

## Files
`view.puml`, `view.png`, `inventory.json` (elements, relations with `file:line`, concern details, omissions).

## Omitted on purpose
DTO package; the MySQL database, users and REST client (not packages; the component view shows them); librarian, authentication, monitoring, user manager and factories; notification scheduler/configuration and the entity state package. Undrawn code dependencies: Library facade to Notification manager, and Study room manager to Notification manager (secondary to the booking flow).
A detailed level would add the classes inside the Reservation manager and Study room manager.

## Assumptions
Package arrows are import/usage dependencies from the static graph; the "Email notification adapter" to "Notification manager" arrow stands for implementing the NotificationService interface that lives in the Notification manager package.

## Check results
check_inventory.py (balanced, with graph): 0 issues, 3 notes (undrawn x2, unchecked grouping layers). check_view.py: clean. check_consistency.py with IS-seat-L1: consistent. puml-check: renders, no crossings; two label-placement warnings remain (labels near a package border). Rendered with plantuml to view.png.
