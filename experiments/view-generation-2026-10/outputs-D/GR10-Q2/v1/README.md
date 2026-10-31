# Deployment view: Municipal Report Management System

**Takeaway:** the system is a standalone Java 23 Swing client with no server tier. It talks directly over JDBC/TCP (port 3306) to a MySQL schema `reports_db`, so a new environment needs a JVM, the Maven-built artifact and a prepared MySQL database.

**Stakeholder:** DevOps engineer deploying to a new environment. **Detail level:** balanced. The concern is about nodes and runtime links, so only nodes, execution environments, artifacts and one communication path are drawn. Wording is technical (protocols, versions).

Files: `view.puml`, `view.png`, `inventory.json` (evidence for each element and relation).

## How the concern is addressed
- **Runtime environments and artifacts:** the Java 23 JVM, the application artifact, the Hibernate and Connector/J libraries, `persistence.xml` and the MySQL server (`pom.xml`, `README.md`).
- **Where it runs and where data lives:** the Swing app runs on the user's workstation. Data lives in schema `reports_db` on the MySQL host, which is `127.0.0.1` by default.
- **How runtime elements communicate:** the only network path is JDBC over TCP on port 3306 from the JVM to MySQL. The GUI, controllers and persistence layer run in one process.
- **Technologies and dependencies between app and database:**
  - Hibernate ORM 6.6.50 is the JPA provider.
  - MySQL Connector/J 9.4.0 is the JDBC driver.
  - `persistence.xml` holds the URL, user and `hbm2ddl.auto=update`, so the app creates and updates the tables.
  - The database and its user must be created by hand (see the note in the diagram).

## Omitted on purpose
The Boundary/Control/Entity/Database layers (a component view would show them), JUnit tests (test scope), and the IntelliJ forms runtime (a library, not a node).

## Assumptions
- The workstation and the database host as separate nodes are assumptions. The code has no deployment descriptors, containers or CI. With the default `127.0.0.1` both can be the same machine.
- `pom.xml` has no packaging or shade plugin and no main-class setting, so there is no executable-JAR step. Each GUI class has its own `main` (`HomePageGUI` is the home page). The compiler plugin block is misspelled (`configuretion`), so the Java 23 source/target settings may not be applied.
- The JDBC edge is drawn from the JVM container, not from the library artifact, to keep the layout clean. The communication is in fact made by the Connector/J driver inside the JVM.
- The credentials in `persistence.xml` are defaults. The README says to change them outside local use.

## Check result
- `check_inventory.py`: 0 issues, 8 elements, 3 relations.
- `puml-check`: OK, no warnings, 2 info notes about the edge crossing the cluster borders.
- Revisions: I flattened the edge routing by linking the JVM container, and used longer dashes for the internal edges. This removed the edge-through-text warnings.
