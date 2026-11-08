# Deployment view: Municipal Report Management System

**Takeaway:** the system is a single Java 23 Swing desktop process that reaches a MySQL server on port 3306 over JDBC (Hibernate/JPA). All data lives in the MySQL schema `reports_db`.

Stakeholder: DevOps engineer. Detail level: **detailed** (as given). Model kind: UML deployment diagram. Files: `view.puml`, `view.png`, `inventory.json`.

## How the view addresses the concern
- **Runtime environments and artifacts:** Java 23 JVM with the application classes, `persistence.xml`, hibernate-core 6.6.50.Final, mysql-connector-j 9.4.0 and forms_rt 7.0.3. MySQL server is the other environment. The build host (Maven, JDK 23, Maven Central) is also shown.
- **Where it runs and where data is stored:** the app runs on the user workstation. Data is in schema `reports_db` on the database host, which is `127.0.0.1` by default (same machine). There is no application server.
- **Communication:** application → Hibernate (JPA) → JDBC driver → MySQL over TCP :3306. Citizens and operators use the same client; there is no other network protocol in the code.
- **Technologies and dependencies between app and database:** `persistence.xml` holds the unit name, driver, URL, user `reports_user` and password. `hbm2ddl.auto=update` creates and alters tables, but the database and user must exist first (README SQL).

## Omitted on purpose
Individual classes (class level), the junit test dependency (tests need a live MySQL), and the app's build output packaging.

## Assumptions / unconfirmed
- No `.claude/repo-graph.json` existed, so evidence comes from reading the code directly. Graph-based checks were not run.
- The pom has no packaging or shade plugin and no manifest main class. How the app is packaged for distribution is **unknown**. Three classes have `main`: `HomePageGUI` (home), `UserLoginGUI`, `UserRegistrationGUI`.
- `pom.xml:64` has a typo, `<configuretion>`, so the compiler settings are ignored. The `maven.compiler.*` properties still set Java 23.
- There are no Docker/Kubernetes/CI files. Separate machines for the DB host are possible by editing the JDBC URL, but this is not set up.
- Credentials are hard-coded defaults. Change them for any non-local environment.

## Check results
- puml-check: renders, 0 warnings. 3 info notes (nested container edges, busy diagram).
- check_inventory.py --level detailed: 0 issues (no graph was available, so run without `--graph`).
