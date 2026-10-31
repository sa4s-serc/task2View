# Deployment view – Municipal Report Management System

**Takeaway:** a Java 23 Swing desktop client (with Hibernate/JDBC embedded) runs on each user workstation and talks directly over JDBC/TCP 3306 to a MySQL server holding schema `reports_db`; there is no application server.

**Stakeholder:** DevOps engineer, deploying to a new environment. **Detail:** overview (whole system; 6 nodes, 7 artifacts), engineering wording (technologies and protocols named).

Files: `view.puml` (source), `view.png` (render).

## How the view addresses the concern
- **Required runtime environments and artifacts:** JVM (Java 23) on the workstation; MySQL server on the database host; app artifact, `persistence.xml`, and library jars (hibernate-core, mysql-connector-j, forms_rt); JDK 23 + Maven on the build machine.
- **Where the app runs / where data is stored:** app on the user workstation inside the JVM; data in the `reports_db` schema on the MySQL server (default host 127.0.0.1, i.e. same machine unless the URL is changed).
- **How runtime elements communicate:** workstation → DB host via JPA/Hibernate over JDBC, TCP 3306; build machine → Maven Central over HTTPS (build time only).
- **Technologies and dependencies app ↔ database:** Hibernate 6.6.50 (JPA, `RESOURCE_LOCAL`), MySQL Connector/J 9.4.0 driver `com.mysql.cj.jdbc.Driver`, persistence unit `Municipal_Report_Management_System`, DB user `reports_user`; note records that Hibernate creates/updates tables (`hbm2ddl.auto=update`) while the database and user are created manually.

## Inventory (element → evidence)
| Element | Evidence |
|---|---|
| JVM Java 23 | `pom.xml:13-14` |
| App artifact `municipal-report-management 1.0-SNAPSHOT`, entry `HomePageGUI.main` | `pom.xml:8-10`, `src/main/java/Boundary/HomePageGUI.java:75` |
| Library jars | `pom.xml:34-52` |
| `persistence.xml`, unit name | `src/main/resources/META-INF/persistence.xml:10` |
| JDBC driver, URL (127.0.0.1:3306/reports_db), user | `persistence.xml:23-33` |
| `hbm2ddl.auto=update` | `persistence.xml:35-36` |
| Unit loaded by app | `src/main/java/Database/JpaUtil.java:17` |
| MySQL server, DB/user creation | `README.md` "MySQL setup" |
| Maven Central | `pom.xml:18-22` |

## Omitted on purpose
BCED layers (Boundary/Control/Entity/Database) and entity classes (component/class concerns), tests and JUnit, Hibernate properties for SQL logging, the three alternative `main` methods (login, registration, home).

## Assumptions / unconfirmed
- Distribution form of the app (jar, launch script) is not defined: no packaging/shade/manifest config in `pom.xml`; "app jar" is the default Maven output (unconfirmed). Also `pom.xml:64` has a typo `configuretion`, so compiler settings fall to the properties.
- Workstation and DB host are separate nodes in the diagram; the code defaults make them the same machine (127.0.0.1). A remote DB requires editing `persistence.xml`.
- Build machine and "deploy" edge reflect the Maven workflow, not a CI/CD pipeline (none in the repo). Credentials are hardcoded in `persistence.xml`.

## Check result
Final `puml-check`: OK, 0 warnings (one advisory "busy" info). Image review: an initial edge cut through the workstation boxes and was fixed by linking containers and moving the note; no other changes.
