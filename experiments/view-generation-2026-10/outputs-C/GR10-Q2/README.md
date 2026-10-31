# Deployment view — Municipal Report Management desktop application

**Takeaway:** the application is a Java 23 Swing desktop program that runs in one JVM and reaches a MySQL schema `reports_db` through Hibernate/JDBC over TCP at 127.0.0.1:3306, so both must be installed on the same workstation.
**Stakeholder:** DevOps engineer. **Detail:** overview (whole-system deployment, 6 nodes/artifacts-level elements).

## How the concern is addressed
- **Runtime environments and artifacts:** JVM (Java 23) and MySQL server nodes; artifacts: application (artifactId/version), hibernate-core, mysql-connector-j, forms_rt, persistence.xml, schema reports_db.
- **Where it runs / where data lives:** the application runs in the JVM on the workstation; data lives in the `reports_db` schema in the MySQL server, created/updated by Hibernate (`hbm2ddl.auto=update`).
- **Communication:** one communication path, JDBC over TCP, port 3306; internal dependencies between artifacts are `«use»`. No other network link exists in the code (no HTTP/mail/socket usage found).
- **Technologies and dependencies app↔DB:** Hibernate 6.6.50 (JPA, RESOURCE_LOCAL) → MySQL Connector/J 9.4.0 → MySQL; credentials/URL come from persistence.xml.

## Inventory (element → evidence)
- Workstation, JVM Java 23: pom.xml:13-14; README.md "Requirements"; Swing entry points `main` at Boundary/HomePageGUI.java:75, UserLoginGUI.java:91, UserRegistrationGUI.java:145.
- Application artifact: pom.xml:8-10.
- hibernate-core: pom.xml:48-52; forms_rt: pom.xml:35-38; mysql-connector-j: pom.xml:42-45.
- persistence.xml (unit, provider): src/main/resources/META-INF/persistence.xml:10,12.
- JDBC driver/URL/user: persistence.xml:23-33; schema auto-update: :35-36.
- JpaUtil creates the EntityManagerFactory: Database/JpaUtil.java:17.
- MySQL server / reports_db: persistence.xml:27; README.md "MySQL setup".

## Omitted on purpose
Classes/packages (component-level concern), tests, Maven Central build-time repository (pom.xml:18-22), IDE files.

## Assumptions / unconfirmed
- Same host for app and MySQL is derived from the 127.0.0.1 URL; a remote DB would need that URL changed.
- "Operator / citizen workstation" is a generic device; code names no OS or hardware.
- (unconfirmed) How the application is packaged/launched: pom.xml has no jar/shade/main-class setup, and the compiler plugin block uses the misspelled `<configuretion>` (pom.xml:64), so it is ignored; the artifact is shown by its Maven coordinates.
- Credentials are in plain text in persistence.xml (README advises changing them).

## Check result
puml-check: OK, 0 issues on the final run (first runs had label-on-border/edge-through-label warnings, fixed by shortening labels and lengthening the edge). Image review: readable, no changes needed.
