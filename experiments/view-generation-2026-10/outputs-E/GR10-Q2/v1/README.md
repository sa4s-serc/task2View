# Deployment view: Municipal Report Management System

**Takeaway:** a Java 23 Swing desktop client runs on the user's workstation. It reaches a MySQL server over JDBC/TCP 3306 (default 127.0.0.1, schema `reports_db`) through Hibernate and the MySQL connector.
**Stakeholder:** DevOps engineer. **Detail level:** detailed (given). Files: `view.puml`, `view.png`, `inventory.json`.

## How the view answers the concern
- **Runtime environments and artifacts:** the JVM (Java 23) and the MySQL server are execution environments. The deployed artifacts are the application classes, `persistence.xml`, hibernate-core 6.6.50.Final, mysql-connector-j 9.4.0 and forms_rt 7.0.3. The build side (Maven 3 + JDK 23, Maven Central) is also shown.
- **Where it runs and where data is stored:** the app runs in a JVM on the user workstation. All data lives in the `reports_db` schema on MySQL (README.md:26-35). The default host is 127.0.0.1, so by default both sit on the same machine; the database host is drawn separately because the URL can point elsewhere.
- **Communication:** JDBC over TCP :3306 from the JVM to MySQL, and HTTPS from Maven to Maven Central at build time. There is no other network communication in the code (no HTTP, SMTP or sockets). Notifications are rows in the database.
- **Technologies and dependencies:** the app uses JPA (Hibernate), which loads `com.mysql.cj.jdbc.Driver`. `persistence.xml` holds the URL, user and password. `hbm2ddl.auto=update` creates and alters tables on first connect, but the database and user must exist beforehand.

## Omitted on purpose
Application layers (component view), junit (test scope), and the JDK's Swing modules (labelled on the JVM).

## Assumptions and unconfirmed items
- The Maven build is drawn as creating the app classes. The pom has no packaging plugin, shade plugin or main-class manifest, so there is no runnable jar. The launch command is unknown. The entry points are the `main()` methods in HomePageGUI, UserLoginGUI and UserRegistrationGUI.
- Dependencies must be put on the classpath by hand or by an IDE.
- Operator note: `pom.xml:64` misspells `<configuretion>`, so the compiler plugin ignores that block. The `maven.compiler.source/target` properties still apply.
- The credentials are hard-coded and the README says to change them outside local use.
- Multiple clients can share one database only if the URL is changed. This is not shown in the code.

## Check results
- `puml-check`: renders OK, no warnings. There are two info lines: an edge crossing container borders and a busy-diagram note.
- `check_inventory.py --level detailed`: exit 0, clean (13 elements, 7 relations).
