# UML component view: seat booking (balanced)

**Takeaway:** a booking request enters through the REST boundary or the Swing wizard, passes the Library facade, and is processed by the Reservation manager. That manager applies the booking rules, uses the domain model to check availability, asks the assignment strategy for a seat, saves the reservation through the registries and persistence manager into MySQL, and notifies the student through the Notification manager and the email adapter.

Stakeholder: software developer about to add booking rules. Detail level: balanced, as given. Model kind: UML component diagram, built from `model.json` by `component_model.py`. Files: `view.puml`, `view.png`, `inventory.json` (evidence and members for every element).

## How the view answers the concern
- **Handling booking requests:** REST boundary (`ReservationController`), Swing booking wizard and Notification scheduler call the Library facade API. The facade delegates to Reservation manager.
- **Checking seat availability:** the Reservation manager calls the domain model (`Area.getAvailableSeats`, `Seat.isAvailable`), which looks up existing reservations via the registries.
- **Applying booking rules:** they sit in the Reservation manager (room active and open, area and seat valid, one reservation per student and slot, no free seat). Seat choice is in the Seat assignment strategy. **New rules most likely go in Reservation manager, the domain model or the strategy.**
- **Managing and storing reservations:** Reservation manager creates the reservation in state Active (domain model). Registries save and query it. Persistence manager runs JPA/Hibernate against the MySQL database.
- **External services:** Reservation manager attaches Notification manager as observer. Notification manager sends through the Notification service interface, implemented by the Email notification adapter (the gateway is a stub returning 200). The scheduler triggers reminders and reservation ends via the facade.
- **Affected parts:** a change to the Reservation manager's operations affects the facade and so the REST boundary, Swing wizard and scheduler. A change to domain rules or states also affects the registries and the Notification manager, which builds messages per state.

## Omitted on purpose
Room, user and factory managers, DTOs, cancel, check-in and history flows (same components). Undrawn code dependencies, listed in `inventory.json` `omitted`: Notification manager to domain and registries, domain to strategy, Swing to the email adapter (startup wiring).

## Assumptions
Entities and registries are grouped into two components (domain model, registries) although they share one package. Interface names are my naming of what each component offers.

## Check results
- `check_inventory.py --level balanced --graph`: 0 issues, with notes for undrawn dependencies and for the external elements, which have no members.
- `puml-check`: still reports warnings. In the middle row the interface labels (e.g. "Assignment strategy", "Availability and lifecycle rules", "Registry API") overlap and several edges cross. The generator offers no layout controls and I did not hand-edit the generated PlantUML, so this is not fixed. A reviewer should read those labels from the `.puml` or `inventory.json`.
