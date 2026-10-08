# Notes: User registration architecture (IS-reg-L3)

**Run id:** IS-reg-L3  
**Subject:** `experiments/skill-baseline/subjects/Progetto-IS`  
**Goal:** Integration-tester view of components supporting UC1 user registration (personal data + role validation, role-specific IDs, uniqueness, persistence, invalid/duplicate handling).

## Evidence sources (read-only)

| Area | Path |
|------|------|
| REST boundary | `JavaProject/.../boundary/SpringBoot/BoundaryAutenticazione.java` |
| Exception → HTTP | `JavaProject/.../boundary/SpringBoot/GestoreEccezioni.java` |
| Swing boundary | `JavaProject/.../boundary/Swing/Registrazione.java` |
| Web form | `JavaProject/src/main/resources/static/registrazione.html` |
| Facade | `JavaProject/.../controller/BibliotecaFacade.java` |
| Registration logic | `JavaProject/.../controller/GestoreUtenti.java` |
| Factories | `.../factory/UtenteFactory.java`, `StudenteFactory.java`, `BibliotecarioFactory.java` |
| User registry | `JavaProject/.../entity/RegistroUtenti.java` |
| Entities | `Utente.java`, `Studente.java`, `Bibliotecario.java` |
| Persistence | `JavaProject/.../database/GestorePersistenza.java` |
| Transfer type | `JavaProject/.../dto/UtenteDTO.java` |
| Existing unit/integration-style tests | `.../test/.../RegistrazioneTest.java` (calls `BibliotecaFacade.registrazione`) |

## Registration collaboration (happy path)

1. **Request intake**
   - REST: `BoundaryAutenticazione` `POST /api/auth/registrazione` collects `ruolo, nome, cognome, email, password, identificativo` and forwards to `BibliotecaFacade` (no domain logic in the boundary).
   - Swing: `Registrazione.registra()` collects the same fields (client-side blank check), then calls `BibliotecaFacade.registrazione(...)`.
   - Static HTML posts to the auth registration endpoint (same facade path via REST).

2. **Facade**
   - `BibliotecaFacade.registrazione` delegates entirely to `GestoreUtenti.registrazione`.

3. **Validation & uniqueness (`GestoreUtenti`)**
   - Common: role must be Studente/Bibliotecario; nome required; password length 8–32 (`verificaValidita`).
   - Role-specific: `verificaCorrettezzaStudente` / `verificaCorrettezzaBibliotecario` — nome/cognome letters ≤20, institutional email (`*unina.it`), identifier format; student matricola `[A-Z]\d{8}`.
   - Uniqueness via `RegistroUtenti`: `esisteEmailIstituzionale`; student `cercaStudentePerMatricola` / librarian `cercaBibliotecarioPerCodice`.

4. **Role-specific object creation**
   - Selects `StudenteFactory` or `BibliotecarioFactory` (`UtenteFactory`); sets matricola vs `codiceIdentificativoInterno`.

5. **Persistence**
   - `RegistroUtenti.registraUtente` → `GestorePersistenza.salva` (JPA persist/commit). Failure → `RuntimeException` from `GestoreUtenti`.
   - Success → `UtenteDTO` (role + identifier derived from concrete subclass).

## Invalid / already-existing data (integration points)

| Condition | Thrown by | Propagated as |
|-----------|-----------|---------------|
| Invalid role / personal fields / password / ID format | `GestoreUtenti` `IllegalArgumentException` | Swing: catch `RuntimeException` → error dialog; REST: `GestoreEccezioni` → HTTP 400 `{"errore": ...}` |
| Duplicate email or identifier | `GestoreUtenti` `IllegalArgumentException` | Same |
| Persist failure | `GestoreUtenti` `RuntimeException` | Swing dialog; REST unhandled by `GestoreEccezioni` for generic `RuntimeException` (only `IllegalArgument`/`IllegalState`/`Security`) |

Main integration seams for tests: Boundary↔Facade, Facade↔GestoreUtenti, GestoreUtenti↔factories, GestoreUtenti↔RegistroUtenti (lookup + save), RegistroUtenti↔GestorePersistenza, REST exception mapping via GestoreEccezioni.

## Diagram choice

Component/collaboration view (PlantUML) scoped to registration only; layers Boundary → Facade → Gestore → Factory/Entity/Registry → Persistence.
