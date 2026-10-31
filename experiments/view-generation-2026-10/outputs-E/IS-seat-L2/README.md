# Seat booking: UML component diagram (revision 1)

**Takeaway:** every booking request enters through the `makeReservation(ReservationRequestDTO)` contract on `LibraryFacade` and is decided in `ReservationManager`. New booking rules go there, and they must stay consistent with the availability logic that `StudyRoomManager` shows to students.

**Stakeholder:** software developer about to add booking rules. **Detail level:** balanced (given). The view has 12 elements (10 components and 2 interfaces) and 14 relations. Technology names are shown because the audience is engineering. The previous version is in `v1/`.

## How the view addresses the concern
- **Main components and responsibilities:**
  - The UIs (Swing wizard, REST controllers) are at the top.
  - `LibraryFacade` provides the booking interface.
  - `ReservationManager` holds the booking rules. The note lists the checks it makes today.
  - `FirstAvailableAssignment` provides the `AssignmentStrategy` interface.
  - `StudyRoomManager` answers the availability queries.
  - The reservation model and the study-room model hold the rule data and state.
  - The registries (JPA/MySQL) store everything.
  - `NotificationManager` is the observer notified after booking.
- **Interaction:**
  - Both UIs require the booking interface that `LibraryFacade` provides.
  - The facade delegates to the two managers.
  - `ReservationManager` requires `AssignmentStrategy` and depends on the models, the registries and the notifier.
  - `StudyRoomManager` depends on the study-room model and the registries.
  - Dashed arrows are dependencies. Ball-and-socket pairs show provided and required interfaces.
- **Parts affected:**
  - Blue marks the first places to edit: `ReservationManager` and the seat-assignment implementation.
  - Red marks what is also affected:
    - `StudyRoomManager`, because the wizard's seat lists and counts use the same availability rules.
    - The two models.
    - The registries, which hold the shared `occupiesSlot` rule (ACTIVE or CONFIRMED). The second note names it.
  - A rule that needs new request data changes `ReservationRequestDTO`, so it reaches both UI callers of the booking interface. That impact is now drawn in the view.
- **Tests:** the existing `MakeReservationTest` (`src/test/.../controller/MakeReservationTest.java`) covers `makeReservation`. It is not a component, so it is not drawn.

`inventory.json` lists the evidence (`file:line`) for every element and relation.

## Changes from v1, following the reviewer's critique
- **Added** `StudyRoomManager` -> study-room model, and marked `StudyRoomManager` and the registries as affected. Added the `occupiesSlot` and `Seat.isAvailable` note.
- **Added** the booking contract as an interface provided by `LibraryFacade` and required by both UIs. `AssignmentStrategy` is now an interface, provided by `FirstAvailableAssignment` and required by `ReservationManager`.
- **Changed** the solid arrows to dashed dependencies.
- **Removed** `NotificationManager` -> registries (reminder job, not booking) and reservation model -> `NotificationManager` (`ReservationManager` attaches the observer at runtime, so one edge remains).
- **Merged** `PersistenceManager` and MySQL into the registries box. It now names the three registry classes, so it reads as a grouping and not a deployable.
- **Kept as is:** the interface sits on `LibraryFacade` because that is where the DTO signature is declared. `ReservationManager` has the same signature, so the delegation is shown as a separate dependency.

## Omitted on purpose
DTO classes other than the contract signature, user management and factories, notification delivery (adapter, e-mail gateway, scheduler), exception handler, launcher, JPA utilities and tests.

## Assumptions
- The Swing wizard is drawn as one component, though it spans several screens.
- The registries are a grouping of three classes.

## Check results
- `check_inventory.py --level balanced`: 0 issues, 0 unbacked items, 12 elements, 14 relations.
- `puml-check --target 16:9`: the view renders with 1 edge crossing and 1 warning, `tiny-text` (smallest text about 8.3 px when scaled to 1200 px wide, against a 9 px limit). The diagram is wide because the two interface lollipops add a rank. I left it, since cutting more content would drop a point the reviewer asked for.
- A separate reviewer has not seen this revision.
