# Deployment view: Municipal Report Management System (revision 1)

**Takeaway:** by default a Java 23 Swing client and a MySQL server (127.0.0.1:3306, schema `reports_db`) run on the same workstation. The JVM talks JDBC/TCP 3306 through Hibernate, the MySQL driver and the `persistence.xml` deployment spec.
**Stakeholder:** DevOps engineer. **Detail level:** detailed (given). Files: `view.puml`, `view.png`, `inventory.json`. The previous version is in `v1/`.

## How the view answers the concern
- **Runtime environments and artifacts:** the JVM (Java 23) and the MySQL server are execution environments. The artifacts are the app classes, hibernate-core 6.6.50.Final, mysql-connector-j 9.4.0, forms_rt 7.0.3 and `persistence.xml`. A note adds that there is no fat jar, so the transitive dependencies (e.g. `jakarta.persistence-api`) must be on the classpath. It also notes that `/images/logo.png` is expected but absent.
- **Where it runs and where data lives:** everything is on the user workstation by default. Data is in `reports_db` inside MySQL.
- **Communication:** one undirected communication path, JDBC/TCP 3306, between the JVM and MySQL. The code has no other network I/O. The note on the JVM mentions `mvn` and Java 23 for the build.
- **Technologies and dependencies:** app -> Hibernate (JPA) -> MySQL driver -> MySQL. `persistence.xml` is a `<<deploymentSpec>>` that holds the URL, user and `hbm2ddl.auto=update`. Editing it changes the database endpoint. The MySQL note says the database, the user and the grant must exist before the first start. Hibernate then creates and alters the tables.

## Changes after the review (v1 -> v2)
- **MySQL moved onto the workstation.** The 127.0.0.1 URL and the `@'localhost'` grant (README.md:29-31) only support a single host. A remote host is described in a note, with the changes it needs: a new JDBC URL and a grant for the client host.
- **`persistence.xml` is now a `<<deploymentSpec>>`** that lists its settings. A `configures` dependency links it to the app.
- **The communication path is now an undirected association** named by protocol. The `<<create>>` dependency is removed.
- **The build side is cut:** the Build machine, Maven and Maven Central boxes are gone and only a note is left. This also removes the `<<device>>` classification for Maven Central.
- **Notes added:** transitive dependencies and the missing logo resource.

## Omitted on purpose
The build machine and Maven Central (build-time), application layers (component view), junit (test scope), and the enumeration of Hibernate's transitive libraries.

## Assumptions
- The launch command is unknown (no manifest or launcher). The entry points are the three `main()` methods.
- The `/images/logo.png` absence is non-fatal. `InternalNoteGUI.java:399` only logs it, and I did not check the other GUIs.
- `pom.xml:64` misspells `<configuretion>`, so the compiler plugin ignores that block. The `maven.compiler.*` properties still apply.
- Credentials are hard-coded in `persistence.xml`.

## Check results
- `puml-check`: OK, no warnings (v1 had none, only info lines). The first v2 render had an edge-through-text warning from a note, fixed by moving the configuration text into the artifact.
- `check_inventory.py --level detailed`: exit 0 (9 elements, 5 relations).
- Reviewer points kept as is: none were contradicted by the code.
