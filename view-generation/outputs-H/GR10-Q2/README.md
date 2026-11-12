# Deployment view: Municipal Report Management System

**Takeaway:** the desktop app runs as a Swing process in a Java 23 JVM on the user's workstation and talks over JDBC/TCP port 3306 (Hibernate + MySQL Connector/J) to a MySQL server holding schema `reports_db`. The configuration (127.0.0.1, account `reports_user@localhost`) makes the database co-located with the app by default.

Stakeholder: DevOps engineer. Detail level: balanced (as given). UML deployment diagram in `view.puml` (rendered `view.png`); elements and evidence in `inventory.json`. The first version is kept in `v1/`.

## How the concern is answered
- **Runtime environments and artifacts:** Java 23 JVM (no executable jar in the pom: launch with the dependency classpath and main class `Boundary.HomePageGUI`), the application artifact, the libraries Hibernate 6.6, Connector/J 9.4 and forms_rt 7.0.3 (compile scope, used by the Swing forms at runtime), MySQL server and schema `reports_db`.
- **Where executed and stored:** application in the JVM on the user workstation; data in `reports_db` on MySQL. The database host is drawn as a separate node but marked "same machine by default"; a separate host needs a new URL and a new MySQL grant (note in the view).
- **Communication:** one path, a communication path between the JVM and the MySQL server, JDBC over TCP :3306. The code has no other network I/O.
- **Technologies in the app-database link:** JPA via Hibernate, Connector/J driver, and `persistence.xml` drawn as a «deployment spec» of the app: driver, URL, user, plaintext password, `hbm2ddl update`. It is packaged with the app (`src/main/resources`), so changing it means rebuilding.

## Omitted
GUI/controller/entity structure (component view), JUnit (test scope only). A different detail level would add the layers inside the app.

## Assumptions
- Launch via main class `Boundary.HomePageGUI` is inferred: it is one of three GUI classes with `main` (also `UserLoginGUI`, `UserRegistrationGUI`); the home page is the natural entry point (unconfirmed).
- That `persistence.xml` ends up inside the built artifact is inferred from Maven's resource layout; the pom has no packaging config.
- Separate Database host node is kept (UML needs a node for the MySQL environment), marked as co-located by default.

## Revision after review (v1 -> v2)
- Communication is now a communication path JVM -- MySQL (v1: arrow from an artifact); app -> libraries is a dashed «use»; removed the "stores data" dependency (nesting shows it).
- `persistence.xml` became a «deployment spec» attached to the app and lists the settings.
- Added forms_rt as a runtime library and corrected the earlier "build-only" claim (reviewer was right; compile scope, imported in the Boundary GUIs).
- Added launch note, `reports_user@localhost` grant and co-location note.
- Not applied: nothing rejected.

## Check result
puml-check: one `aspect` warning (ratio 1.25, a little tall, because the nested nodes stack). All overlap and edge-through-text warnings from the first draft of this revision are gone. check_inventory.py: 0 issues; check_view.py: clean.
