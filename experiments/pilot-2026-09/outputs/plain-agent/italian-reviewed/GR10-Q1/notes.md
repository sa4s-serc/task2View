# Architecture notes — GR10-Q1

**Subject:** `progetto_ing_software_gr10`  
**Run id:** GR10-Q1  
**Stakeholder goal:** software architect review of overall organization, layers/subsystems, responsibilities, and separation of UI / application logic / domain / persistence.

Evidence sources (repository only):
- `README.md` — municipal complaint/reporting system; actors Cittadino and OperatoreComunale; documented BCED pattern in Visual Paradigm models
- `pom.xml` — Java desktop app; Swing (IntelliJ forms_rt); Hibernate ORM + MySQL JDBC
- `src/main/java/{Boundary,Control,Entity,Database}` — package decomposition matching BCED
- `src/main/resources/META-INF/persistence.xml` — JPA unit `Sistema_Gestione_Segnalazioni_Comunali` → MySQL `segnalazioni_db`
- Class comments and imports confirming dependency direction

## Layered decomposition (BCED)

| Layer (package) | Responsibility | Key types |
|-----------------|----------------|-----------|
| **Boundary** | User-facing Swing UI; collects simple data (`Map`); navigates screens | `GUIHomePage` (entry), access/registration, `GUIDashboardUtente`, feature GUIs for segnalazioni |
| **Control** | Application / use-case orchestration; role checks; DTO-style Maps to/from Boundary | `ControllerServiziSistema` (facade), dedicated use-case controllers, `ControllerAccessoUtente` |
| **Entity** | Domain model + domain facades; business rules; State pattern for report status | `ServizioUtenti`, `ServizioSegnalazioni`, JPA entities, `StatoSegnalazione` implementations |
| **Database** | Persistence facade over JPA/Hibernate; no Control→Database coupling | `ServizioPersistenza`, `JpaUtil` |

## Main dependency rules (from imports)

1. Boundary → Control (mostly `ControllerServiziSistema`; login uses `ControllerAccessoUtente` directly).
2. Boundary rarely imports Entity (`CategoriaSegnalazione` enum only in a few GUIs).
3. Control → Entity facade services (`ServizioUtenti`, `ServizioSegnalazioni`); **no** Control → Database imports.
4. Entity facades → `Database.ServizioPersistenza`.
5. Database → JPA (`EntityManager` / `EntityManagerFactory`) → MySQL.

## Collaboration for main functionalities

- **Access / registration:** GUI → `ControllerAccessoUtente` / facade `registraUtente` → `ServizioUtenti` → persistenza.
- **Citizen flows:** create report, consult sent reports → facade → `ControllerCreazione*` / `ControllerConsultazione*` → `ServizioSegnalazioni` (+ role checks via `ServizioUtenti`).
- **Operator flows:** consult received, update status, internal notes, monitoring → same Control facade → dedicated controllers → `ServizioSegnalazioni`.
- **Status lifecycle:** Entity State pattern (`Inviata` → `PresaInCarico` → `InLavorazione` → `Risolta`) advanced via `ServizioSegnalazioni`, not chosen by the GUI.

## External runtime

Desktop JVM client + Hibernate + MySQL database `segnalazioni_db` (credentials in `persistence.xml`).

## Out of diagram scope

- Test packages (`testingBlackBox`, `testingWhiteBox`)
- Docs/Visual Paradigm artifacts under `docs/` (design evidence, not runtime components)
