# UML component diagram: seat booking (revision 1)

**Takeaway:** a booking request reaches `ReservationManager` from the web client (through `ReservationController`) or the Swing client (in-process, through `LibraryFacade`). `ReservationManager` resolves the request, checks rules and availability with the domain model, saves the reservation, then attaches `NotificationManager` as an Observer. Email goes out through the `NotificationService` interface to the external gateway.

Stakeholder: software developer about to add booking rules. Detail level: **balanced** (given); 12 elements, interfaces included. A *detailed* level would add each validation step and the reservation state classes.

## How the view answers the concern
- **Handling booking requests:** Web client, Swing client, ReservationController, ReservationManager. The two clients take different paths.
- **Checking seat availability:** ReservationManager (step 2) calls the domain model. `Area.getAvailableSeats` lists seats from the Room and User registries, and `Seat.isAvailable` reads occupancy from ReservationRegistry.
- **Applying booking rules:** two places. ReservationManager holds the request checks (room, area, slot, seat) and the seat strategy. The domain model holds the student uniqueness rule (`Student.hasActiveOrConfirmedReservationForDateAndSlot`) and seat occupancy. The note says a new rule may go in either.
- **Managing and storing reservations:** ReservationManager (step 3) saves through ReservationRegistry, which persists via PersistenceManager (JPA to MySQL).
- **External services:** ReservationManager attaches NotificationManager (step 4). The domain model notifies through the `Observer` interface. NotificationManager requires `NotificationService`, which NotificationServiceAdapter implements, and the adapter calls the external ExternalEmailGateway (a stub).
- **What to change and what is affected:** blue is the main change point. Red marks components likely affected by a new rule: domain model (rule methods), ReservationRegistry (new queries), ReservationController (request fields, error texts) and NotificationManager (new messages).

Evidence: `inventory.json`. `check_inventory.py --level balanced`: 0 issues. `puml-check`: 1 warning (an edge passes over the label "notifies"), ratio 1.72 against 1.78 target, no other issues.

## Changes from v1 (kept in `v1/`) and why
- Notification boundary now uses interfaces `Observer` and `NotificationService`; the adapter and the external gateway are separate. The direct domain model to NotificationManager edge is gone.
- Added ReservationManager to NotificationManager (booking confirmation), and domain model to Room and User registries (`Area.getAvailableSeats`).
- Dropped cancel notice, reminder and expiry edges; NotificationScheduler removed (not booking flow, and needed to stay within 12 elements).
- Note corrected: uniqueness sits in the domain model. Booking steps are numbered 1 to 4 in ReservationManager's flow order. Affected components are marked red.
- Web and Swing clients split.

## Reviewer points not applied fully
- **LibraryFacade and PersistenceManager boxes:** the reviewer did not ask to keep them, but adding the interfaces, the split clients and the gateway pushed the count to 14 (budget 12). Both are pass-through or infrastructure, so I named them in the labels of `ReservationManager` and the registries instead of drawing them. The ReservationController and Swing edges therefore point to ReservationManager; in code they go through LibraryFacade (`LibraryFacade.java:117-119`).
- **Step order:** the numbers 1 to 4 follow `makeReservation` for the resolve, rules and availability, save and notify phases. In the code, rule checks and availability (`validateUniqueness`, `availableSeats`) run before the save in a synchronized block, so step 2 groups several calls.
- **Room and User registries, domain model:** kept as grouped components with their class names listed, as the reviewer allowed.

## Omitted on purpose
StudyRoomManager, UserManager and other controllers; NotificationScheduler; cancel and reminder flows; AssignmentStrategy as its own box (folded into ReservationManager); DTOs, state classes, factories, JPA utilities.

## Assumptions
- Web client path from `reservation.html:385`; Swing path from `ReservationSummary.java:99-100`.
- The email gateway is a stub that always returns 200.
