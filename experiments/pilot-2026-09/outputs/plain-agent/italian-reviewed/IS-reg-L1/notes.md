# Notes — IS-reg-L1 (User Registration Architecture View)

**Run ID:** IS-reg-L1  
**Subject:** `experiments/skill-baseline/subjects/Progetto-IS`  
**Stakeholder goal (verbatim):** "I am an integration tester. I need to test the user registration functionality and understand which system components are involved and how they interact."  
**UC:** UC1 — Registrazione (evidenced in `GestoreUtenti`, `BibliotecaFacade`, `BoundaryAutenticazione`)

## Evidence sources (repository only)

| Area | Path |
|------|------|
| REST boundary | `JavaProject/src/main/java/.../boundary/SpringBoot/BoundaryAutenticazione.java` |
| Exception mapping (REST) | `.../boundary/SpringBoot/GestoreEccezioni.java` |
| Swing boundary | `.../boundary/Swing/Registrazione.java` |
| Facade | `.../controller/BibliotecaFacade.java` |
| Business logic | `.../controller/GestoreUtenti.java` |
| Factories | `.../controller/factory/{UtenteFactory,StudenteFactory,BibliotecarioFactory}.java` |
| Domain entities | `.../entity/{Utente,Studente,Bibliotecario,RegistroUtenti}.java` |
| Persistence | `.../database/{GestorePersistenza,JpaUtil}.java`, `META-INF/persistence.xml` |
| Transfer object | `.../dto/UtenteDTO.java` |
| Integration-style tests | `.../test/.../controller/RegistrazioneTest.java` |

## Call chain (evidence)

1. **Entry points (two UI/API surfaces, same facade):**
   - Swing: `Registrazione.registra()` → `BibliotecaFacade.getInstance().registrazione(...)`
   - REST: `POST /api/auth/registrazione` in `BoundaryAutenticazione` → same facade method
2. **Facade:** `BibliotecaFacade.registrazione` delegates to `GestoreUtenti.getInstance().registrazione`
3. **GestoreUtenti.registrazione (UC1):**
   - Validates role (`Studente` \| `Bibliotecario`), name/cognome, password (8–32), email (`*unina.it`), identifier format
   - Uniqueness via `RegistroUtenti.esisteEmailIstituzionale` / `cercaStudentePerMatricola` / `cercaBibliotecarioPerCodice`
   - Creates entity via `StudenteFactory` or `BibliotecarioFactory` (`UtenteFactory`)
   - Persists via `RegistroUtenti.registraUtente` → `GestorePersistenza.salva` → JPA `EntityManager.persist` (MySQL `prenotazionidb`)
   - Returns `UtenteDTO` (no entity crosses the boundary)
4. **REST errors:** `IllegalArgumentException` / `IllegalStateException` → HTTP 400 via `GestoreEccezioni`; Swing shows `RuntimeException` message in dialog
5. **Tests:** `RegistrazioneTest` drives `BibliotecaFacade.registrazione` against JPA/DB (student & librarian success; validation & duplicate failures)

## Scope decisions for the view

- Included only components on the UC1 registration path (integration-test relevant).
- Omitted unrelated gestori (sale, prenotazioni, notifiche) and auth-only paths beyond shared facade/gestore.
- Showed both Swing and REST as alternative boundaries sharing one controller stack.
- Persistence shown as GestorePersistenza → JpaUtil/Hibernate → MySQL (from `persistence.xml`).

## Diagram choice

Component-interaction diagram (Mermaid) for L1 integration view: boundaries → facade → gestore → factories/entities → registro → persistence → DB, plus `UtenteDTO` return and test harness entry.
