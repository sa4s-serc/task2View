# Seat booking: UML component diagram (balanced), revision 2

**Takeaway:** a booking enters through the Swing wizard or `ReservationController`, goes through `LibraryFacade` to `ReservationManager`, which orchestrates it. The existing rules live in the domain model (`StudyRoom`, `Area`, `Seat`, `Student`) and in `ReservationRegistry.occupiesSlot`. The seat choice is the `AssignmentStrategy` extension point.

Stakeholder: software developer about to add booking rules. Detail level: balanced (given). Wording uses class and technology names.
Files: `view.puml`, `view.png`, `inventory.json` (elements, relations, `file:line` evidence). The first version is in `v1/`.

## How the view answers the concern
- **Components and responsibilities:** each box has a one-line role. The domain model box and a note list the existing checks: `StudyRoom.isActive/isOpenOnDate`, `Area.getAvailableSeats`, `Seat.isAvailable`, `Student.hasActiveOrConfirmedReservation...`. `Registries` names the `occupiesSlot` rule.
- **Interaction:** dashed usage dependencies run caller to dependency. `ReservationManager` delegates checks to the domain model, which consults the Registries for occupancy. `ReservationManager` requires the `AssignmentStrategy` interface, realized by `FirstAvailableAssignment`. `StudyRoomManager` is shown on a separate branch: it serves the wizard's availability screens and is not called by `makeReservation`.
- **Affected parts:** blue = code that holds or applies booking rules (`ReservationManager`, the strategy, domain model, Registries). `StudyRoomManager`'s availability screens must reflect any new rule or the UI will offer seats that booking rejects. Faded callers (wizard, REST controller) must show rule errors, which are thrown as `IllegalArgumentException`/`IllegalStateException` and mapped to HTTP 400 by `RestExceptionHandler` (see the note).

## Changes after the review (critique-1.json)
All points were accepted; the code supports them (checked `StudyRoom.java:141`, `ReservationRegistry.java:120`, `LibraryFacade.java:82-101`, `RestExceptionHandler.java:19-22`).
- Removed `PersistenceManager`, the MySQL database and `NotificationServiceAdapter` (12 to 10 elements).
- Rule locations now include the domain model and Registries. The legend no longer says only `ReservationManager` holds rules.
- `facade -> roommgr` relabelled "availability queries", with evidence `LibraryFacade.java:82-101` and a note that booking does not call it.
- Notes added for the existing checks and for how rule errors surface.
- UML: dashed dependencies, no custom stereotypes (colour only, explained in the legend), `AssignmentStrategy` as an interface with a realization from `FirstAvailableAssignment`.

## Omitted on purpose
DTOs, `UserManager`/factories/authentication, cancel, check-in and expiry flows, `NotificationScheduler`, `PersistenceManager`, database, email adapter, `RestExceptionHandler` (a note only). Undrawn dependencies reported by the checker: domain with notif, strategy and the interface (they use `Seat`/`Student`); notif with registries; facade and roommgr with notif (reminders); `resmgr` with `FirstAvailableAssignment` (drawn through the interface). A detailed level would show the validation steps inside `ReservationManager`, best as a sequence view.

## Assumptions
"Registries" and "Reservation domain model" each merge several classes (members in `inventory.json`).

## Check result
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues, 7 notes (undrawn/unchecked as above).
- `puml-check`: renders, 10 nodes, 14 edges, ratio 1.81 vs 16:9. One warning remains: the realization line from `FirstAvailableAssignment` crosses the `AssignmentStrategy` label. v1 had an aspect warning (portrait), now fixed.
