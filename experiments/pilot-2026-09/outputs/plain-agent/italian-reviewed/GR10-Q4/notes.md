# GR10-Q4 — Notes for architecture view

**Run id:** GR10-Q4  
**Stakeholder goal (verbatim):** business analyst needs high-level understanding of municipal problem reporting/management: main user types, goals per type, and how functionalities relate.  
**Subject:** `experiments/skill-baseline/subjects/progetto_ing_software_gr10`  
**View type:** stakeholder-oriented use-case / capability overview (not code-layer BCED).

## Evidence used (repository only)

### System purpose
- README: system for managing reports (segnalazioni) of problems/disservices in municipal areas; two main user types — cittadini and operatori comunali.
- `GUIHomePage`: titled “Sistema Comunale Gestione Segnalazioni”; platform for territory-related reports.

### Main user types
- `Utente` (abstract) specialized as `Cittadino` (`CITTADINO`) and `OperatoreComunale` (`OPERATORE_COMUNALE`).
- Registration requires selecting a role (`ControllerRegistrazioneUtente` validates `ruolo`).
- After login, `GUIDashboardUtente` branches on role and shows different buttons.

### Goals / functionalities by role (dashboard + controllers)

**Shared (before role-specific work)**
- Registrazione Utente — README use cases; `ControllerRegistrazioneUtente` / `GUIRegistrazioneUtente`.
- Accesso Utente — `ControllerAccessoUtente` / `GUIAccessoUtente`; session carries id, name, role.

**Cittadino** (`configuraDashboardCittadino`)
- Create new report — “Crea nuova segnalazione” → `ControllerCreazioneSegnalazione` (citizen-only check).
- Consult own sent reports — “Consulta segnalazioni inviate” → `ControllerConsultazioneSegnalazioni.recuperaSegnalazioniInviate`.
- View report detail — `ControllerDettaglioSegnalazione` allows citizen only for their own report.
- While status is `inviata`, report remains editable by citizen (`Inviata`, Segnalazione comments; README: “Inserisci Informazioni Aggiuntive”).

**Operatore Comunale** (`configuraDashboardOperatore`)
- Consult received reports — “Consulta segnalazioni ricevute” → `recuperaSegnalazioniRicevute` (optional filters / ricerca by state etc.).
- Update report status — “Aggiorna stato segnalazione” → `ControllerAggiornamentoStatoSegnalazione`.
- Monitor activity — “Monitora andamento attività” → `ControllerMonitoraggioAttivita` (in lavorazione / riepilogo zona / generale).
- Add internal note — optional on received-report detail → `ControllerNotaInterna` (operator-only).
- View any receivable report detail — operator path in `ControllerDettaglioSegnalazione`.

### How functionalities relate
1. Registration + login establish role → dashboard capabilities.
2. Citizen creates a `Segnalazione` (title, description, category, position, optional image) in state **inviata**.
3. Operator consults received reports; may filter/search; opens detail; may add **nota interna**.
4. Operator advances status along fixed lifecycle: **inviata → presa_in_carico → in_lavorazione → risolta** (State pattern classes).
5. On notificabile states (`presa_in_carico`, `risolta`), status update coordinates **notifica** to the reporting citizen (`ControllerNotifiche`).
6. Monitoring aggregates operator view of activity over time/zone; depends on managed reports and their states.
7. Categories of problems (domain attribute): illuminazione_guasta, strada_dissestata, rifiuti_abbandonati, pericolo_generico, arredo_urbano_danneggiato.

## View design choices
- Emphasize actors, goals, and cross-links (report lifecycle + notification), not Swing/JPA/BCED packages.
- Include shared identity functions and the report-centered workflow that ties citizen and operator sides.
- Labels kept close to README Italian use-case names where they match implementation.
