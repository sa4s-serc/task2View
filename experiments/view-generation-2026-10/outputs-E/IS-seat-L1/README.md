# UML component diagram: seat booking (overview)

**Takeaway:** a booking request enters through the Swing wizard or the web client with its REST controllers, goes through `LibraryFacade` to `ReservationManager`, which validates it, picks the seat, saves the reservation through the registries and notifies the student through `Notification`.

- Stakeholder: software developer about to modify seat booking.
- Detail level: overview, as given. A balanced or detailed level would add the validation steps inside `ReservationManager`, the seat-assignment strategy and the reservation state classes.
- Files: `view.puml`, `view.png`, `inventory.json` (elements, relations and `file:line` evidence).

## How the view answers the concern
- **Main components involved:** seven components, from the two entry points (`Swing booking wizard`, `Web client + REST controllers`) to `Registries and domain model`. `ReservationManager` and `LibraryFacade` are highlighted as the places to change.
- **How they interact:** the arrows show the control flow of `makeReservation`.
  - Both entry points call `LibraryFacade`, which delegates to `ReservationManager`.
  - `ReservationManager` checks free seats and picks the seat itself when booking. It reads and writes through the registries, then attaches `Notification` as an observer of the `Reservation`, and the `Reservation` notifies it.
  - Both entry points also call the facade for rooms, time slots and room detail. These go to `StudyRoomManager`, which serves the browsing screens and queries seats in the registries. To change seat selection at booking time, edit `ReservationManager`, not `StudyRoomManager`.
  - Calls are drawn as dashed dependencies, as UML expects between components.
- **Structural and behavioural aspects:** the structure is the component boxes and their dependencies. The behaviour is the verb on each edge, read from entry point to storage.

## Omitted on purpose
- The web pages are merged into the REST element rather than drawn separately.
- The student actor. Users are not components and would exceed the 7-component budget.
- The assignment strategy, the state classes, DTOs, factories, `UserManager`, the notification scheduler and the other controllers.

## Assumptions
- Persistence is JPA to MySQL, from `persistence.xml`. The wizard-to-registries path goes through the managers only.
- Check-in and cancel go through the same entry points but are outside this booking view.

## Check results
- `check_inventory.py --level overview`: 0 issues, 7 elements, 7 relations.
- `puml-check --target letter`: OK, 0 crossings, no warnings.

## Revision after review (v1 is kept in `v1/`)
- Entry points: the web client is folded into the REST element, which now covers `ReservationController` and `StudyRoomController`. Both entry points carry the same availability calls as the Swing wizard.
- Notification edge: relabelled to "attach observer; Reservation notifies", because `notifyObservers` is a method of `Reservation`.
- Roles: `ReservationManager` is labelled as the place that checks free seats and picks the seat. `StudyRoomManager` is labelled as availability for the browsing screens.
- UML: solid arrows became dashed dependencies, and the `<<accent>>` stereotype was replaced by a fill colour explained in a legend.
- Not adopted: modelling `LibraryFacade` as a provided interface. The code has no interface type for it, and dashed dependencies already express the calls.
