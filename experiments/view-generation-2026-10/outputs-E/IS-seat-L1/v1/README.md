# UML component diagram: seat booking (overview)

**Takeaway:** a booking request enters through the Swing wizard or the REST controllers, goes through `LibraryFacade` to `ReservationManager`, which validates it, picks the seat, saves the reservation through the registries and notifies the student through `Notification`.

- Stakeholder: software developer about to modify seat booking.
- Detail level: overview, as given. A balanced or detailed level would add the validation steps inside `ReservationManager`, the seat-assignment strategy and the reservation state classes.
- Files: `view.puml`, `view.png`, `inventory.json` (elements, relations and `file:line` evidence).

## How the view answers the concern
- **Main components involved:** seven components, from the two entry points (`Swing booking wizard`, `REST controllers`) to `Registries and domain model`. `ReservationManager` and `LibraryFacade` are highlighted as the places to change.
- **How they interact:** the arrows show the control flow of `makeReservation`.
  - Both entry points call `LibraryFacade`, which delegates to `ReservationManager`.
  - `ReservationManager` reads and writes through the registries and then calls `Notification` via `notifyObservers`.
  - The wizard's seat and area screens call `getRoomDetail` through the facade to `StudyRoomManager`, which queries seats in the registries.
- **Structural and behavioural aspects:** the structure is the component boxes and their dependencies. The behaviour is the verb on each edge, read from entry point to storage.

## Omitted on purpose
- The static web pages (`reservation.html`, `app.js`). They POST to the REST controllers and are not drawn.
- The student actor. Users are not components and would exceed the 7-component budget.
- The assignment strategy, the state classes, DTOs, factories, `UserManager`, the notification scheduler and the other controllers.

## Assumptions
- Persistence is JPA to MySQL, from `persistence.xml`. The wizard-to-registries path goes through the managers only.
- Check-in and cancel go through the same entry points but are outside this booking view.

## Check results
- `check_inventory.py --level overview`: 0 issues, 7 elements, 7 relations.
- `puml-check --target letter`: OK, 0 crossings. The only message is an info line that the diagram fits its slot unscaled.
- Revisions: the first render with left-to-right direction was too wide, so I switched to top-to-bottom. I then removed the actor to meet the budget.
