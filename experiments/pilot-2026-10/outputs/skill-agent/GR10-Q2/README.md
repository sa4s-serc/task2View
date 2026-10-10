# Task2View single-agent run GR10-Q2

- **Model:** Claude Sonnet 5.5 (claude-sonnet-5-5), agent + task2view skill; `usage.json` omitted (no token report available to the agent)
- **Goal:** I am a DevOps engineer. I need to deploy and configure the system in a new execution environment. Before preparing the deployment, I need to understand which runtime environments and software artifacts are required, where the application and its data are executed and stored, and how the main runtime elements communicate with each other. I also need to identify the technologies and runtime dependencies involved in the communication between the application and the database.
- **Role:** DevOps engineer (`devops`) · **Target:** whole system · **Detail level:** feature
- **Primary needs:** deployment, build-packaging, data-storage · **Secondary:** dependencies (not shown as a view)

## Views
| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-deployment | deployment (V&B 5.2) | confirm | pass_with_limitations | 7 | PlantUML (`plantuml -checkonly` passes) |

## Rationale
One Deployment Style view covers all three primary needs (it frames deployment and also covers build-packaging and data-storage), so no second view was added. The runtime picture: a Java 23 process runs `municipal-report-management.jar` plus three library jars (hibernate-core, mysql-connector-j, forms_rt); the app talks to MySQL database `reports_db` through JPA/Hibernate over JDBC (`jdbc:mysql://127.0.0.1:3306/reports_db`, user `reports_user`).

## Facts a deployer must know (all cited in `evidence_model.json`)
- Connection URL, user and password are inside the packaged `persistence.xml`; the defaults point at loopback, so another host needs a rebuild or a changed resource.
- `hibernate.hbm2ddl.auto=update`: the schema is created/updated on start, so the DB user needs DDL rights; the database itself must be created by hand.
- `RESOURCE_LOCAL`: each desktop process opens its own JDBC connections; there is no application server or datasource.
- The app is a Swing GUI and needs a display; attached images are stored as file paths, not content.
- `pom.xml` has no shade/manifest config: libraries must be on the classpath and the start class (e.g. `Boundary.HomePageGUI`) named explicitly.

## Limitations and gaps
- Repository defines no node, host, container or Dockerfile: 'where it runs' is only the Java 23 and MySQL execution environments; the default JDBC host 127.0.0.1 implies the same machine.
- Library artifacts are drawn as communicates edges from the application jar because the viewpoint has no 'uses' relation; they are in-process calls, not network links.
- Transitive runtime dependencies (for example jakarta.persistence-api, jboss-logging, JDK modules) are not declared in pom.xml and are not drawn.
- pom.xml misspells <configuretion> in maven-compiler-plugin; the plugin therefore ignores it, but the maven.compiler.* properties still apply.
- pom.xml defines no jar-with-dependencies, shade or manifest main class: the library jars must be on the classpath at launch and the start class must be named explicitly.
- Secondary need 'dependencies' (between code parts) is not shown as a separate view.
- Task-fit validation is `not-run` (a different model must judge).

## Evidence counts
Claims verified 25, rejected 0 (7 inferred, 1 documented); elements 7; relations 9 (4 drawn `communicates`, 4 `contains` shown as nesting); scenarios 0.
