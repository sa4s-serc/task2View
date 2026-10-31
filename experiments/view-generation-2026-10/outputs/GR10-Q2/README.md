# GR10-Q2 – Deployment view (UML deployment diagram)

`view.puml` shows how the Municipal Report Management System is deployed and how its runtime elements connect. It was derived from `pom.xml`, `persistence.xml`, `Database/*`, the `main` methods in `Boundary/*`, and the README.

## How it addresses the concern
- **Required runtime environments and artifacts:** Client workstation runs a Java 23 JVM with the application classes, `persistence.xml`, the logo resource, and the libraries hibernate-core 6.6.50.Final, mysql-connector-j 9.4.0 and forms_rt 7.0.3. A MySQL server is the second environment. A build host (JDK 23 + Maven) produces the artifact and resolves dependencies from Maven Central.
- **Where the application runs and where data is stored:** The whole application (Swing GUI, controllers, entities, persistence) is one desktop process on the client. Data lives only in the MySQL schema `reports_db` (tables `users`, `reports`, `internal_notes`, `status_updates`, `notifications`). By default MySQL is on `127.0.0.1`, i.e. the same machine.
- **How the main elements communicate:** The only runtime link is JDBC over TCP (port 3306) from the client JVM to MySQL, via JPA/Hibernate. Maven Central access is build-time only. The code has no application server, web service or e-mail integration.
- **Technologies and runtime dependencies between app and DB:** JPA (Hibernate, `RESOURCE_LOCAL` transactions) → MySQL Connector/J (`com.mysql.cj.jdbc.Driver`) → MySQL. The database, user `reports_user` and grants must exist before first run; Hibernate then creates/updates the tables (`hbm2ddl.auto=update`).

## Deployment notes
- Credentials and the JDBC URL are hard-coded in `persistence.xml`; to use a remote DB, change the URL, user and password there, and open port 3306.
- The repository defines no packaging (no jar/shade plugin, no manifest), so the "deploy" step shown (jar + dependencies on the classpath) is an inference; start from a `main` class such as `Boundary.HomePageGUI`.
- `pom.xml` has a typo (`configuretion`), so the compiler plugin settings are ignored. The JDK 23 requirement comes from the properties and README.
- The black-box tests need a running MySQL instance and may open Swing dialogs.
