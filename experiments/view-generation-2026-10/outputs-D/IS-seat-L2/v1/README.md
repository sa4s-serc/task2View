# Seat booking: UML component diagram

**Takeaway:** a booking request flows from the web or Swing UI through `LibraryFacade` to `ReservationManager`, where the booking rules live. Those rules lean on the domain model, the seat-assignment strategy and the registries.

Stakeholder: software developer about to add booking rules. Detail level: **detailed** for the booking path only (14 components), because the developer is about to change this area. Wording uses code and technology names.

## How the concern is answered
- **Main components and responsibilities:** each box names its role. Boxes cover the two UIs, REST controllers, facade, `ReservationManager`, `AssignmentStrategy`, `StudyRoomManager`, the domain model, notification, registries and persistence.
- **Interactions:** labelled arrows run from caller to dependency. The path is UI → facade → manager → domain and registries → JPA → MySQL.
- **Affected parts:** blue = likely edit points. These are `ReservationManager` (the existing checks are in `makeReservation`), `AssignmentStrategy`, and the domain model (`Seat.isAvailable`, `Student.hasActiveOrConfirmedReservationForDateAndSlot`, `Area.getAvailableSeats`). Rules that change availability also touch `StudyRoomManager`, which shows free-seat counts in the wizard, and the registries. UIs and the facade change only if the request shape changes. Grey parts are peripheral.

Details: `inventory.json` (`check_inventory.py`: clean with detail level "detailed"; at "balanced" it reported 14 elements over the budget of 12).

## Omitted on purpose
DTOs, `UserManager` and factories, `RestExceptionHandler`, and the cancel, check-in and monitoring flows. These are glue or outside make-reservation.

## Assumptions
- The domain model, registries and the three notification classes are each merged into one component. Separate classes exist in the code.
- `NotificationServiceAdapter` is wired to `NotificationManager` in `NotificationConfiguration`. `NotificationManager` also reaches reservations through the Observer interface, which the view does not draw.
- `StudyRoomManager`'s dependency on `NotificationManager` (room deletion) is omitted.

## Check result
`puml-check`: renders, 0 overlaps, 1 crossing. Two warnings remain: aspect (ratio 0.99, a tall layout) and one edge label ('counts free seats') crossed by its own edge. I accepted both after trying left-to-right, which was worse (ratio 3.98, tiny text).
