# GR10-Q3 — Persistence architecture notes

**Run-id:** GR10-Q3  
**Stakeholder goal:** Database engineer understanding entities, relationships, and what must persist across a municipal report lifecycle.  
**Subject:** `experiments/skill-baseline/subjects/progetto_ing_software_gr10`  
**Evidence only from repository sources below (no skill paths used).**

## Persistence stack

- JPA unit `Sistema_Gestione_Segnalazioni_Comunali` in `src/main/resources/META-INF/persistence.xml`
- Registered classes: `Utente`, `Cittadino`, `OperatoreComunale`, `Segnalazione`, `NotaInterna`, `AggiornamentoStato`, `Notifica`
- MySQL DB `segnalazioni_db`; `hibernate.hbm2ddl.auto=update`
- Access facade: `Database.ServizioPersistenza` (`salva`, `aggiorna`, `cercaPerAttributo`, `cercaPerCampi`, `trovaPerId`) via `JpaUtil`

## Persisted entities and tables

| Concept | Java type | Table / storage | Notes |
|--------|-----------|-----------------|-------|
| User (base) | `Utente` | `utenti` | SINGLE_TABLE inheritance; discriminator column `ruolo` |
| Citizen | `Cittadino` | same `utenti` | `@DiscriminatorValue("CITTADINO")` |
| Municipal operator | `OperatoreComunale` | same `utenti` | `@DiscriminatorValue("OPERATORE_COMUNALE")` |
| Credentials | `Credenziali` `@Embeddable` | columns on `utenti` (`email` unique, `password`) | No autonomous lifecycle |
| Report | `Segnalazione` | `segnalazioni` | Core aggregate |
| Location | `Posizione` `@Embeddable` | columns on `segnalazioni` (`citta`, `cap`, `strada`, `numero_civico`, `area_comunale`) | Contained in report |
| Category | `CategoriaSegnalazione` enum | column `categoria` STRING | Values: illuminazione_guasta, strada_dissestata, rifiuti_abbandonati, pericolo_generico, arredo_urbano_danneggiato |
| Current state | `String nomeStatoCorrente` | column `stato_corrente` | Behavioral `StatoSegnalazione` is `@Transient` (not persisted) |
| State history | `AggiornamentoStato` | `aggiornamenti_stato` | Cascade ALL + orphanRemoval from `Segnalazione` |
| Internal note | `NotaInterna` | `note_interne` | Cascade ALL + orphanRemoval from `Segnalazione` |
| Notification | `Notifica` | `Notifiche` | Independent entity; saved explicitly |

## Relationships (from JPA mappings)

- `Segnalazione` **ManyToOne** `Cittadino` (`id_cittadino`, required) — author
- `Segnalazione` **ManyToOne** `OperatoreComunale` (`id_operatore`, optional) — assigned manager
- `Segnalazione` **OneToMany** `NotaInterna` (mappedBy `segnalazione`, cascade ALL, orphanRemoval)
- `Segnalazione` **OneToMany** `AggiornamentoStato` (mappedBy `segnalazione`, cascade ALL, orphanRemoval)
- `NotaInterna` **ManyToOne** `OperatoreComunale` (`id_operatore`, required)
- `AggiornamentoStato` **ManyToOne** `OperatoreComunale` (`id_operatore`, required)
- `Notifica` **ManyToOne** `Cittadino` (`id_cittadino`, required) — recipient
- `Notifica` **ManyToOne** `Segnalazione` (`id_segnalazione`, required)

## Report lifecycle — what must persist

State names (persisted strings on `segnalazioni.stato_corrente` and history `nuovo_stato`):

1. `inviata` (creation; `modificabile_dal_cittadino=true`) — `Inviata` is not notificabile
2. `presa_in_carico` (after operator assignment + first `aggiornaStato`) — notificabile
3. `in_lavorazione` — not notificabile
4. `risolta` (terminal) — notificabile

On each successful state advance, `Segnalazione` creates an `AggiornamentoStato` (date, `nuovo_stato`, report, operator) kept under the report.  
Notifications for `presa_in_carico` / `risolta` are created by `ServizioSegnalazioni` and `salva`d as `Notifica` (message, `stato_notificato`, recipient citizen, report).  
Internal notes (`testo`, `data_inserimento`, operator, report) persist with the report aggregate.

Report fields persisted at/after creation: `titolo`, `descrizione`, `categoria`, embedded location, `data_segnalazione`, optional `immagine_allegata`, `stato_corrente`, `modificabile_dal_cittadino`, citizen FK, later operator FK.

## Application parts that depend on this persisted data

Entity facades (only packages that call `ServizioPersistenza`):

- `Entity.ServizioUtenti` — register/find users, credentials lookup
- `Entity.ServizioSegnalazioni` — create/update reports, notes, state history, notifications, consultation/monitoring queries

Control layer (does **not** call `ServizioPersistenza` directly; uses facades):

- `ControllerAccessoUtente`, `ControllerRegistrazioneUtente` → `ServizioUtenti`
- `ControllerCreazioneSegnalazione`, `ControllerConsultazioneSegnalazioni`, `ControllerDettaglioSegnalazione`, `ControllerAggiornamentoStatoSegnalazione`, `ControllerNotaInterna`, `ControllerNotifiche`, `ControllerMonitoraggioAttivita` → `ServizioSegnalazioni` (often + `ServizioUtenti` for role checks)

Boundary GUIs depend on Controllers only (no direct persistence).

## Diagram scope

The view `architecture_view.puml` shows: persisted tables/entities, embeds/enums, associations, state-string lifecycle, and dependency from facades/controllers onto the persistence layer.
