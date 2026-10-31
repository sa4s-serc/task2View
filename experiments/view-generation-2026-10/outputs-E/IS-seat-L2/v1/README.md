# Seat booking: UML component diagram

**Takeaway:** every booking request enters through `LibraryFacade` and is decided in `ReservationManager`, which uses the study-room model, the reservation model and `AssignmentStrategy`. New booking rules belong there.

**Stakeholder:** software developer about to add booking rules. **Detail level:** balanced (given). The view covers one feature, with 12 components and 15 relations. Technology names are shown because the audience is engineering.

## How the view addresses the concern
- **Main components and responsibilities:** each box names one component and its role. The two UIs (Swing wizard, REST controllers) sit at the top. Below them are the facade, the managers, the two domain models, the registries, JPA persistence and MySQL.
- **Interaction:** the arrows run from caller to callee. Both UIs call the facade, which calls `ReservationManager` (booking) or `StudyRoomManager` (availability queries). `ReservationManager` calls the models, the strategy, the registries and the notifier. The registries delegate to `PersistenceManager`, then to the database.
- **Parts affected by the change:** blue marks the first places to edit: `ReservationManager`, which holds today's checks (see the note), and `AssignmentStrategy`, for seat choice. Red marks the models that carry rule data and state: `Reservation`/`Student` (uniqueness, check-in tolerance, states) and `StudyRoom`/`Area`/`Seat`/`TimeSlot` (opening days, slots, seat availability). A new rule that needs new input also reaches the facade, the REST controller and the Swing wizard, because the request DTO passes through them. Treat that as an inference, not something the diagram shows.

`inventory.json` lists the evidence (`file:line`) for every element and relation.

## Omitted on purpose
DTOs, user management and factories, notification delivery (adapter, e-mail gateway, scheduler), exception handler, launcher and JPA utilities.

## Assumptions
- The three registries are merged into one component. They share one pattern and are separate classes.
- `AssignmentStrategy` is drawn as a component. In the code it is an interface with one implementation, `FirstAvailableAssignment`.
- The Swing wizard is drawn as one component. It spans several screens.

## Check results
- `check_inventory.py --level balanced`: 0 issues, 0 unbacked items, 12 elements, 15 relations.
- `puml-check`, final run: renders with 0 crossings. 3 warnings remain.
  - `tiny-text`: the diagram is tall, so it is small when scaled to a letter page.
  - `edge-through-node` and `text-on-node` on the `selectSeat` edge, and `edge-through-own-label` on the `queries availability` edge. In the PNG neither edge overlaps another box or label.
  - Several layout tweaks swapped one warning for another, so I kept the version with the fewest warnings.
- Not reviewed by a separate reviewer.

A different detail level would add the controller/service/repository chain inside `ReservationManager` (overview: less; detailed: more).
