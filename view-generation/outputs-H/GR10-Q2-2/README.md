# GR10-Q2-2: Component view of runtime communication (revision 1)

**Takeaway:** the application is one Java 23 process, started from `Boundary.HomePageGUI.main`. Its persistence access reaches the MySQL server (schema `reports_db`) through Hibernate and Connector/J over JDBC on TCP port 3306, with all settings fixed in the packaged `persistence.xml`.

Stakeholder: DevOps engineer. Detail level: balanced (given). Model kind: UML component diagram. Files: `view.puml`, `view.png`, `inventory.json`. The previous version is in `v1/`. Names match the deployment view GR10-Q2.

## How it addresses the concern
- **Runtime environments and artifacts:** the Maven artifact `municipal-report-management-1.0-SNAPSHOT` (no executable jar, so dependency jars go on the classpath), the Java 23 JVM and its entry point, `persistence.xml`, the libraries, and the MySQL server. The setup prerequisite is in a note: `reports_db` and `reports_user@localhost` are created by hand (README SQL), and Hibernate only creates the tables.
- **Where the application and data live:** the application and its libraries share one JVM. The data is in `reports_db` on the MySQL server. The URL is 127.0.0.1, so the server is expected on the same host. Moving it means editing `persistence.xml` and repackaging, because there is no external override (note).
- **Communication:** in-process calls inside the application, then Hibernate (JPA), Connector/J (JDBC), then TCP 3306 to MySQL.
- **Technologies on the database path:** Hibernate ORM 6.6, MySQL Connector/J 9.4 (driver `com.mysql.cj.jdbc.Driver`), JDBC, TCP 3306, persistence unit `Municipal_Report_Management_System`, RESOURCE_LOCAL, `hbm2ddl update`.

## Changes after the review
- Split the library box into Hibernate and Connector/J on the database path, inside the application. forms_rt is now attached only to the GUI.
- The process boundary is a component (not a package). `persistence.xml` and the schema are artifacts. Plain arrows became `<<use>>` dependencies.
- Added the deployable artifact, entry point, setup prerequisite and configuration notes.
- Merged Swing screens, controllers and domain into one "Application logic and GUI" component.
- Dropped the `@localhost` host part from the server label, since it comes from the README setup SQL. It appears only in the note as a prerequisite.

## Reviewer points not followed
- **Interface symbols (JPA, JDBC) with assembly connectors:** I tried them. Every layout made an edge cross the interface label, so the JPA and JDBC links are labelled `<<use>>` dependencies instead.
- **The MySQL version** is not shown because nothing in the code or the build files states it.

## Omitted on purpose
Single classes, and direct screen-to-domain dependencies (screens use domain data types). Deployment nodes belong to GR10-Q2.

## Assumptions
The jar element carries the same members as in GR10-Q2, to keep names consistent. The inner components therefore have no member list, so the graph does not check their relations.

## Check results
puml-check: 0 warnings. check_inventory.py (balanced, with graph): 0 issues, one note about unchecked elements. check_view.py: clean. check_consistency.py with GR10-Q2: consistent.
