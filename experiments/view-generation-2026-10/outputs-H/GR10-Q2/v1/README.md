# Deployment view: Municipal Report Management System

**Takeaway:** the desktop app runs as a Swing process in a Java 23 JVM on the user's workstation and talks over JDBC/TCP (port 3306, Hibernate + MySQL Connector/J) to a MySQL server holding schema `reports_db`; by default that server is on the same machine (127.0.0.1).

Stakeholder: DevOps engineer. Detail level: balanced (as given). UML deployment diagram in `view.puml` (rendered `view.png`); elements and evidence in `inventory.json`.

## How the concern is answered
- **Runtime environments and artifacts:** Java 23 JVM, the Maven-built application artifact, `persistence.xml`, Hibernate/Connector-J libraries, MySQL server and schema `reports_db` (user `reports_user`; created manually per README).
- **Where executed and stored:** application on the user workstation (each user runs their own client, started from a GUI `main`); data in MySQL on the database host, localhost by default.
- **Communication:** application -> Hibernate/JPA -> JDBC over TCP :3306 -> MySQL. No other servers or protocols exist in the code.
- **Technologies in the app-database link:** JPA (Hibernate 6.6), MySQL Connector/J 9.4, settings in `persistence.xml` (`hbm2ddl update` creates tables).

## Omitted
GUI/controller/entity structure (component view), test and build-only dependencies (JUnit, forms_rt). A different detail level would add the layers inside the app.

## Assumptions
- Workstation and database host are separate nodes in the diagram, but the default config puts both on one machine; for a new environment change the URL and credentials in `persistence.xml` (hardcoded defaults, including password).
- No packaging/launch config exists (pom has no jar or main class setup); how the app is started is not specified (unconfirmed).

## Checks
puml-check: one `aspect` warning (ratio 2.8, wide because deployment reads left to right; hidden stacking links did not change it) and one info about an edge crossing node borders, which is inherent. check_inventory and check_view results below.
