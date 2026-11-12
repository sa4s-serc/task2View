# GR10-Q2-2: Component view of runtime communication

**Takeaway:** the Swing client is one Java 23 process whose layers call each other in memory, and its persistence layer reaches the MySQL server (schema `reports_db`) through Hibernate and MySQL Connector/J over JDBC on TCP port 3306.

Stakeholder: DevOps engineer. Detail level: balanced (given). Model kind: UML component diagram (`view.puml`, `view.png`, `inventory.json`). Names match the deployment view GR10-Q2.

## How it addresses the concern
- **Runtime environments and artifacts:** the application process, `persistence.xml` packaged with it, the Hibernate / Connector/J / forms_rt libraries, and the MySQL server. Machines and the JVM as nodes belong to view GR10-Q2.
- **Where the application and data live:** the application is one process. Data is in schema `reports_db` on the MySQL server. The URL 127.0.0.1 makes the server local by default (see GR10-Q2 for hosts).
- **Runtime communication:** screens call controllers, controllers call the domain services and the services call persistence access, all in process. Persistence goes to the libraries through JPA, and the libraries reach MySQL over JDBC/TCP 3306.
- **Technologies between application and database:** JPA (Hibernate ORM 6.6), JDBC (Connector/J 9.4), TCP 3306, and the persistence unit settings in `persistence.xml` (driver, URL, user, plaintext password, `hbm2ddl update`).

## Omitted on purpose
Single classes, and 7 direct screen-to-domain dependencies (screens use domain data types such as report categories). Deployment nodes are not drawn.

## Assumptions
Layer-to-layer calls are grouped per package. The MySQL server is assumed to be set up manually, as in GR10-Q2.

## Check results
puml-check: 0 warnings. check_inventory.py (balanced, with graph): 0 issues, notes only (the undrawn dependencies above, and unchecked non-code elements). check_view.py: clean. check_consistency.py with GR10-Q2: consistent.
