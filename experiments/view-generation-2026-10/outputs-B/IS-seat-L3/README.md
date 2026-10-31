# Component view: seat booking (IS-seat-L3)

**Takeaway:** every booking enters through `LibraryFacade`; `ReservationManager` validates the request and applies the booking rules, with seat availability checked in the domain entities and seat choice delegated to `AssignmentStrategy`. Reservations are stored through `ReservationRegistry` and `PersistenceManager` into MySQL, and `NotificationManager` sends notices through an adapter to an email gateway.

Stakeholder: software developer adding booking rules. Detail level: detailed for the booking path (15 components, within the 20 budget). Technology names are included because the audience is engineering. Yellow marks the components most likely to change.

## How the view answers the concern
- **Handles booking requests:** Swing Client and REST Controllers call Library Facade, which calls Reservation Manager (`makeReservation`).
- **Checks seat availability:** Reservation Manager calls Domain Entities (`Area.getAvailableSeats`, `Seat.isAvailable`), which query Reservation Registry for existing bookings and Study Room Registry for the area's seats. Study Room Manager serves the availability queries used by the UI.
- **Applies booking rules:** Reservation Manager (room active and open, slot not past, one booking per student and slot, seat in area, locked section) and Assignment Strategy (automatic seat choice).
- **Manages and stores reservations:** Reservation Manager, Domain Entities (Reservation and its states), Reservation Registry, Persistence Manager, MySQL.
- **External services:** Notification Manager → Notification Adapter → External Email Gateway (a stub).
- **Modify / affected:** Reservation Manager, Assignment Strategy and Domain Entities are the likely change points. Affected: Library Facade (if the API changes), Notification Manager, the registries, and the Swing and REST callers.

## Inventory (element → evidence)
Paths are under `JavaProject/src/main/java/it/unina/reservations/`.
- Swing Client → `boundary/Swing/ReservationSummary.java:100`
- REST Controllers → `boundary/SpringBoot/ReservationController.java:21-48`
- Notification Scheduler → `boundary/NotificationScheduler.java:15-28`
- Library Facade → `controller/LibraryFacade.java:117-164`
- Reservation Manager → `controller/ReservationManager.java:65-102`
- Study Room Manager → `controller/StudyRoomManager.java` (`getRoomDetail`)
- Assignment Strategy → `controller/strategy/AssignmentStrategy.java`, `ReservationManager.java:400`
- Notification Manager → `controller/NotificationManager.java:15-66`
- Domain Entities → `entity/Area.java:49`, `entity/Seat.java:44`, `entity/Reservation.java`
- Reservation Registry and Study Room Registry → `entity/ReservationRegistry.java:33`, `ReservationManager.java:28-30`
- Persistence Manager → `database/PersistenceManager.java`
- MySQL reservationsdb → `src/main/resources/META-INF/persistence.xml:21`
- Notification Adapter and External Email Gateway → `boundary/NotificationServiceAdapter.java`, `boundary/ExternalEmailGateway.java:12`
- Wiring of the adapter into the manager → `boundary/NotificationConfiguration.java:17`

## Omitted on purpose
DTOs, User and Librarian components, the Observer and ReservationState classes (shown as part of Domain Entities), the static web front end, `UserRegistry` and `NotificationConfiguration`. The cancel, check-in and expiry flows are shown only as the facade's inbound calls. A sequence view would show the order of the checks.

## Assumptions
- The Study Room Manager → Study Room Registry edge is based on `getRoomDetail` (`StudyRoomManager.java:264-284`); I did not trace its other methods.
- The web front end (`static/app.js`) probably calls the REST controllers, but I did not confirm it and left it out.

## Check result
`puml-check` reports 7 warnings: edges crossing package borders, one label on a border, and edges bundled out of Reservation Manager. The aspect ratio is 1.39 against the 1.78 target. A revision with a reordering and a hidden link also gave 7, so I reverted it. The single change after reading the image was replacing the in-diagram note with a legend, which went from 6 to 7 warnings. I kept the legend because the diagram reads the same either way and a legend is the proper notation. The warnings are layout issues, not content issues.
