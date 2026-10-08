# Notes — IS-seat-L3 architecture view (seat booking)

**Run-id:** IS-seat-L3  
**Subject:** `experiments/skill-baseline/subjects/Progetto-IS`  
**Goal (verbatim):** software developer modifying seat booking rules; need high-level architecture of booking request handling, availability checks, booking rules, reservation storage, and notification service interactions.

## Evidence sources (JavaProject only)

| Concern | Primary types | Evidence |
|--------|----------------|----------|
| Handle booking requests | `BoundaryPrenotazione`, Swing wizard (`Seleziona*`, `RiepilogoPrenotazione`), `BibliotecaFacade` | REST `POST /api/prenotazioni/effettua`; facade delegates UC7 to `GestorePrenotazioni` |
| Pre-booking availability browse | `BoundarySalaStudio`, `GestoreSale` | UC6: `consultazioneSaleDisponibili`, `getFasceDisponibili`, `selezionaDettaglioSala` |
| Apply booking rules (UC7) | `GestorePrenotazioni.effettuaPrenotazione` | Validates student/sala/area/fascia; uniqueness V18; availability under `synchronized`; seat selection; create ATTIVA; notify after save |
| Seat availability | `Area.getPostazioniDisponibili`, `Postazione.disponibilita` | Availability derived from ATTIVA/CONFERMATA prenotazioni via `RegistroPrenotazioni` |
| Uniqueness rule V18 | `Studente.verificaPrenotazioneAttivaOConfermataInDataFascia` | Same student cannot hold ATTIVA/CONFERMATA for same date+fascia |
| Auto seat assignment | `StrategiaAssegnazione` / `AssegnazionePrimaLibera` | Strategy used when `idPostazione == 0` |
| Store reservations | `RegistroPrenotazioni` → `GestorePersistenza` (JPA) | `salvaPrenotazione` / `aggiorna` / queries |
| Domain reservation + state rules | `Prenotazione` + state classes | State pattern; V07 cancel window; V08 check-in tolerance; Observer on `setStato` |
| Notifications | `GestoreNotifiche` (Observer), `ServizioNotifiche`, `AdapterServizioNotifiche`, `GatewayEmailEsterno` | Wired by `ConfigurazioneNotifiche`; stub gateway prints to console |
| Time-driven rules | `SchedulerNotifiche` | Every 60s: UC16 termine + UC14 promemoria via facade |

## Booking-rule touchpoints (for modification impact)

Changing **new booking rules** most directly affects:

1. **`GestorePrenotazioni.effettuaPrenotazione`** — orchestration and validation sequence  
2. **Entity helpers** used as rules: `SalaStudio` (active, opening days), `Studente` (V18), `Postazione`/`Area` (availability), `Prenotazione` (state/time constraints for cancel/check-in/expiry)  
3. **`StrategiaAssegnazione`** — if rules change how a free seat is chosen  
4. **Downstream:** `RegistroPrenotazioni` / persistence schema; `GestoreNotifiche` if new states/messages; `GestoreSale` if availability presentation must match new rules  

## Layering observed

BCED-style: Boundary → `BibliotecaFacade` → Gestori (controller) → Entity/Registro → `GestorePersistenza`. Notification adapter lives in boundary and is injected into `GestoreNotifiche` so controller depends only on `ServizioNotifiche`.

## Diagram choices

- One component/container-level view focused on the **booking process**, not the full product (omitted: full utente registration UI, sala CRUD except where GestoreSale feeds availability).  
- Elements named after concrete types found in source.  
- Dependencies oriented as call/use edges supporting UC7 and related notification path.
