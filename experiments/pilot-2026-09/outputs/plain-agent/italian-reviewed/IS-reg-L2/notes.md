# Notes: User registration architecture (run-id IS-reg-L2)

Stakeholder goal (verbatim): integration tester needs main components, responsibilities, and interactions for new-account registration, plus main integration points to exercise.

Evidence sources (subject repo only):
- `JavaProject/src/main/java/it/unina/prenotazioni/boundary/SpringBoot/BoundaryAutenticazione.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/boundary/Swing/Registrazione.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/controller/BibliotecaFacade.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/controller/GestoreUtenti.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/controller/factory/{UtenteFactory,StudenteFactory,BibliotecarioFactory}.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/entity/{RegistroUtenti,Utente,Studente,Bibliotecario}.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/dto/UtenteDTO.java`
- `JavaProject/src/main/java/it/unina/prenotazioni/database/{GestorePersistenza,JpaUtil}.java`
- `JavaProject/src/main/resources/META-INF/persistence.xml`
- Existing suite `RegistrazioneTest` exercises via `BibliotecaFacade` + real JPA DB cleanup

## Components and responsibilities (UC1)

| Component | Layer | Responsibility in registration |
|-----------|-------|--------------------------------|
| `BoundaryAutenticazione` | Spring Boot boundary | HTTP POST `/api/auth/registrazione`; collects form params; forwards to facade; returns `UtenteDTO` |
| `Registrazione` (Swing) | UI boundary | Collects ruolo/nome/cognome/email/password/identificativo; calls facade; shows success/error |
| `BibliotecaFacade` | Controller facade | Sole boundary entry for UC1; delegates to `GestoreUtenti` |
| `GestoreUtenti` | Controller | Validates role/fields (V12–V14, V20); uniqueness of email & identifier; selects factory by role; persists; maps entity → `UtenteDTO` |
| `UtenteFactory` / `StudenteFactory` / `BibliotecarioFactory` | Factory Method | Build concrete `Studente` (matricola) or `Bibliotecario` (codice interno) |
| `Utente` / `Studente` / `Bibliotecario` | JPA entities | Domain model; JOINED inheritance; unique email / matricola / codice |
| `UtenteDTO` | DTO | Boundary-facing payload (id, anagraphics, ruolo, identificativo) |
| `RegistroUtenti` | Entity-layer registry | Uniqueness queries; `registraUtente` → persist |
| `GestorePersistenza` | Database | Generic `salva` / field queries via EntityManager transactions |
| `JpaUtil` + `prenotazioniPU` | Persistence infra | EMF for MySQL unit `prenotazioniPU` |

## Happy-path interaction (new account)

1. Boundary (REST or Swing) → `BibliotecaFacade.registrazione(...)`
2. Facade → `GestoreUtenti.registrazione(...)`
3. `GestoreUtenti` validates input; role must be Studente or Bibliotecario
4. Uniqueness: `RegistroUtenti.esisteEmailIstituzionale` and matricola/codice lookup via `GestorePersistenza` queries
5. Role selects `StudenteFactory` or `BibliotecarioFactory` → `creaUtente` → entity instance
6. `RegistroUtenti.registraUtente` → `GestorePersistenza.salva` → JPA persist/commit (MySQL)
7. On failure of save → `RuntimeException`; on success → `UtenteDTO` returned to boundary

## Main integration points for tests

1. **Boundary ↔ Facade**: REST/UI params cross into `BibliotecaFacade.registrazione` (both Swing and Spring use the same signature).
2. **Facade ↔ GestoreUtenti**: UC1 delegation; validation and business rules live here.
3. **GestoreUtenti ↔ RegistroUtenti**: uniqueness checks (email, matricola/codice) before create; persist after create.
4. **GestoreUtenti ↔ Factories**: role-based creation of `Studente` vs `Bibliotecario` entities.
5. **RegistroUtenti ↔ GestorePersistenza ↔ JPA/DB**: write path (`salva`) and read path (uniqueness queries); DB uniqueness constraints on email/matricola/codice.
6. **GestoreUtenti ↔ UtenteDTO**: entity-to-DTO mapping returned across the controller/boundary boundary (no entity types cross that boundary per facade contract).

Existing `RegistrazioneTest` primarily exercises points 2–6 through the facade with a live persistence unit; REST/Swing entry points (point 1) are additional integration surfaces.
