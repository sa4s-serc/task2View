# Deployment view: Municipal Report Management System (v2)

**Takeaway:** by default the whole system sits on one machine: a Java 23 Swing application (jar plus three libraries on the classpath) talks to a MySQL server on the same host (`127.0.0.1:3306`, schema `reports_db`) through JPA/Hibernate over JDBC. There is no application server.

Stakeholder: DevOps engineer. Detail level: **detailed** (as given). Files: `view.puml`, `view.png`, `inventory.json`; the first version is in `v1/`.

## How the view addresses the concern
- **Runtime environments and artifacts:** Maven + JDK 23 (build host), JVM Java 23, the jar, hibernate-core 6.6.50.Final, mysql-connector-j 9.4.0, forms_rt 7.0.3, MySQL server. The jar is labelled "no Main-Class, no bundled libs" and a note states how to launch it (classpath = jar + libraries, pick a main class such as `Boundary.HomePageGUI`; `UserLoginGUI` and `UserRegistrationGUI` also have `main`).
- **Where it runs / where data is stored:** one application host holding both the JVM and the MySQL server; data is in schema `reports_db`, user `reports_user` (localhost-only grant).
- **Communication:** a UML communication path (undirected) JVM — MySQL, labelled JDBC, TCP 3306; build host to Maven Central over HTTPS.
- **Application–database dependencies:** the packaged `persistence.xml` is a «deployment spec» nested in the jar with driver class, JDBC URL, user, hard-coded password, `hbm2ddl.auto=update`, RESOURCE_LOCAL and the persistence unit name. Artifact dependencies are dashed «use» (jar → hibernate, jar → forms_rt, hibernate → JDBC driver). The precondition (create database and user first, README SQL) is a note on the MySQL node.

## Changes after the review
- Removed the separate «device» Database host; MySQL now sits on the application host (127.0.0.1 and the `@'localhost'` grant support only that). The note on remote use says what would have to change (edit `persistence.xml`, rebuild, new grant). Dropped the "each user connects directly" claim.
- `persistence.xml` is a «deployment spec» nested in the jar, not a separate artifact with a "reads settings" arrow.
- Relations fixed: dashed «use» between artifacts (jar → forms_rt added), undirected communication path to MySQL, dropped the Maven "builds, packages" arrow.
- Maven Central is a plain node, not a «device».
- Launch fact and DB precondition moved into the view.
- Kept my version: the reviewer's point that the build host goes beyond runtime was accepted as "may stay"; it is kept minimal since a new environment must build with Maven.

## Omitted on purpose
Internal packages (component view), JUnit (test scope), transitive libraries, an arrow from the build host to the jar (no standard UML form; the build output is the jar shown on the host).

## Assumptions / unconfirmed
- Build host as a machine separate from the application host is an assumption (no CI, Docker or installer in the repo).
- The pom has only `maven-compiler-plugin` (with a misspelled `<configuretion>` tag, so source/target come from properties); the jar is therefore assumed not runnable alone. Which main class users start is not defined; HomePageGUI is a suggestion.
- Passwords are the README examples and must be changed outside local use.

## Check results
puml-check: renders, 0 overlaps or crossings; one aspect warning (ratio 1.31, a bit tall) and one "busy" info. check_inventory.py (`--level detailed --graph`): 0 issues, 1 note (infrastructure elements have no code members). v1 had the same kind of aspect warning (0.81), so the revision is better.
