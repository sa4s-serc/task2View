# Deployment view: Municipal Report Management System (revision 1)

**Takeaway:** with the shipped configuration the system is one Java 23 Swing process and one MySQL server on the same machine, connected by JDBC over TCP (loopback, port 3306). A new environment needs a JVM, the jar plus its dependency jars, and a manually prepared `reports_db`.

**Stakeholder:** DevOps engineer deploying to a new environment. **Detail level:** balanced (7 nodes/artifacts), with technical wording (versions, protocol, launch details).

Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation). The previous version is in `v1/`.

## How the concern is addressed
- **Runtime environments and artifacts:** the Java 23 JVM, the application jar, the dependency jars (Hibernate 6.6.50, Connector/J 9.4.0, forms_rt 7.0.3), `persistence.xml` and the MySQL server. The MySQL version is not specified in the code, and the diagram says so. The launch note says: no Main-Class and no shaded jar, so run with the dependency jars on the classpath, main class `Boundary.HomePageGUI`.
- **Where it runs and where data is stored:** the client and MySQL both sit on the workstation. Data is in schema `reports_db`, accessed as `reports_user@localhost`.
- **Communication:** one undirected communication path, JDBC over TCP :3306, loopback by default. There is no other runtime link, because it is a single process with no server tier.
- **Technologies and dependencies:** the app uses the dependency jars and the `persistence.xml` packaged in the jar (JDBC URL, user, hard-coded password, `hbm2ddl.auto=update`). The manual preparation note gives `CREATE DATABASE`, `CREATE USER` with the default password, and `GRANT ALL`. Changing host or password means editing `persistence.xml` and rebuilding.

## Changes from v1 (reviewer critique)
- MySQL now sits on the workstation, since the URL is `127.0.0.1` and the grant is for `localhost`. The separate database host is gone, and a note says a remote host needs config, rebuild and grant changes.
- `persistence.xml` stays an artifact in the JVM. I did not nest it inside the jar artifact, which is the reviewer's UML fix and remains open. I did not try nesting; its label states it is packaged in the jar, and the app-to-`persistence.xml` link is a `<<use>>` dependency.
- Added forms_rt 7.0.3, the launch note and the database preparation note (now attached to the schema).
- The JDBC path is undirected; the dependencies use `<<use>>`.

## Where I kept my version
- The reviewer says the jar is "packaged as jar". `pom.xml` has no `<packaging>` element, so jar is the Maven default. The diagram shows a jar and notes that there is no Main-Class or shade plugin.
- The communication path joins the JVM and MySQL containers. The Connector/J driver inside the JVM makes the call.

## Omitted on purpose
The Boundary/Control/Entity/Database layers (a component view), JUnit tests (test scope), and a remote DB host (unsupported without changes).

## Assumptions
- "Operator/citizen PC" for the workstation is inferred from the Swing `main` entry points. The code has no deployment descriptors, containers or CI.
- The compiler plugin block is misspelled (`configuretion` in `pom.xml`), so the Java 23 source/target settings may not be applied (`maven.compiler.*` properties are set).
- `pom.xml` has no assembly/dependency-copy plugin, so how the dependency jars reach the classpath is left to the operator (for example `mvn dependency:copy-dependencies`; not in the repo).

## Check result
- `puml-check`: OK, no warnings (ratio 1.54 vs 1.78).
- `check_inventory.py`: 0 issues, 7 elements, 3 relations.
