# Italian-to-English UML Identifier Mapping

This mapping traces view-only English comprehension-model symbols back to the original Italian/Java names. UML IDs are unchanged.

| Italian / Java symbol | English model symbol | Kind | Occurrences |
|---|---|---|---:|
| `acquisisciCriteriFiltro` | `collectFilterCriteria` | Operation | 1 |
| `acquisisciDatiAccesso` | `collectAccessData` | Operation | 1 |
| `acquisisciDatiRegistrazione` | `collectRegistrationData` | Operation | 1 |
| `acquisisciDatiSegnalazione` | `collectReportData` | Operation | 1 |
| `acquisisciInfoAggiuntive` | `collectAdditionalInformation` | Operation | 1 |
| `acquisisciNuovoStato` | `collectNewStatus` | Operation | 1 |
| `acquisisciParametriMonitoraggio` | `collectMonitoringParameters` | Operation | 1 |
| `acquisisciTestoNota` | `collectNoteText` | Operation | 1 |
| `aggiorna` | `update` | Operation | 1 |
| `aggiornaElencoSegnalazioniConFiltri` | `updateFilteredReportList` | Operation | 1 |
| `aggiornamentiStatoRegistrati` | `recordedStatusUpdates` | AssociationEnd | 1 |
| `Aggiornamento a stato` | `Status updated to` | embedded label | 0 |
| `AggiornamentoStato` | `StatusUpdate` | ActivityPartition, CandidateItem, Class | 5 |
| `AggiornamentoStato2` | `StatusUpdate2` | Class | 1 |
| `aggiornaStato` | `updateStatus` | Operation | 7 |
| `aggiornaStatoSegnalazione` | `updateReportStatus` | Operation | 2 |
| `aggiungiNotaInterna` | `addInternalNote` | Operation | 4 |
| `allegaImmagine` | `attachImage` | Operation | 1 |
| `allegatoImmagine` | `imageAttachment` | Attribute | 3 |
| `appartiene` | `belongs to` | embedded label | 0 |
| `applicaNuovoStato` | `applyNewStatus` | Operation | 1 |
| `ArchivioSegnalazioni` | `ReportArchive` | ActivityPartition | 1 |
| `areaComunale` | `municipalArea` | Attribute, Parameter | 3 |
| `ArredoUrbanoDanneggiato` | `DamagedStreetFurniture` | Class | 1 |
| `arredoUrbanoDanneggiato` | `damagedStreetFurniture` | Attribute | 1 |
| `attributo` | `attribute` | Parameter | 1 |
| `campiricerca` | `searchFields` | Parameter | 1 |
| `cap` | `postalCode` | Attribute | 2 |
| `Caricamento Allegato` | `Attachment Upload` | CandidateItem, Requirement | 2 |
| `CatalogoSegnalazioni` | `ReportCatalog` | ActivityPartition, Class | 2 |
| `categoria` | `category` | Attribute | 1 |
| `CategoriaSegnalazione` | `ReportCategory` | CandidateItem, Class | 3 |
| `CategoriaSegnalazione2` | `ReportCategory2` | Class | 1 |
| `CentroNotifiche` | `NotificationCenter` | ActivityPartition, Class | 3 |
| `CentroSegnalazioni` | `ReportCenter` | ActivityPartition, Class | 2 |
| `cercaPerAttributo` | `findByAttribute` | Operation | 1 |
| `cercaPerCampi` | `findByFields` | Operation | 1 |
| `chiudi` | `close` | Operation | 1 |
| `Cittadino` | `Citizen` | Class | 2 |
| `cittadino` | `citizen` | InteractionLifeLine | 2 |
| `città` | `city` | Attribute | 2 |
| `classe` | `classType` | Parameter | 3 |
| `cognome` | `lastName` | Attribute | 3 |
| `comunica` | `communicates` | embedded label | 0 |
| `comunicaAccessoRiuscito` | `displayAccessSuccess` | Operation | 1 |
| `comunicaConfermaAggiornamento` | `displayUpdateConfirmation` | Operation | 1 |
| `comunicaConfermaCreazione` | `displayCreationConfirmation` | Operation | 1 |
| `comunicaConfermaInserimento` | `displayEntryConfirmation` | Operation | 1 |
| `comunicaConfermaRegistrazione` | `displayRegistrationConfirmation` | Operation | 1 |
| `comunicaDettaglioSegnalazione` | `displayReportDetails` | Operation | 1 |
| `comunicaElencoSegnalazioni` | `displayReportList` | Operation | 1 |
| `comunicaRisultatiMonitoraggio` | `displayMonitoringResults` | Operation | 1 |
| `consultaSegnalazioniInviate` | `viewSubmittedReports` | Operation | 2 |
| `consultaSegnalazioniRicevute` | `viewReceivedReports` | Operation | 2 |
| `ControllerAccessoUtente` | `UserAccessController` | Class | 1 |
| `ControllerAggiornamentoStatoSegnalazione` | `ReportStatusUpdateController` | Class | 1 |
| `ControllerConsultazioneSegnalazioni` | `ReportConsultationController` | Class | 1 |
| `ControllerCreazioneSegnalazione` | `ReportCreationController` | Class | 1 |
| `ControllerDettaglioSegnalazione` | `ReportDetailsController` | Class | 1 |
| `ControllerMonitoraggioAttività` | `ActivityMonitoringController` | Class | 1 |
| `ControllerNotaInterna` | `InternalNoteController` | Class | 1 |
| `ControllerNotifiche` | `NotificationController` | Class | 1 |
| `ControllerRegistrazioneUtente` | `UserRegistrationController` | Class | 1 |
| `ControllerServiziSistema` | `SystemServicesController` | Class | 1 |
| `creaAggiornamentoStato` | `createStatusUpdate` | Operation | 1 |
| `creaSegnalazione` | `createReport` | Operation | 2 |
| `Creator NotaInterna` | `InternalNote Creator` | Stereotype | 1 |
| `creaUtente` | `createUser` | Operation | 1 |
| `Credenziali` | `Credentials` | CandidateItem, Class | 3 |
| `credenziali` | `credentials` | embedded label | 0 |
| `criteriFiltro` | `filterCriteria` | Parameter | 4 |
| `criteriMonitoraggio` | `monitoringCriteria` | Parameter | 2 |
| `dataAggiornamento` | `updateDate` | Attribute | 4 |
| `dataFine` | `endDate` | Parameter | 1 |
| `dataInizio` | `startDate` | Parameter | 1 |
| `dataInserimento` | `insertionDate` | Attribute | 2 |
| `dataInvio` | `sentDate` | Attribute | 3 |
| `dataSegnalazione` | `reportDate` | Attribute, Parameter | 5 |
| `datiAccesso` | `accessData` | Parameter | 3 |
| `datiRegistrazione` | `registrationData` | Parameter | 7 |
| `datiSegnalazione` | `reportData` | Parameter | 6 |
| `datoSegnalazione` | `reportDataItem` | Parameter | 1 |
| `descrizione` | `description` | Attribute | 4 |
| `dettaglio` | `details` | Parameter | 1 |
| `effettuaRegistrazione` | `register` | Operation | 1 |
| `elaboraDatiSegnalazioniPerIntervallo` | `processReportsByTimeRange` | Operation | 1 |
| `elaboraDatiSegnalazioniPerZona` | `processReportsByArea` | Operation | 1 |
| `elenco` | `list` | Parameter | 1 |
| `genera` | `generates` | embedded label | 0 |
| `generaDatiMonitoraggio` | `generateMonitoringData` | Operation | 1 |
| `generaNotificaCambioStato` | `generateStatusChangeNotification` | Operation | 1 |
| `generaRisultatiMonitoraggio` | `generateMonitoringResults` | Operation | 1 |
| `generaVistaRiepilogativaZona` | `generateAreaSummary` | Operation | 1 |
| `gestisce` | `manages` | embedded label | 0 |
| `getCategoria` | `getCategory` | Operation | 1 |
| `getCognome` | `getLastName` | Operation | 1 |
| `getDescrizione` | `getDescription` | Operation | 1 |
| `getIdNotifica` | `getNotificationId` | Operation | 1 |
| `getIdSegnalazione` | `getReportId` | Operation | 1 |
| `getIdUtente` | `getUserId` | Operation | 1 |
| `getMessaggio` | `getMessage` | Operation | 1 |
| `getNome` | `getFirstName` | Operation | 1 |
| `getNuovoStato` | `getNewStatus` | Operation | 1 |
| `getStatoCorrente` | `getCurrentStatus` | Operation | 1 |
| `getTitolo` | `getTitle` | Operation | 1 |
| `GUIAccessoUtente` | `UserAccessGUI` | Class | 1 |
| `GUIAggiornamentoStatoSegnalazione` | `ReportStatusUpdateGUI` | Class | 1 |
| `GUIConsultazioneSegnalazione` | `ReportConsultationGUI` | Class | 1 |
| `GUIConsultazioneSegnalazioniInviate` | `SubmittedReportsGUI` | Class | 1 |
| `GUIConsultazioneSegnalazioniRicevute` | `ReceivedReportsGUI` | Class | 1 |
| `GUICreazioneSegnalazione` | `ReportCreationGUI` | Class | 1 |
| `GUIDashboardUtente` | `UserDashboardGUI` | Class | 1 |
| `GUIHomePage` | `HomePageGUI` | Class | 1 |
| `GUIMonitoraggioAttività` | `ActivityMonitoringGUI` | Class | 1 |
| `GUINotaInterna` | `InternalNoteGUI` | Class | 1 |
| `GUIRegistrazioneUtente` | `UserRegistrationGUI` | Class | 1 |
| `haStatoCorrente` | `hasCurrentStatus` | embedded label | 0 |
| `idNotifica` | `notificationId` | Attribute | 1 |
| `idSegnalazione` | `reportId` | Attribute, Message, Parameter | 27 |
| `idUtente` | `userId` | Attribute, Message, Parameter | 30 |
| `IlluminazioneGuasta` | `FaultyStreetLighting` | Class | 1 |
| `illuminazioneGuasta` | `faultyStreetLighting` | Attribute | 1 |
| `immagineAllegata` | `attachedImage` | Attribute, Parameter | 2 |
| `impostaDataSegnalazione` | `setReportDate` | Operation | 1 |
| `InLavorazione` | `InProgress` | Class | 2 |
| `inserisce` | `adds` | embedded label | 0 |
| `inserisceDatiSegnalazione` | `enterReportData` | Operation | 1 |
| `inserisciInformazioniAggiuntive` | `addAdditionalInformation` | Operation | 1 |
| `invia` | `sends` | embedded label | 0 |
| `inviaCriteriFiltro` | `sendFilterCriteria` | Operation | 1 |
| `inviaDatiAccesso` | `sendAccessData` | Operation | 1 |
| `inviaDatiRegistrazione` | `sendRegistrationData` | Operation | 1 |
| `inviaDatiSegnalazione` | `sendReportData` | Operation | 1 |
| `inviaNotaInterna` | `sendInternalNote` | Operation | 1 |
| `inviaNotificaAlCittadino` | `sendNotificationToCitizen` | Operation | 2 |
| `inviaRichiestaAggiornamento` | `sendUpdateRequest` | Operation | 1 |
| `inviaRichiestaConsultazione` | `sendConsultationRequest` | Operation | 1 |
| `inviaRichiestaMonitoraggio` | `sendMonitoringRequest` | Operation | 1 |
| `Inviata` | `Submitted` | Class | 2 |
| `isStatoNotificabile` | `isNotifiableStatus` | Operation | 1 |
| `isStatoSegnalazione` | `isReportStatus` | Operation | 4 |
| `istantiate` | `instantiate` | Stereotype | 2 |
| `messaggio` | `message` | Attribute | 3 |
| `messaggioErrore` | `errorMessage` | Parameter | 8 |
| `monitoraAndamentoAttivita` | `monitorActivityProgress` | Operation | 2 |
| `nome` | `firstName` | Attribute | 3 |
| `nota` | `note` | embedded label | 0 |
| `NotaInterna` | `InternalNote` | CandidateItem, Class | 3 |
| `Notifica` | `Notification` | Class | 2 |
| `notifica` | `notification` | InteractionLifeLine | 2 |
| `Notifica2` | `Notification2` | Class | 1 |
| `numeroCivico` | `streetNumber` | Attribute | 2 |
| `nuovo stato` | `new status` | embedded label | 0 |
| `Nuovo Stato` | `New Status` | embedded label | 0 |
| `nuovoStato` | `newStatus` | AssociationEnd, Attribute, Parameter | 9 |
| `oggetto` | `object` | Parameter | 2 |
| `operatore` | `operator` | embedded label | 0 |
| `Operatore Comunale` | `Municipal Operator` | embedded label | 0 |
| `OperatoreComunale` | `MunicipalOperator` | Class, Message | 4 |
| `parametriMonitoraggio` | `monitoringParameters` | Parameter | 1 |
| `PericoloGenerico` | `GenericHazard` | Class | 1 |
| `pericoloGenerico` | `genericHazard` | Attribute | 1 |
| `Posizione` | `Location` | Class | 2 |
| `posizione` | `location` | InteractionLifeLine | 1 |
| `possiede` | `owns` | embedded label | 0 |
| `Presa In Carico` | `Accepted` | State2 | 1 |
| `Presa in Carico` | `Accepted` | embedded label | 0 |
| `presa in carico` | `accepted` | embedded label | 0 |
| `PresaInCarico` | `Accepted` | Class | 2 |
| `presaInCarico` | `accepted` | embedded label | 0 |
| `presaincarico` | `accepted` | embedded label | 0 |
| `raccoglie` | `collects` | embedded label | 0 |
| `recapito telefonico` | `phone number` | embedded label | 0 |
| `recapitoTelefonico` | `phoneNumber` | Attribute | 3 |
| `recuperaCittadinoSegnalante` | `retrieveReportingCitizen` | Operation | 1 |
| `recuperaDatUtenteDaCredenziali` | `retrieveUserDataFromCredentials` | Operation | 1 |
| `recuperaDettaglioSegnalazione` | `retrieveReportDetails` | Operation | 2 |
| `recuperaDettagliSegnalazione` | `retrieveReportDetails` | Operation | 1 |
| `recuperaEvoluzioneSegnalazione` | `retrieveReportHistory` | Operation | 3 |
| `recuperaSegnalazioniDelCittadino` | `retrieveCitizenReports` | Operation | 1 |
| `recuperaSegnalazioniInLavorazione` | `retrieveReportsInProgress` | Operation | 2 |
| `recuperaSegnalazioniInviate` | `retrieveSubmittedReports` | Operation | 2 |
| `recuperaSegnalazioniPerZona` | `retrieveReportsByArea` | Operation | 1 |
| `recuperaSegnalazioniRicevute` | `retrieveReceivedReports` | Operation | 3 |
| `registra` | `records` | embedded label | 0 |
| `registraAggiornamentoStato` | `recordStatusUpdate` | Operation | 2 |
| `registraNotaInterna` | `recordInternalNote` | Operation | 1 |
| `registraNuovaSegnalazione` | `recordNewReport` | Operation | 1 |
| `registraUtente` | `recordUser` | Operation | 2 |
| `RegistroUtenti` | `UserRegistry` | Class | 1 |
| `restituisceRisultatiMonitoraggio` | `returnMonitoringResults` | Operation | 1 |
| `riceve` | `receives` | embedded label | 0 |
| `richiediAccesso` | `requestAccess` | Operation | 1 |
| `richiediAggiornamentoStato` | `requestStatusUpdate` | Operation | 1 |
| `richiediAggiuntaNotaSegnalazione` | `requestReportNote` | Operation | 1 |
| `richiediConsultazioneSegnalazionInviate` | `requestSubmittedReports` | Operation | 1 |
| `richiediConsultazioneSegnalazioniRicevute` | `requestReceivedReports` | Operation | 1 |
| `richiediCreazioneSegnalazione` | `requestReportCreation` | Operation | 2 |
| `richiediDettaglioSegnalazione` | `requestReportDetails` | Operation | 1 |
| `richiediInserimentoNota` | `requestNoteEntry` | Operation | 1 |
| `richiediInvioNotifica` | `requestNotification` | Operation | 1 |
| `richiediMonitoraggioAttività` | `requestActivityMonitoring` | Operation | 1 |
| `richiediRegistrazione` | `requestRegistration` | Operation | 2 |
| `richiediRegistrazioneNotaInterna` | `requestInternalNoteRecording` | Operation | 1 |
| `richiediRegistrazioneUtente` | `requestUserRegistration` | Operation | 1 |
| `RifiutiAbbandonati` | `AbandonedWaste` | Class | 1 |
| `rifiutiAbbandonati` | `abandonedWaste` | Attribute | 1 |
| `Risolta` | `Resolved` | Class | 2 |
| `risolta` | `resolved` | embedded label | 0 |
| `risultatiMonitoraggio` | `monitoringResults` | Parameter | 2 |
| `Ruolo` | `Role` | embedded label | 0 |
| `salva` | `save` | Operation | 1 |
| `segnalaErroreAccesso` | `displayAccessError` | Operation | 1 |
| `segnalaErroreAggiornamento` | `displayUpdateError` | Operation | 1 |
| `segnalaErroreConsultazione` | `displayConsultationError` | Operation | 1 |
| `segnalaErroreCreazioneSegnalazione` | `displayReportCreationError` | Operation | 1 |
| `segnalaErroreDashboard` | `displayDashboardError` | Operation | 1 |
| `segnalaErroreMonitoraggio` | `displayMonitoringError` | Operation | 1 |
| `segnalaErroreNota` | `displayNoteError` | Operation | 1 |
| `segnalaErroreRegistrazione` | `displayRegistrationError` | Operation | 1 |
| `Segnalazione` | `Report` | Class | 3 |
| `segnalazione` | `report` | InteractionLifeLine, Parameter | 13 |
| `Segnalazione2` | `Report2` | Class | 1 |
| `selezionaFunzionalita` | `selectFeature` | Operation | 1 |
| `selezionaIntervalloTemporale` | `selectTimeRange` | Operation | 1 |
| `selezionaNuovoStato` | `selectNewStatus` | Operation | 1 |
| `selezionaSegnalazione` | `selectReport` | Operation | 1 |
| `ServizioPersistenza` | `PersistenceService` | Class | 1 |
| `servizioPersistenza` | `persistenceService` | AssociationEnd, Attribute, InteractionLifeLine | 12 |
| `ServizioSegnalazioni` | `ReportService` | Class | 1 |
| `ServizioUtenti` | `UserService` | Class | 1 |
| `setDataSegnalazione` | `setReportDate` | Operation | 1 |
| `setImmagine` | `setImage` | Operation | 1 |
| `Sistema Comunale Gestione Segnalazioni` | `Municipal Report Management System` | Component | 1 |
| `Sistema Gestione Segnalazioni in Aree Comunali` | `Report Management System for Municipal Areas` | InteractionLifeLine | 9 |
| `State Dependend` | `State Dependent` | Stereotype | 1 |
| `statoCorrente` | `currentStatus` | AssociationEnd, Attribute | 4 |
| `StatoSegnalazione` | `ReportStatus` | CandidateItem, Class | 4 |
| `StatoSegnalazione2` | `ReportStatus2` | Class | 1 |
| `StoricoStatiSegnalazione` | `ReportStatusHistory` | ActivityPartition, Class | 2 |
| `strada` | `street` | Attribute | 2 |
| `StradaDissestata` | `DamagedRoad` | Class | 1 |
| `stradaDissestata` | `damagedRoad` | Attribute | 1 |
| `testo` | `text` | Attribute | 2 |
| `testoNota` | `noteText` | Parameter | 7 |
| `titolo` | `title` | Attribute | 4 |
| `trovaPerId` | `findById` | Operation | 1 |
| `UfficioSegnalazioni` | `ReportOffice` | ActivityPartition, Class | 2 |
| `Utente` | `User` | Class | 2 |
| `utente` | `user` | InteractionLifeLine | 1 |
| `Utente2` | `User2` | Class | 1 |
| `utentiRegistrati` | `registeredUsers` | AssociationEnd | 1 |
| `validaCampiRegistrazione` | `validateRegistrationFields` | Operation | 1 |
| `validaCampiSegnalazione` | `validateReportFields` | Operation | 1 |
| `validaTestoNota` | `validateNoteText` | Operation | 1 |
| `valore` | `value` | Parameter | 1 |
| `verificaAccessoAllaSegnalazione` | `verifyReportAccess` | Operation | 1 |
| `verificaAccessoDettaglio` | `verifyDetailsAccess` | Operation | 1 |
| `verificaCredenzialiAccesso` | `verifyAccessCredentials` | Operation | 1 |
| `verificaDatiInseriti` | `validateEnteredData` | Operation | 1 |
| `verificaDatiObbligatori` | `validateRequiredData` | Operation | 2 |
| `verificaDatiRegistrazione` | `validateRegistrationData` | Operation | 1 |
| `verificaPassaggioDiStatoConsentito` | `isStatusTransitionAllowed` | Operation | 1 |
| `verificaStatoNotificabile` | `isNotifiableStatus` | Operation | 3 |
| `verificaUtenteCittadino` | `isCitizenUser` | Operation | 1 |
| `verificaUtenteOperatore` | `isOperatorUser` | Operation | 1 |
| `verificaUtenteRegistrato` | `isRegisteredUser` | Operation | 1 |
| `visualizzaDettagliSegnalazione` | `displayReportDetails` | Operation | 1 |
| `CriteriFiltroDTO` | `FilterCriteriaDTO` | embedded signature/prose | 0 |
| `CriteriMonitoraggioDTO` | `MonitoringCriteriaDTO` | embedded signature/prose | 0 |
| `DatiRegistrazioneDTO` | `RegistrationDataDTO` | embedded signature/prose | 4 |
| `DatiSegnalazioneDTO` | `ReportDataDTO` | embedded signature/prose | 4 |
| `DettaglioSegnalazioneCittadinoDTO` | `CitizenReportDetailsDTO` | embedded signature/prose | 4 |
| `DettaglioSegnalazioneDTO` | `ReportDetailsDTO` | embedded signature/prose | 4 |
| `DettaglioSegnalazioneOperatoreDTO` | `OperatorReportDetailsDTO` | embedded signature/prose | 2 |
| `RisultatiMonitoraggioDTO` | `MonitoringResultsDTO` | embedded signature/prose | 4 |
| `controllerMonitoraggioAttività` | `activityMonitoringController` | embedded signature/prose | 4 |
| `gUIMonitoraggioAttività` | `activityMonitoringGUI` | embedded signature/prose | 4 |
| `immagineAllegataQ` | `attachedImage` | embedded signature/prose | 1 |
| `nomeUtente` | `username` | embedded signature/prose | 3 |
