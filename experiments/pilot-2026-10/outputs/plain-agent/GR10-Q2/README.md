# Architecture views for the DevOps deployment request (GR10-Q2)

System: Municipal Report Management System (Java 23 / Maven Swing desktop client + MySQL via JPA/Hibernate).

## view-1.puml - Deployment view
Shows the execution environments (user workstation with JVM 23, MySQL host, build machine with JDK 23 + Maven/Maven Central), the artifacts required (application jar, persistence.xml, Hibernate, MySQL Connector/J, forms_rt, logo resource), where the app runs (client JVM, one per user) and where data lives (MySQL schema `reports_db`, tables users/reports/internal_notes/status_updates/notifications), and the single network link (JDBC over TCP 3306). Why: this answers what to provision and where.
Observations from the code: there is no server tier; the DB URL/credentials are hard-coded in `persistence.xml` inside the artifact (default 127.0.0.1); `/images/logo.png` is referenced but not present in the repo resources.

## view-2.puml - Runtime communication / DB stack view
Shows the in-process layering (Boundary -> Control -> Entity -> PersistenceService -> JpaUtil), and the technology chain to the database: Jakarta Persistence 3.1 -> Hibernate 6.6.50 -> MySQL Connector/J 9.4.0 -> MySQL protocol over TCP. Why: identifies the runtime dependencies and settings (hbm2ddl=update needs DDL rights, SQL logging on, RESOURCE_LOCAL transactions, no TLS configured) that matter for DB connectivity and configuration.
Observation: notifications are DB rows only; no other external communication was found.
