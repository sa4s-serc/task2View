# Seat booking: UML component diagram (balanced)

**Takeaway:** a booking enters through the Swing wizard or the REST controller, goes through `LibraryFacade` to `ReservationManager`, which holds the booking rules and the seat choice, so new rules belong there (and in `AssignmentStrategy` for automatic seat choice).

Stakeholder: software developer about to add booking rules. Detail level: balanced (given). Wording uses class and technology names.

Files: `view.puml`, `view.png`, `inventory.json` (elements, relations and `file:line` evidence).

## How the view answers the concern
- **Main components and responsibilities:** each box carries a one-line role: `LibraryFacade` (entry), `ReservationManager` (validation, seat selection, saving, notifying), `AssignmentStrategy` (automatic seat pick), `StudyRoomManager` (availability), the domain model (Seat/Area availability, per-student checks, reservation states), registries, `PersistenceManager`, `NotificationManager`.
- **Interaction:** arrows run caller to dependency with the operation as label, from both UIs down to the MySQL database. `ReservationManager` calls the strategy, the domain model, the registries and the notifier.
- **Affected parts:** blue = where rules live (`ReservationManager`, `AssignmentStrategy`). Plain components are collaborators that may need changes (domain model for new checks, `NotificationManager` for new messages). Faded components (`Swing` wizard, `ReservationController`) are callers that may need to show new rule errors. Rule failures are `IllegalArgumentException`/`IllegalStateException` thrown from `makeReservation`.

## Omitted on purpose
DTOs, `UserManager`/factories/authentication, cancel, check-in and expiry flows, `NotificationScheduler`. Dependencies not drawn (listed by the checker as undrawn): domain<->notif, domain<->strategy (both use `Seat`/`Student`), facade->notif and roommgr->notif (reminders), notif->registries.
A higher level would drop the registry/persistence chain; a detailed one would show the validation steps inside `ReservationManager` (a sequence view would show the call order).

## Assumptions
- "Registries" and "Reservation domain model" merge several classes into one element each.
- `domain --> reg` is drawn from `Student.java:43` (reservation lookup).

## Check result
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues, 6 notes (undrawn/unchecked as above).
- `puml-check`: renders, 12 nodes, 14 edges, no overlaps; one remaining `aspect` warning (portrait 0.78 vs 16:9) because the flow is a layered chain; left-to-right was tried and was worse (ratio 4.2, tiny text). The note on `ReservationManager` was removed to clear an edge-through-node warning.
