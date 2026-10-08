# GR10-Q2 — Architecture view notes (DevOps / deployment)

**Run id:** GR10-Q2  
**Subject:** `progetto_ing_software_gr10`  
**Stakeholder goal:** deploy/configure in a new environment — runtime environments, software artifacts, where app/data run and store, how runtime elements communicate, technologies for app↔database communication.

Evidence sources (subject repo only): `README.md`, `pom.xml`, `src/main/resources/META-INF/persistence.xml`, `Database/JpaUtil.java`, `Database/ServizioPersistenza.java`, Entity facades, Boundary entry points, package layout.

---

## Runtime environments required

| Environment | Evidence |
|-------------|----------|
| **JVM host (desktop)** | Java Swing GUI (`javax.swing`, `GUIHomePage.main`); Maven compiler source/target **23** (`pom.xml`). App is a local desktop process, not a web/app server. |
| **MySQL server** | README § “Configurazione del database MySQL”; JDBC URL `jdbc:mysql://127.0.0.1:3306/segnalazioni_db` in `persistence.xml`. Default port **3306**, host **127.0.0.1** (same machine as client in shipped config). |

---

## Software artifacts & build/runtime dependencies

| Artifact / dependency | Role | Evidence |
|----------------------|------|----------|
| Maven artifact `it.unina.ingegneriasoftware:Progetto_Ing_Software_GR10:1.0-SNAPSHOT` | Buildable application | `pom.xml` |
| `mysql-connector-j` 9.4.0 | JDBC driver Java→MySQL | `pom.xml` comment + dependency |
| `hibernate-core` 6.6.50.Final | JPA ORM provider | `pom.xml`; provider `org.hibernate.jpa.HibernatePersistenceProvider` in `persistence.xml` |
| `forms_rt` 7.0.3 | IntelliJ GUI Designer runtime for Swing forms | `pom.xml`; GUI classes use `com.intellij.uiDesigner` |
| `junit-jupiter` 5.10.2 | Tests only | `pom.xml` scope test |
| `META-INF/persistence.xml` | Persistence unit + JDBC credentials | `src/main/resources/META-INF/persistence.xml` |

Packaged Java layers (BCED, per README): **Boundary** (Swing), **Control**, **Entity**, **Database**.

---

## Where application and data execute / are stored

- **Application execution:** Desktop JVM process started via Swing entry points (e.g. `Boundary.GUIHomePage.main`). In-process layers: Boundary → Control → Entity facades → Database package.
- **Data storage:** Relational DB **`segnalazioni_db`** on MySQL. Mapped entity classes listed in persistence unit: `Utente`, `Cittadino`, `OperatoreComunale`, `Segnalazione`, `NotaInterna`, `AggiornamentoStato`, `Notifica`. Schema updates via `hibernate.hbm2ddl.auto=update`.
- **Config location:** JDBC URL/user/password and driver in `persistence.xml` (must be aligned with MySQL setup; README documents create DB/user/grants).

Configured credentials (from shipped `persistence.xml`):

- Driver: `com.mysql.cj.jdbc.Driver`
- URL: `jdbc:mysql://127.0.0.1:3306/segnalazioni_db`
- User: `segnalazioni_user`
- Password: `segnalazioni_password`
- Persistence unit name: `Sistema_Gestione_Segnalazioni_Comunali` (must match `JpaUtil` / `Persistence.createEntityManagerFactory(...)`)
- Transaction type: `RESOURCE_LOCAL`

---

## How main runtime elements communicate

In-process (same JVM):

1. **Boundary (Swing GUI)** invokes **Control** controllers with simple DTOs/maps.
2. **Control** delegates to **Entity** facades (`ServizioUtenti`, `ServizioSegnalazioni`) — controllers do not use `ServizioPersistenza` directly (class comments).
3. **Entity facades** use **`ServizioPersistenza`**.
4. **`ServizioPersistenza`** obtains `EntityManager` from singleton **`JpaUtil`**.
5. **`JpaUtil`** creates `EntityManagerFactory` for persistence unit `Sistema_Gestione_Segnalazioni_Comunali`.

Cross-process (app ↔ database):

- **JDBC** over TCP to MySQL (`jdbc:mysql://...`), driven by **MySQL Connector/J**, mediated by **Hibernate/JPA** (`EntityManager` persist/merge/find/JPQL).
- No separate application server, message broker, or REST API found in source for runtime communication.

---

## Technologies involved in application–database communication

1. **Jakarta Persistence (JPA) 3.1** — `persistence.xml` schema; API types in `JpaUtil` / `ServizioPersistenza`.
2. **Hibernate ORM** — JPA provider; `hbm2ddl.auto`, SQL logging properties.
3. **MySQL Connector/J** — JDBC driver class `com.mysql.cj.jdbc.Driver`.
4. **MySQL** — RDBMS holding `segnalazioni_db`.
5. **RESOURCE_LOCAL** transactions — `EntityTransaction` begin/commit/rollback in `ServizioPersistenza`.

---

## View choice

PlantUML **deployment / runtime** diagram (`architecture_view.puml`) focusing on nodes (JVM host, MySQL), deployable artifacts, in-process BCED communication path, and JDBC/JPA stack between application and database — aligned to the DevOps stakeholder questions above.
