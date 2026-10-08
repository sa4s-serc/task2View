# Notes — IS-seat-L2 (seat booking architecture)

**Run ID:** IS-seat-L2  
**Subject:** `experiments/skill-baseline/subjects/Progetto-IS`  
**Goal:** Understand main components of seat booking (prenotazione postazione), responsibilities, interactions, and likely impact of new booking rules.

## Evidence sources (repository only)

- `README.md` — library seat-booking domain (Java / Spring Boot / Hibernate)
- `controller/GestorePrenotazioni.java` — UC7 create booking; rules V18 uniqueness, seat selection, sync; also UC9/10/16
- `controller/BibliotecaFacade.java` — sole boundary→controller entry; DTO-only API
- `controller/GestoreSale.java` — UC6/UC7 wizard: available slots and area/seat detail via `Postazione.disponibilita`
- `controller/strategy/StrategiaAssegnazione.java`, `AssegnazionePrimaLibera.java` — automatic seat assignment
- `controller/GestoreNotifiche.java` — Observer on `Prenotazione` state changes
- `boundary/SpringBoot/BoundaryPrenotazione.java` — REST `/api/prenotazioni` (effettua, annulla, checkin)
- `boundary/SpringBoot/BoundarySalaStudio.java` — fasce/dettaglio for booking wizard
- `boundary/Swing/RiepilogoPrenotazione.java` — Swing confirms via `BibliotecaFacade.effettuaPrenotazione`
- `entity/Prenotazione.java` — State pattern; V07 cancel window; V08 check-in tolerance
- `entity/Postazione.java` — availability derived from ATTIVA/CONFERMATA bookings
- `entity/Area.java` — aggregates free seats for (data, fascia)
- `entity/Studente.java` — V18 uniqueness check
- `entity/RegistroPrenotazioni.java` — persistence facade; `occupaSlot`
- `dto/RichiestaPrenotazioneDTO.java` — UC7 request (`idPostazione=0` = auto-assign)

## Booking create flow (UC7) — interaction summary

1. Boundary (REST or Swing) → `BibliotecaFacade.effettuaPrenotazione(RichiestaPrenotazioneDTO)`
2. Facade → `GestorePrenotazioni.effettuaPrenotazione`
3. Resolve `Studente` (`RegistroUtenti`), `SalaStudio`/`Area`/`FasciaOraria` (`RegistroSale`); validate room active, weekday open, fascia not past
4. Under `synchronized`: V18 via `Studente.verificaPrenotazioneAttivaOConfermataInDataFascia`; free seats via `Area.getPostazioniDisponibili` → `Postazione.disponibilita` → `RegistroPrenotazioni`
5. Seat: explicit id or `StrategiaAssegnazione` (`AssegnazionePrimaLibera`)
6. Create `Prenotazione` in `StatoAttiva`; save via `RegistroPrenotazioni`; notify `GestoreNotifiche` (Observer)

## Likely impact of new booking rules

| Concern | Primary locations |
|--------|-------------------|
| Eligibility / uniqueness / validation before save | `GestorePrenotazioni` (esp. `effettuaPrenotazione`, `verificaUnicita`, `risolvi*`) |
| “Seat free?” definition | `Postazione.disponibilita`, `RegistroPrenotazioni.occupaSlot` |
| Auto-assignment policy | `StrategiaAssegnazione` / `AssegnazionePrimaLibera` |
| Temporal cancel/check-in rules | `Prenotazione` (V07/V08), state classes under `entity/state` |
| Availability shown in wizard | `GestoreSale.getFasceDisponibili`, `selezionaDettaglioSala` |
| Downstream of new bookings | `GestoreNotifiche`, monitoring/stats in `GestorePrenotazioni` / `GestoreSale` |

## Diagram scope

Component/collaboration view centered on UC7 seat booking and the collaborators that enforce or consume booking rules. Persistence (`GestorePersistenza`) shown as the store behind registers.
