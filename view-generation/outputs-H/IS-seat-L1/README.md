# Seat booking: component view (UML component diagram), revision 1

**Takeaway:** a seat booking enters through the Swing wizard or the REST API, passes the Library facade to the Reservation manager, which validates it, picks a seat through the assignment strategy, saves via the registries and the Hibernate persistence layer (JDBC to MySQL), and triggers the student's email through the Observer the model notifies.

Stakeholder: software developer who will modify seat booking. Detail level: **balanced** (as given). A *detailed* level would add the validation steps, reservation states and DTOs; an *overview* would drop the interfaces.

## How the view answers the concern
- **Main components:** Booking wizard (Swing), Booking REST API (reservation create plus room/time-slot/detail availability endpoints), Library facade, Reservation manager, Study room manager, Seat assignment strategy, Notification manager, Reservation model and registries, Persistence manager (JPA, Hibernate), Email notification adapter, Reservation database (MySQL), in layers Presentation, Booking logic, Domain and data.
- **Interactions:** labelled arrows give call direction. The "Booking operations" interface carries a note naming the four facade operations booking uses. Notification runs through the Observer: the Reservation manager attaches the Notification manager when saving, and the model notifies it through the "Observer" interface.

Evidence is in `inventory.json`. Final `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues (10 notes: undrawn minor dependencies, unchecked non-code elements). `check_view.py`: clean. `puml-check`: renders, 4 layout warnings (2 edges crossing a container label, 2 bundled edges at interfaces); the first version had 2, but this one removes the incorrect edges and adds the Observer path, so I kept it.

## Changes after review (previous version in `v1/`)
- Persistence tail corrected: the database no longer "provides JPA". Persistence manager (JPA, Hibernate) reaches MySQL over JDBC (persistence.xml:8,24).
- Notification trigger corrected: the direct "notifies student" edge is replaced by "saves, attaches observer" plus model to Notification manager via the Observer interface (ReservationManager.java:120-122, Reservation.java:182, NotificationManager.java:15,40).
- Booking operations named in a note on the interface.
- REST component renamed "Booking REST API" with StudyRoomController availability endpoints added to its description and evidence.
- Student no longer uses the REST API; an external "REST client" actor does.

Not adopted: collapsing the persistence tail further was optional; I kept the JPA/Hibernate label inside the Persistence manager and removed the JPA interface, which collapses it to two elements.

## Omitted on purpose
Librarian screens, user/authentication, monitoring, cancel/check-in; DTOs, factories, wizard helpers; minor dependencies (facade to notification manager, strategy to model, study room manager to notification manager). Edges drawn through interfaces appear as "undrawn" notes because the graph checker matches direct dependencies.

## Assumptions
- The Reservation manager reads rooms and seats through the registries directly, so there is no edge to the Study room manager.
- The REST client is an unspecified HTTP consumer.
