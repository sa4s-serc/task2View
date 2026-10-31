# Component view: seat booking (IS-seat-L1)

Files: `view.puml` (source), `view.png` (render).

**Takeaway:** every booking request, from the Swing wizard or the web page, enters `LibraryFacade`. The facade delegates to `ReservationManager`, which validates the request, picks the seat, saves the reservation and notifies the student.

**Stakeholder / detail:** software developer about to modify seat booking. The view is *detailed* for the booking path and shows 15 components, within the budget of 20. Wording is technical (Spring REST, JPA/Hibernate, Observer).

## How the concern is addressed
- **Main components involved:** four layers are drawn.
  - Boundary: Swing wizard, web page, `ReservationController`.
  - Controller: `LibraryFacade`, `ReservationManager`, `AssignmentStrategy`, `NotificationManager`.
  - Entity: domain model, three registries, `PersistenceManager`.
  - Notification delivery: adapter and email gateway.

  `ReservationManager` is highlighted as the component to modify.
- **How they interact (control flow):** each edge is a call, labelled with the operation or protocol. The flow is UI/REST → facade → `ReservationManager`. From there it resolves room, area, seat and student through the registries, checks seat availability on the domain model, and selects a seat via the strategy when the seat is automatic (id 0). It then saves the reservation and notifies via the Observer. `NotificationScheduler` is the other entry point into the facade, via `manageReservationEnd()`.
- **Structural and behavioural aspects:** components and dependencies give the structure. Labelled call directions give the behaviour. Call order is not drawn; a sequence view would show it.

## Inventory (element → evidence)
| Element | Evidence |
|---|---|
| Swing Booking Wizard | `boundary/Swing/ReservationSummary.java:100` |
| Web Booking Page | `static/reservation.html:385` (`POST /reservations/create`), `static/app.js:2,10` |
| ReservationController | `boundary/SpringBoot/ReservationController.java:21-38` |
| LibraryFacade | `controller/LibraryFacade.java` (`makeReservation`, `manageReservationEnd`) |
| ReservationManager | `controller/ReservationManager.java:61` (`makeReservation`) |
| AssignmentStrategy / FirstAvailableAssignment | `controller/strategy/*`, `ReservationManager.java:29,258` |
| NotificationManager | `ReservationManager.java:114-117`, `controller/NotificationManager.java:15,40` |
| Domain model | `ReservationManager.java:92,100,122` (`Area.getAvailableSeats`, `Seat.isAvailable`, `Student`, `Reservation`) |
| ReservationRegistry / StudyRoomRegistry / UserRegistry | `ReservationManager.java:25-27` |
| PersistenceManager | `entity/ReservationRegistry.java:17-20`, `entity/StudyRoomRegistry.java:17-20`; Hibernate/MySQL in `META-INF/persistence.xml:8,21` |
| NotificationServiceAdapter, ExternalEmailGateway | `boundary/NotificationConfiguration.java:17`, `boundary/NotificationServiceAdapter.java:12` |
| NotificationScheduler | `boundary/NotificationScheduler.java:19-30` |

## Omitted on purpose
- DTOs and `RestExceptionHandler`.
- The other Swing wizard steps.
- `StudyRoomManager` and `StudyRoomController`, which serve the room, slot and seat queries before booking. They are not on the `makeReservation` path.
- Other managers (`UserManager`, user factories).
- Reservation state classes.
- The MySQL database, which is only named in the legend.

## Assumptions
- The Swing wizard is represented by `ReservationSummary`, the only step that calls `makeReservation`. The earlier wizard steps are folded into it.
- The three registries and the domain classes are grouped as the Entity layer, as the package layout does.
- The Hibernate/MySQL link comes from `persistence.xml`. I did not check how `PersistenceManager` uses it.

## Check result
- `puml-check`: 0 overlap, edge or text issues. The one remaining warning is `aspect` (the view is taller than 16:9), accepted because the view is meant as a page, not a slide.
- Image review changes:
  - Removed the `StudyRoomManager` edge, because it is off the booking path.
  - Lightened the `ReservationManager` fill so its text is readable.
  - Gave the `ReservationManager` edges separate ranks so their labels don't crowd.
