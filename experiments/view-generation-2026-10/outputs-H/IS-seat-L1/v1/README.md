# Seat booking: component view (UML component diagram)

**Takeaway:** a seat booking enters through the Swing wizard or the REST API, passes the Library facade to the Reservation manager, which validates it, uses the Study room manager data, picks a seat through the assignment strategy, saves via the registries and persistence layer to MySQL, and notifies the student by email.

Stakeholder: software developer who will modify seat booking. Detail level: **balanced** (as given): the components involved and their interfaces, no classes. A *detailed* level would add the booking validation steps, the reservation state classes and DTOs; an *overview* would drop the interfaces.

## How the view answers the concern
- **Main components involved:** Booking wizard (Swing), Reservation REST API, Library facade, Reservation manager, Study room manager, Seat assignment strategy, Notification manager, Reservation model and registries, Persistence manager, Email notification adapter, Reservation database. Grouped as Presentation, Booking logic, Domain and data.
- **How they interact:** arrows show the call direction (labelled verbs, `«use»` for interface use); lollipops show what Library facade (booking operations), the strategy (seat assignment), the email adapter (notification service) and the database (JPA) offer.

Evidence for every element and relation is in `inventory.json`. `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (9 notes: undrawn minor dependencies and unchecked non-code elements). `check_view.py`: clean. `puml-check`: renders; 2 cosmetic label-on-border warnings remain.

## Omitted on purpose
Librarian screens, user/authentication, monitoring and cancel/check-in flows; DTOs, factories, wizard helper classes; minor dependencies (facade to notification manager, strategy/notification manager to model, study room manager to notification manager). Dependencies drawn through an interface are not matched one-to-one by the graph, so the facade/wizard/REST edges appear as "undrawn" notes.

## Assumptions
- The Reservation manager reads rooms and seats via the registries directly, not through the Study room manager (no code dependency), so no such edge is drawn; the Study room manager serves the wizard/REST availability listing via the facade.
- Student actor: the wizard is the student's booking path (ReservationSummary); the REST API consumer is assumed to be a student client.
