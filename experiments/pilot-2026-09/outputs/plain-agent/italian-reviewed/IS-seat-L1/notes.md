# Notes — IS-seat-L1 (seat booking architecture)

**Run id:** IS-seat-L1  
**Subject:** `experiments/skill-baseline/subjects/Progetto-IS`  
**Goal (verbatim):** I am a software developer. I need to modify the seat booking functionality and understand the main system components involved and how they interact.

## Scope of evidence

Evidence taken only from `JavaProject/src/main/java` (and README for product context). Focus: UC7 *EffettuaPrenotazione* (book a seat/postazione) and the supporting consult/availability path used by the booking wizard (UC6 / sala detail). Related lifecycle ops that touch the same seat booking aggregate (annulla, check-in) appear only where they share the same controllers/registries.

## Layered structure (observed)

| Layer | Packages / types |
|-------|------------------|
| Boundary (UI/API) | `boundary.SpringBoot.BoundaryPrenotazione`, `BoundarySalaStudio`; Swing wizard `SelezionaDataAndSala` → `SelezionaFascia` → `SelezionaArea` → `SelezionaPostazione` → `RiepilogoPrenotazione` |
| Controller facade | `BibliotecaFacade` — sole entry for boundaries; DTO-only API |
| Application controllers | `GestorePrenotazioni` (UC7 create + assignment), `GestoreSale` (availability / detail), `GestoreNotifiche` (Observer on booking state) |
| Strategy | `StrategiaAssegnazione` / `AssegnazionePrimaLibera` (auto seat when `idPostazione == 0`) |
| Domain entities | `Prenotazione`, `Postazione`, `Area`, `SalaStudio`, `FasciaOraria`, `Studente` |
| Entity registries | `RegistroPrenotazioni`, `RegistroSale`, `RegistroUtenti` |
| Persistence | `GestorePersistenza` (+ `JpaUtil`) |

## Booking interaction chain (evidence)

1. **REST:** `POST /api/prenotazioni/effettua` → `BoundaryPrenotazione` → `BibliotecaFacade.effettuaPrenotazione(RichiestaPrenotazioneDTO)` → `GestorePrenotazioni.effettuaPrenotazione`.
2. **Swing:** wizard ends in `RiepilogoPrenotazione` calling the same facade method; prior steps call `consultaSaleDisponibili`, `getFasceDisponibili`, `selezionaDettaglioSala` via `GestoreSale`.
3. **UC7 inside `GestorePrenotazioni` (synchronized):** resolve student / sala / area / fascia via registries; uniqueness V18 on student; `Area.getPostazioniDisponibili`; select seat (`idPostazione > 0` explicit or Strategy); create `Prenotazione` in `StatoAttiva`; `RegistroPrenotazioni.salvaPrenotazione`; attach/notify `GestoreNotifiche`.
4. **Availability of a seat (`Postazione.disponibilita`):** derived — free iff no ATTIVA/CONFERMATA booking on that postazione+data+fascia (`RegistroPrenotazioni.cercaPrenotazioniPerPostazione` / `occupaSlot`).
5. **Persistence:** registries call `GestorePersistenza` (JPA EntityManager transactions).

## Elements intentionally emphasized for the developer goal

- Seat = `Postazione` (belongs to `Area` of `SalaStudio`); no independent seat state — occupancy from `Prenotazione`.
- Entry points for booking UX (REST + Swing wizard) and the shared facade.
- Controllers a developer must change for booking rules vs. room listing vs. notifications.
- Auto vs. manual seat selection path.

## Out of primary diagram scope

Authentication (`GestoreUtenti`), room create/delete, librarian monitoring, email adapter internals — not required to understand core seat booking interactions; mentioned only if on the critical path (notifications after save).
