# UML package diagram: modules that depend on persisted report data

**Takeaway:** the persisted entities are reached only through the data services (`ReportService`, `UserService`) and the persistence access; screens and controllers depend on them indirectly, and only `ReportCategory` is used directly.
**Stakeholder:** database engineer. **Detail level:** balanced (given), so packages of the four layers are drawn, not classes.

## How the concern is addressed
- *Which parts depend on persisted information:* Screens → Use-case controllers → Data services → Persistence access/Persisted entities. A schema change therefore reaches the data services first; screens and controllers only see the `ReportCategory` enum directly.
- *Main persisted entities:* the "Persisted entities" package lists users, citizens, operators, credentials, reports, locations, categories, status updates, internal notes and notifications.
- *Lifecycle information:* "Report status states" shows that the state classes are rebuilt from the stored status text and are not persisted.
- *Entity relationships:* not drawn here; the class view `GR10-Q3` shows them (foreign keys, embeddings).

Details are in `inventory.json`. `check_inventory.py --level balanced --graph`: 0 issues. `check_view.py`: clean. `check_consistency.py` with GR10-Q3: consistent. `puml-check`: OK, no warnings.

## Omitted
Individual GUI/controller classes, generic persistence-access-to-entity dependency (the persistence unit lists the entities in `persistence.xml`), build files and tests. A detailed level would split the controllers and show each service operation.

## Assumptions
Packages are groupings of classes: `Entity` is split into three packages by role (the code keeps them in one Java package). The MySQL database is named in a note, not drawn.
